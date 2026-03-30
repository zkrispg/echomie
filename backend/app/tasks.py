import json
import os
from pathlib import Path
from uuid import uuid4
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from .db import SessionLocal
from . import models
from .storage import StorageService
from .logging_config import get_logger
from .ai_service import (
    extract_key_frames,
    analyze_scene,
    generate_emotion_card,
    generate_voice,
)
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
    **extra_fields,
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

    for k, v in extra_fields.items():
        if hasattr(task, k) and v is not None:
            setattr(task, k, v)

    db.commit()
    return task


def _callback_internal(cb: Dict[str, Any]) -> None:
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
# AI emotion processing
# ---------------------------

def _process_emotion(
    storage: StorageService,
    input_path: str,
    user_id: int,
    user_context: str,
    media_type: str,
    task_id: int,
    style: str,
    db: Session,
) -> Dict[str, Any]:
    """Run: key-frames → VLM → LLM → TTS → cartoon effect. Returns result dict."""

    src_abs = str(storage.abs_path(input_path))

    # Step 1: Get the image to analyze
    if media_type == "video":
        frames = extract_key_frames(src_abs, n=3)
        analysis_image = frames[len(frames) // 2] if frames else src_abs
    else:
        analysis_image = src_abs

    _set_task_state(db, task_id, models.TaskStatus.processing.value, progress=20)
    _callback_internal({"task_id": task_id, "status": "processing", "progress": 20})

    # Step 2: VLM scene analysis
    analysis = analyze_scene(analysis_image, user_context)

    _set_task_state(db, task_id, models.TaskStatus.processing.value, progress=35,
                    scene_description=analysis.get("scene", ""),
                    emotion=analysis.get("emotion", "calm"))
    _callback_internal({"task_id": task_id, "status": "processing", "progress": 35})

    # Step 3: LLM emotion card generation
    card = generate_emotion_card(analysis, user_context)

    _set_task_state(db, task_id, models.TaskStatus.processing.value, progress=50,
                    generated_title=card.get("title"),
                    generated_text=card.get("healing_text"),
                    emotion_emoji=card.get("emotion_emoji"),
                    tags_json=json.dumps(card.get("tags", []), ensure_ascii=False))
    _callback_internal({"task_id": task_id, "status": "processing", "progress": 50})

    # Step 4: TTS voice generation
    voice_rel = ""
    healing_text = card.get("healing_text", "")
    if healing_text:
        voice_dir = storage.base_dir / "voice" / str(user_id)
        voice_dir.mkdir(parents=True, exist_ok=True)
        voice_file = voice_dir / f"{uuid4().hex}.mp3"
        result_path = generate_voice(healing_text, str(voice_file))
        if result_path:
            voice_rel = voice_file.relative_to(storage.base_dir).as_posix()

    _set_task_state(db, task_id, models.TaskStatus.processing.value, progress=65,
                    voice_path=voice_rel if voice_rel else None)
    _callback_internal({"task_id": task_id, "status": "processing", "progress": 65})

    # Step 5: Cartoon style effect (if selected)
    output_rel = ""
    logger.info("Task %d: style='%s', media_type='%s'", task_id, style, media_type)
    if style and style != "none":
        is_image = media_type == "image"
        subdir = f"images/output/{user_id}" if is_image else f"videos/output/{user_id}"
        ext = Path(input_path).suffix
        out_dir = storage.base_dir / subdir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{uuid4().hex}{ext}"

        def _progress_cb(pct: int):
            scaled = 65 + int(pct * 0.30)
            _set_task_state(db, task_id, models.TaskStatus.processing.value, progress=scaled)
            _callback_internal({"task_id": task_id, "status": "processing", "progress": scaled})

        if is_image:
            apply_image_effect(src_abs, str(out_file), style)
        else:
            apply_video_effect(src_abs, str(out_file), style, progress_cb=_progress_cb)

        output_rel = out_file.relative_to(storage.base_dir).as_posix()
        logger.info("Task %d: style effect '%s' applied -> %s", task_id, style, output_rel)
    else:
        logger.info("Task %d: no style selected (style='%s'), skipping effect", task_id, style)

    _set_task_state(db, task_id, models.TaskStatus.processing.value, progress=95)
    _callback_internal({"task_id": task_id, "status": "processing", "progress": 95})

    return {
        "scene_description": analysis.get("scene", ""),
        "emotion": analysis.get("emotion", "calm"),
        "emotion_emoji": card.get("emotion_emoji", "🌸"),
        "generated_title": card.get("title", ""),
        "generated_text": healing_text,
        "tags_json": json.dumps(card.get("tags", []), ensure_ascii=False),
        "voice_path": voice_rel,
        "output_path": output_rel if output_rel else None,
    }


# ---------------------------
# Worker entry
# ---------------------------
def process_payload(payload: Dict[str, Any]):
    task_id = int(payload["task_id"])
    user_id = int(payload["user_id"])
    input_path = payload["input_path"]
    params = payload.get("params") or {}
    user_context = params.get("context", "")
    style = params.get("style", "none")

    db: Session = SessionLocal()
    storage = StorageService()

    try:
        _set_task_state(db, task_id=task_id, status=models.TaskStatus.processing.value, progress=5)
        _callback_internal({"task_id": task_id, "status": "processing", "progress": 5})

        media_type = _guess_media_type(input_path)
        if media_type == "unknown":
            raise ValueError(f"Unsupported file type: {Path(input_path).suffix}")

        _set_task_state(db, task_id=task_id, status=models.TaskStatus.processing.value, progress=10)
        _callback_internal({"task_id": task_id, "status": "processing", "progress": 10})

        result = _process_emotion(storage, input_path, user_id, user_context, media_type, task_id, style, db)

        final_output = result.pop("output_path", None) or input_path
        _set_task_state(
            db,
            task_id=task_id,
            status=models.TaskStatus.completed.value,
            progress=100,
            output_path=final_output,
            error_msg=None,
            **result,
        )
        _callback_internal({
            "task_id": task_id, "status": "completed",
            "progress": 100, "output_path": input_path, "error_msg": None,
        })

    except Exception as e:
        logger.error("Task %d failed: %s", task_id, e, exc_info=True)
        _set_task_state(
            db, task_id=task_id,
            status=models.TaskStatus.failed.value, progress=100, error_msg=str(e),
        )
        _callback_internal({
            "task_id": task_id, "status": "failed",
            "progress": 100, "output_path": None, "error_msg": str(e),
        })
    finally:
        db.close()


def enqueue_task(
    task_id: int,
    user_id: int,
    input_rel_path: str,
    params: Optional[Dict[str, Any]] = None,
):
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
