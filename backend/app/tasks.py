import json
import os
import time
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .db import SessionLocal
from . import models
from .storage import StorageService
from .logging_config import get_logger
from .effects import apply_image_effect, apply_video_effect

logger = get_logger("app.tasks")

try:
    import requests  # type: ignore
except Exception:
    requests = None


# ---------------------------
# Helpers
# ---------------------------
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv"}


def _set_task_state(
    db: Session,
    task_id: int,
    status: str,
    progress: Optional[int] = None,
    output_path: Optional[str] = None,
    error_msg: Optional[str] = None,
):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        return None

    task.status = status
    if progress is not None:
        task.progress = int(progress)
    if output_path is not None:
        task.output_path = output_path
    if error_msg is not None:
        task.error_msg = error_msg

    db.commit()
    return task


def _callback_internal(cb: Dict[str, Any]) -> None:
    """
    Notify backend /internal/task_callback
    Env:
      - INTERNAL_TOKEN
      - BACKEND_BASE_URL (default http://127.0.0.1:8000)
    """
    if requests is None:
        return

    token = os.getenv("INTERNAL_TOKEN", "")
    if not token:
        return

    base = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    url = f"{base}/internal/task_callback"

    try:
        requests.post(url, json=cb, headers={"X-Internal-Token": token}, timeout=5)
    except Exception as e:
        logger.warning("Internal callback failed for task %s: %s", cb.get("task_id"), e)


def _guess_media_type(input_rel_path: str) -> str:
    ext = Path(input_rel_path).suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in VIDEO_EXTS:
        return "video"
    return "unknown"


# ---------------------------
# Real cartoon-style processing via OpenCV
# ---------------------------
def run_algorithm_image(
    storage: StorageService,
    input_rel_path: str,
    user_id: int,
    params: Dict[str, Any],
) -> str:
    style = params.get("style", "warm_cartoon")
    src_abs = str(storage.abs_path(input_rel_path))

    out_subdir = f"images/out/{user_id}"
    out_dir = (storage.base_dir / out_subdir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(input_rel_path).suffix or ".png"
    dst_name = f"{uuid4().hex}{ext}"
    dst_abs = str(out_dir / dst_name)

    apply_image_effect(src_abs, dst_abs, style=style)

    return (out_dir / dst_name).relative_to(storage.base_dir).as_posix()


def run_algorithm_video(
    storage: StorageService,
    input_rel_path: str,
    user_id: int,
    params: Dict[str, Any],
    progress_fn=None,
) -> str:
    style = params.get("style", "warm_cartoon")
    src_abs = str(storage.abs_path(input_rel_path))

    out_subdir = f"videos/out/{user_id}"
    out_dir = (storage.base_dir / out_subdir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    dst_name = f"{uuid4().hex}.mp4"
    dst_abs = str(out_dir / dst_name)

    apply_video_effect(src_abs, dst_abs, style=style, progress_cb=progress_fn)

    return (out_dir / dst_name).relative_to(storage.base_dir).as_posix()


# ---------------------------
# Worker entry
# ---------------------------
def process_payload(payload: Dict[str, Any]):
    """
    payload:
      - task_id
      - user_id
      - input_path (relative path under storage)
      - params (dict)
    """
    task_id = int(payload["task_id"])
    user_id = int(payload["user_id"])
    input_path = payload["input_path"]
    params = payload.get("params") or {}

    db: Session = SessionLocal()
    storage = StorageService()

    try:
        # queued -> processing
        _set_task_state(db, task_id=task_id, status=models.TaskStatus.processing.value, progress=5)
        _callback_internal({"task_id": task_id, "status": "processing", "progress": 5})

        media_type = _guess_media_type(input_path)
        if media_type == "unknown":
            raise ValueError(f"Unsupported file type: {Path(input_path).suffix}")

        # "pre-check"
        _set_task_state(db, task_id=task_id, status=models.TaskStatus.processing.value, progress=10)
        _callback_internal({"task_id": task_id, "status": "processing", "progress": 10})

        # ---- real AI processing via OpenCV ----
        _set_task_state(db, task_id=task_id, status=models.TaskStatus.processing.value, progress=20)
        _callback_internal({"task_id": task_id, "status": "processing", "progress": 20})

        if media_type == "video":
            def _video_progress(pct: int):
                real_pct = 20 + int(pct * 0.7)
                _set_task_state(db, task_id=task_id, status=models.TaskStatus.processing.value, progress=real_pct)
                _callback_internal({"task_id": task_id, "status": "processing", "progress": real_pct})

            output_path = run_algorithm_video(storage, input_path, user_id, params, progress_fn=_video_progress)
        else:
            output_path = run_algorithm_image(storage, input_path, user_id, params)

        _set_task_state(db, task_id=task_id, status=models.TaskStatus.processing.value, progress=90)
        _callback_internal({"task_id": task_id, "status": "processing", "progress": 90})

        # completed
        _set_task_state(
            db,
            task_id=task_id,
            status=models.TaskStatus.completed.value,
            progress=100,
            output_path=output_path,
            error_msg=None,
        )
        _callback_internal(
            {
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "output_path": output_path,
                "error_msg": None,
            }
        )

    except Exception as e:
        logger.error("Task %d failed: %s", task_id, e, exc_info=True)
        _set_task_state(
            db,
            task_id=task_id,
            status=models.TaskStatus.failed.value,
            progress=100,
            error_msg=str(e),
        )
        _callback_internal(
            {
                "task_id": task_id,
                "status": "failed",
                "progress": 100,
                "output_path": None,
                "error_msg": str(e),
            }
        )
    finally:
        db.close()


def enqueue_task(
    task_id: int,
    user_id: int,
    input_rel_path: str,
    params: Optional[Dict[str, Any]] = None,
):
    """
    Queue:
      - USE_REDIS_QUEUE=1 => Redis list rpush (worker.py uses blpop + json.loads)
      - else => run sync
    """
    payload = {
        "task_id": int(task_id),
        "user_id": int(user_id),
        "input_path": input_rel_path,
        "params": params or {},
    }

    use_redis = os.getenv("USE_REDIS_QUEUE", "0") == "1"
    if use_redis:
        from redis import Redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        queue_name = os.getenv("REDIS_QUEUE_NAME", "ai_tasks")

        r = Redis.from_url(redis_url, decode_responses=True)
        r.rpush(queue_name, json.dumps(payload, ensure_ascii=False))
        logger.info("Task %d enqueued to Redis (queue=%s)", task_id, queue_name)
        return

    logger.info("Task %d processing synchronously (Redis queue disabled)", task_id)
    process_payload(payload)
