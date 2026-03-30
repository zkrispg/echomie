import json
import math
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import (
    FastAPI, Depends, HTTPException, UploadFile, File, Form,
    status, Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import (
    get_swagger_ui_html, get_swagger_ui_oauth2_redirect_html,
)
from fastapi.openapi.utils import get_openapi
from sqlalchemy import or_, text
from sqlalchemy.orm import Session

from .db import Base, engine, get_db
from . import models, schemas
from .auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, create_password_reset_token, verify_password_reset_token,
)
from .storage import StorageService, BASE_DIR as STORAGE_BASE_DIR
from .internal import router as internal_router
from .mailer import send_email
from .logging_config import setup_logging, get_logger
from .password_code import (
    generate_code, save_reset_code, verify_reset_code,
    can_send_code, set_cooldown, PWD_RESET_CODE_COOLDOWN_SECONDS,
)

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("app.main")

MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "500"))
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# ==================== Affirmations ====================
AFFIRMATIONS = {
    "great": [
        "你今天状态真好！继续保持这份快乐吧 ✨",
        "开心的你，也在治愈着身边的人呢 🌈",
        "好心情是最好的礼物，你值得拥有 🎁",
        "阳光正好，你的笑容更好 ☀️",
    ],
    "good": [
        "今天也是元气满满的一天呢 🌿",
        "你正在做得很好，别忘了给自己一个拥抱 🤗",
        "每一个平凡的日子，都有属于你的小确幸 🍀",
        "温柔地对待自己，你已经很棒了 💫",
    ],
    "okay": [
        "平淡也是一种幸福，慢慢来就好 🌸",
        "没关系，不需要每天都元气满满 🧸",
        "给自己泡杯茶，看看窗外的风景吧 🍵",
        "今天也辛苦了，你做得比你以为的要好 💕",
    ],
    "sad": [
        "难过的时候，允许自己哭一会儿也没关系 🌧️",
        "你不需要一直坚强，EchoMie 会陪着你 🫂",
        "每一次低谷，都是在为下一次绽放蓄力 🌱",
        "把悲伤画成画吧，让艺术温柔地治愈你 🎨",
        "星星也需要黑夜才能闪耀，你也是 ⭐",
    ],
    "anxious": [
        "深呼吸…吸…呼…你是安全的 🍃",
        "焦虑只是暂时的访客，它会离开的 🦋",
        "试试用创作来安抚内心吧，EchoMie 在这里 💜",
        "把担忧交给风吧，你只需要做好当下 🌬️",
        "每一步都算数，不用着急，慢慢来 🐢",
    ],
}

def get_affirmation(mood: str) -> str:
    pool = AFFIRMATIONS.get(mood, AFFIRMATIONS["okay"])
    return random.choice(pool)


# ==================== App ====================
app = FastAPI(title="EchoMie API", version="1.0.0", docs_url=None, redoc_url=None)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    schema["openapi"] = "3.0.2"
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=False,
    allow_methods=["*"], allow_headers=["*"],
)
app.include_router(internal_router)

storage_service = StorageService()
app.mount("/static", StaticFiles(directory=str(STORAGE_BASE_DIR)), name="static")


# ---- Swagger UI ----
def _find_swagger_dist_dir():
    import importlib.util
    from pathlib import Path
    spec = importlib.util.find_spec("swagger_ui_bundle")
    if spec is None or not spec.origin:
        return None
    base_dir = Path(spec.origin).resolve().parent
    for p in base_dir.rglob("swagger-ui-bundle.js"):
        return p.parent
    return None


_swagger_dist = _find_swagger_dist_dir()
if _swagger_dist and (_swagger_dist / "swagger-ui-bundle.js").exists():
    app.mount("/swagger-ui", StaticFiles(directory=str(_swagger_dist)), name="swagger-ui")

    @app.get("/docs", include_in_schema=False)
    def custom_docs():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/swagger-ui/swagger-ui-bundle.js",
            swagger_css_url="/swagger-ui/swagger-ui.css",
        )
else:
    @app.get("/docs", include_in_schema=False)
    def docs_hint():
        return HTMLResponse("<html><body><h2>pip install swagger-ui-bundle</h2></body></html>")


# ==================== Helpers ====================
def _safe_load_params(s: str) -> Dict[str, Any]:
    if not s:
        return {}
    try:
        obj = json.loads(s)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _build_page_url(request: Request, page: int, page_size: int) -> str:
    from urllib.parse import urlencode
    qp = dict(request.query_params)
    qp["page"] = str(page)
    qp["page_size"] = str(page_size)
    base = str(request.base_url).rstrip("/")
    return f"{base}{request.url.path}?{urlencode(qp, doseq=True)}"


def _abs_url(request: Request, path: str) -> str:
    base = str(request.base_url).rstrip("/")
    if not path:
        return base
    if path.startswith(("http://", "https://")):
        return path
    if not path.startswith("/"):
        path = "/" + path
    return base + path


# ==================== Startup ====================
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    logger.info("EchoMie backend started")


# ==================== System ====================
@app.get("/ping")
def ping():
    return {"ok": True, "app": "EchoMie"}


@app.get("/api/health", response_model=schemas.HealthResponse)
def health_check():
    result = {"status": "ok", "db": "ok", "redis": "unknown", "storage": "ok"}
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        result["db"] = f"error: {e}"
        result["status"] = "degraded"
    try:
        import redis as _redis
        r = _redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"), decode_responses=True)
        r.ping()
        result["redis"] = "ok"
    except Exception:
        result["redis"] = "unavailable"
    if not STORAGE_BASE_DIR.exists():
        result["storage"] = "missing"
        result["status"] = "degraded"
    return result


@app.get("/api/test")
def api_test():
    return {"message": "Hello from EchoMie! 🌸 让每一刻都温柔以待"}


# ==================== Styles ====================
@app.get("/api/styles", response_model=schemas.StyleListResponse)
def list_styles():
    items = [
        schemas.StyleInfo(key=k, label=v["label"], emoji=v["emoji"], desc=v["desc"])
        for k, v in schemas.CARTOON_STYLES.items()
    ]
    return schemas.StyleListResponse(styles=items)


# ==================== Auth ====================
@app.get("/api/me", response_model=schemas.UserMeResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return schemas.UserMeResponse(
        id=current_user.id, username=current_user.username,
        email=current_user.email, avatar_emoji=current_user.avatar_emoji or "🌸",
        created_at=current_user.created_at,
    )


@app.post("/api/register", response_model=schemas.TokenResponse)
def register_user(payload: schemas.UserRegister, db: Session = Depends(get_db)):
    email = (payload.email or "").strip()
    if "@" not in email or len(email) > 255:
        raise HTTPException(status_code=400, detail="Invalid email")
    if not payload.username or len(payload.username) < 2:
        raise HTTPException(status_code=400, detail="用户名至少2个字符")
    if not payload.password or len(payload.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    exists = db.query(models.User).filter(
        or_(models.User.username == payload.username, models.User.email == email)
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在")
    user = models.User(
        username=payload.username, email=email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("New user: id=%d, username=%s", user.id, user.username)
    return schemas.TokenResponse(access_token=create_access_token(str(user.id)))


@app.post("/api/login", response_model=schemas.TokenResponse)
def login_user(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    identifier = (payload.identifier or "").strip()
    if not identifier:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = db.query(models.User).filter(
        or_(models.User.username == identifier, models.User.email == identifier)
    ).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return schemas.TokenResponse(access_token=create_access_token(str(user.id)))


@app.put("/api/me/avatar")
def update_avatar(
    payload: schemas.UpdateAvatarRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    user.avatar_emoji = payload.avatar_emoji
    db.commit()
    return {"ok": True, "avatar_emoji": payload.avatar_emoji}


# ==================== Password ====================
@app.post("/api/password/forgot")
def password_forgot(payload: schemas.PasswordForgotRequest, request: Request, db: Session = Depends(get_db)):
    email = (payload.email or "").strip()
    if not email or "@" not in email:
        return {"ok": True}
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return {"ok": True}
    token = create_password_reset_token(user.id)
    try:
        send_email(to_email=email, subject="EchoMie - 重置密码",
                   body_text=f"Your reset token:\n\n{token}\n\nExpires in 30 min.")
    except Exception as e:
        logger.error("Email failed: %s", e)
    return {"ok": True}


@app.post("/api/password/forgot-code")
def password_forgot_code(payload: schemas.PasswordForgotRequest, db: Session = Depends(get_db)):
    email = (payload.email or "").strip()
    if not email or "@" not in email:
        return {"ok": True, "cooldown_seconds": PWD_RESET_CODE_COOLDOWN_SECONDS}
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        return {"ok": True, "cooldown_seconds": PWD_RESET_CODE_COOLDOWN_SECONDS}
    if not can_send_code(email):
        return {"ok": True, "cooldown_seconds": PWD_RESET_CODE_COOLDOWN_SECONDS}
    code = generate_code()
    save_reset_code(email=email, user_id=user.id, code=code)
    set_cooldown(email)
    try:
        send_email(
            to_email=email, subject="EchoMie - 验证码",
            body_text=f"Your code: {code}\nValid for 10 min.",
            body_html=f'<div style="font-family:sans-serif"><p>Your verification code:</p>'
                      f'<div style="font-size:28px;font-weight:bold;letter-spacing:4px">{code}</div>'
                      f'<p style="color:#888">Valid for 10 minutes</p></div>',
        )
    except Exception as e:
        logger.error("Email failed: %s", e)
    return {"ok": True, "cooldown_seconds": PWD_RESET_CODE_COOLDOWN_SECONDS}


@app.post("/api/password/reset")
def password_reset(payload: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    token = (payload.token or "").strip().strip("<>").replace(" ", "")
    user_id = verify_password_reset_token(token)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not payload.new_password or len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}


@app.post("/api/password/reset-by-code")
def password_reset_by_code(payload: schemas.PasswordResetByCodeRequest, db: Session = Depends(get_db)):
    email = (payload.email or "").strip()
    code = (payload.code or "").strip()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email")
    if not code or len(code) != 6 or not code.isdigit():
        raise HTTPException(status_code=400, detail="Invalid code")
    if not payload.new_password or len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码至少6位")
    user_id = verify_reset_code(email=email, code=code)
    if not user_id:
        raise HTTPException(status_code=400, detail="验证码无效或已过期")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}


@app.post("/api/password/change")
def password_change(
    payload: schemas.PasswordChangeRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="当前密码不正确")
    if not payload.new_password or len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少6位")
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"ok": True}


# ==================== Upload / Transform ====================
@app.post("/api/upload", response_model=schemas.UploadResponse)
def upload_file(
    file: UploadFile = File(...),
    style: str = Form(default="warm_cartoon"),
    title: str = Form(default=""),
    params_json: str = Form(default="{}"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    filename = (file.filename or "").lower()
    allowed = (".mp4", ".mov", ".avi", ".mkv", ".jpg", ".jpeg", ".png", ".webp")
    if not filename.endswith(allowed):
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    if file.size and file.size > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail=f"文件过大，最大 {MAX_UPLOAD_SIZE_MB}MB")
    if style not in schemas.CARTOON_STYLES:
        style = "warm_cartoon"
    try:
        params = json.loads(params_json or "{}")
        if not isinstance(params, dict):
            params = {}
    except Exception:
        params = {}
    params["style"] = style

    ext = os.path.splitext(file.filename or "")[1].lower()
    is_image = ext in [".jpg", ".jpeg", ".png", ".webp"]
    subdir = f"images/raw/{current_user.id}" if is_image else f"videos/raw/{current_user.id}"
    input_rel_path = storage_service.save_upload_file(file, subdir=subdir)

    task = models.Task(
        user_id=current_user.id, input_path=input_rel_path,
        status=models.TaskStatus.queued.value, progress=0,
        style=style, title=title or None,
        params_json=json.dumps(params, ensure_ascii=False),
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    try:
        from .tasks import enqueue_task
        enqueue_task(task.id, current_user.id, input_rel_path, params=params)
    except Exception as e:
        logger.error("Enqueue failed for task %d: %s", task.id, e)

    style_info = schemas.CARTOON_STYLES.get(style, {})
    return {"code": 0, "data": {
        "task_id": task.id, "style": style,
        "style_label": style_info.get("label", style),
        "title": title,
    }}


# ==================== Task APIs ====================
@app.get("/api/status", response_model=schemas.TaskStatusResponse)
def get_status(task_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return schemas.TaskStatusResponse(
        task_id=task.id, status=task.status, progress=task.progress,
        style=task.style or "warm_cartoon", title=task.title,
        params=_safe_load_params(task.params_json), error_msg=task.error_msg,
        created_at=task.created_at, updated_at=task.updated_at,
    )


@app.get("/api/download", response_model=schemas.DownloadResponse)
def download(request: Request, task_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if task.status != models.TaskStatus.completed.value or not task.output_path:
        raise HTTPException(status_code=400, detail="Task not completed")
    url = _abs_url(request, storage_service.get_public_url(task.output_path))
    return schemas.DownloadResponse(download_url=url)


@app.post("/api/tasks/{task_id}/cancel", response_model=schemas.TaskCancelResponse)
def cancel_task(task_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if task.status in (models.TaskStatus.completed.value, models.TaskStatus.failed.value):
        raise HTTPException(status_code=400, detail=f"Cannot cancel '{task.status}' task")
    task.status = models.TaskStatus.failed.value
    task.error_msg = "用户取消"
    task.progress = 0
    db.commit()
    return schemas.TaskCancelResponse(task_id=task.id, status=task.status)


@app.post("/api/tasks/{task_id}/retry", response_model=schemas.TaskRetryResponse)
def retry_task(task_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if task.status != models.TaskStatus.failed.value:
        raise HTTPException(status_code=400, detail="只能重试失败的任务")
    task.status = models.TaskStatus.queued.value
    task.progress = 0
    task.error_msg = None
    task.output_path = None
    db.commit()
    params = _safe_load_params(task.params_json)
    try:
        from .tasks import enqueue_task
        enqueue_task(task.id, current_user.id, task.input_path, params=params)
    except Exception as e:
        logger.error("Retry enqueue failed: %s", e)
    return schemas.TaskRetryResponse(task_id=task.id, status=task.status)


@app.delete("/api/tasks/{task_id}", response_model=schemas.TaskDeleteResponse)
def delete_task(task_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if task.status == models.TaskStatus.processing.value:
        raise HTTPException(status_code=400, detail="处理中的任务请先取消")
    try:
        if task.input_path:
            p = storage_service.abs_path(task.input_path)
            if p.exists():
                p.unlink()
        if task.output_path:
            p = storage_service.abs_path(task.output_path)
            if p.exists():
                p.unlink()
    except Exception as e:
        logger.warning("Cleanup failed for task %d: %s", task_id, e)
    db.delete(task)
    db.commit()
    return schemas.TaskDeleteResponse(task_id=task_id)


@app.get("/api/tasks", response_model=schemas.TaskListResponse)
def list_tasks(
    request: Request, page: int = 1, page_size: int = 20,
    status: Optional[str] = None, style: Optional[str] = None,
    sort: schemas.TaskSort = "id_desc",
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if page < 1:
        raise HTTPException(status_code=400, detail="page >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="page_size in [1,100]")
    query = db.query(models.Task).filter(models.Task.user_id == current_user.id)
    if status:
        query = query.filter(models.Task.status == status)
    if style:
        query = query.filter(models.Task.style == style)

    order = {
        "id_desc": [models.Task.id.desc()],
        "created_desc": [models.Task.created_at.desc(), models.Task.id.desc()],
        "progress_desc": [models.Task.progress.desc(), models.Task.id.desc()],
    }.get(sort, [models.Task.id.desc()])
    for o in order:
        query = query.order_by(o)

    total = query.count()
    pages = max(1, math.ceil(total / page_size)) if total else 1
    if page > pages and total > 0:
        page = pages
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for t in tasks:
        output_url = None
        input_url = None
        if t.status == models.TaskStatus.completed.value and t.output_path:
            output_url = _abs_url(request, storage_service.get_public_url(t.output_path))
        if t.input_path:
            input_url = _abs_url(request, storage_service.get_public_url(t.input_path))
        items.append(schemas.TaskItem(
            task_id=t.id, user_id=t.user_id, status=t.status, progress=t.progress,
            style=t.style or "warm_cartoon", title=t.title,
            params=_safe_load_params(t.params_json), error_msg=t.error_msg,
            input_url=input_url, output_url=output_url,
            created_at=t.created_at, updated_at=t.updated_at,
        ))

    self_url = _build_page_url(request, page, page_size)
    next_url = _build_page_url(request, page + 1, page_size) if page < pages else None
    prev_url = _build_page_url(request, page - 1, page_size) if page > 1 else None
    return schemas.TaskListResponse(
        items=items, page=page, page_size=page_size, total=total, pages=pages,
        self_url=self_url, next_url=next_url, prev_url=prev_url,
    )


# Gallery: only completed tasks
@app.get("/api/gallery", response_model=schemas.TaskListResponse)
def gallery(
    request: Request, page: int = 1, page_size: int = 20,
    style: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(models.Task).filter(
        models.Task.user_id == current_user.id,
        models.Task.status == models.TaskStatus.completed.value,
    )
    if style:
        query = query.filter(models.Task.style == style)
    query = query.order_by(models.Task.created_at.desc())

    total = query.count()
    pages = max(1, math.ceil(total / page_size)) if total else 1
    tasks = query.offset((page - 1) * page_size).limit(page_size).all()
    items = []
    for t in tasks:
        output_url = _abs_url(request, storage_service.get_public_url(t.output_path)) if t.output_path else None
        input_url = _abs_url(request, storage_service.get_public_url(t.input_path)) if t.input_path else None
        items.append(schemas.TaskItem(
            task_id=t.id, user_id=t.user_id, status=t.status, progress=t.progress,
            style=t.style or "warm_cartoon", title=t.title,
            params=_safe_load_params(t.params_json),
            input_url=input_url, output_url=output_url,
            created_at=t.created_at, updated_at=t.updated_at,
        ))
    self_url = _build_page_url(request, page, page_size)
    next_url = _build_page_url(request, page + 1, page_size) if page < pages else None
    prev_url = _build_page_url(request, page - 1, page_size) if page > 1 else None
    return schemas.TaskListResponse(
        items=items, page=page, page_size=page_size, total=total, pages=pages,
        self_url=self_url, next_url=next_url, prev_url=prev_url,
    )


# ==================== Mood / Interaction ====================
@app.post("/api/mood", response_model=schemas.MoodItem)
def create_mood(
    payload: schemas.MoodCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = models.MoodEntry(
        user_id=current_user.id, mood=payload.mood,
        emoji=payload.emoji, note=payload.note,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    aff = get_affirmation(payload.mood)
    return schemas.MoodItem(
        id=entry.id, mood=entry.mood, emoji=entry.emoji,
        note=entry.note, affirmation=aff, created_at=entry.created_at,
    )


@app.get("/api/moods", response_model=schemas.MoodListResponse)
def list_moods(
    limit: int = 30,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = (
        db.query(models.MoodEntry)
        .filter(models.MoodEntry.user_id == current_user.id)
        .order_by(models.MoodEntry.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    total = db.query(models.MoodEntry).filter(models.MoodEntry.user_id == current_user.id).count()
    items = [
        schemas.MoodItem(
            id=e.id, mood=e.mood, emoji=e.emoji, note=e.note,
            created_at=e.created_at,
        )
        for e in entries
    ]
    return schemas.MoodListResponse(items=items, total=total)


@app.get("/api/affirmation")
def get_daily_affirmation(mood: str = "okay"):
    return {"affirmation": get_affirmation(mood), "mood": mood}
