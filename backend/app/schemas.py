from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel


# =====================
# Common
# =====================

class OkResponse(BaseModel):
    ok: bool = True
    message: str = "ok"


class ErrorResponse(BaseModel):
    detail: str


# =====================
# User
# =====================

class UserMeResponse(BaseModel):
    id: int
    username: str
    email: str
    avatar_emoji: str = "🌸"
    created_at: datetime


class UserRegister(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    identifier: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UpdateAvatarRequest(BaseModel):
    avatar_emoji: str


# =====================
# Password
# =====================

class PasswordForgotRequest(BaseModel):
    email: str


class PasswordResetRequest(BaseModel):
    token: str
    new_password: str


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str


class PasswordResetByCodeRequest(BaseModel):
    email: str
    code: str
    new_password: str


class PasswordForgotCodeResponse(BaseModel):
    ok: bool = True
    cooldown_seconds: int = 60


# =====================
# Cartoon Styles
# =====================

CARTOON_STYLES = {
    "warm_cartoon": {"label": "温暖卡通", "emoji": "🧸", "desc": "柔和线条，暖色调，治愈感"},
    "soft_anime": {"label": "柔光动漫", "emoji": "🌸", "desc": "日系柔光，梦幻粉彩"},
    "watercolor": {"label": "水彩手绘", "emoji": "🎨", "desc": "水彩晕染，艺术质感"},
    "dreamy": {"label": "梦境童话", "emoji": "🦋", "desc": "童话色彩，如梦似幻"},
    "ghibli": {"label": "吉卜力风", "emoji": "🌿", "desc": "宫崎骏风格，自然治愈"},
    "chibi": {"label": "Q版萌化", "emoji": "🐱", "desc": "大头萌系，可爱减压"},
    "pixel_art": {"label": "像素回忆", "emoji": "👾", "desc": "复古像素，怀旧温暖"},
    "sketch": {"label": "素描速写", "emoji": "✏️", "desc": "铅笔质感，简约温柔"},
}

CartoonStyle = Literal[
    "warm_cartoon", "soft_anime", "watercolor", "dreamy",
    "ghibli", "chibi", "pixel_art", "sketch",
]


# =====================
# Task
# =====================

TaskStatus = Literal["queued", "processing", "completed", "failed"]
TaskSort = Literal["id_desc", "created_desc", "progress_desc"]


class TaskStatusResponse(BaseModel):
    task_id: int
    status: TaskStatus
    progress: int
    style: str = "warm_cartoon"
    title: Optional[str] = None
    params: Dict[str, Any] = {}
    error_msg: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DownloadResponse(BaseModel):
    download_url: str


class TaskItem(BaseModel):
    task_id: int
    user_id: int
    status: TaskStatus
    progress: int
    style: str = "warm_cartoon"
    title: Optional[str] = None
    params: Dict[str, Any] = {}
    error_msg: Optional[str] = None
    input_url: Optional[str] = None
    output_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TaskListResponse(BaseModel):
    items: List[TaskItem]
    page: int
    page_size: int
    total: int
    pages: int
    self_url: str
    next_url: Optional[str] = None
    prev_url: Optional[str] = None


class TaskCancelResponse(BaseModel):
    ok: bool = True
    task_id: int
    status: str


class TaskRetryResponse(BaseModel):
    ok: bool = True
    task_id: int
    status: str


class TaskDeleteResponse(BaseModel):
    ok: bool = True
    task_id: int


# =====================
# Mood / Interaction
# =====================

class MoodCreate(BaseModel):
    mood: Literal["great", "good", "okay", "sad", "anxious"]
    emoji: str = "😊"
    note: Optional[str] = None


class MoodItem(BaseModel):
    id: int
    mood: str
    emoji: str
    note: Optional[str] = None
    affirmation: Optional[str] = None
    created_at: datetime


class MoodListResponse(BaseModel):
    items: List[MoodItem]
    total: int


# =====================
# Health / System
# =====================

class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str
    storage: str


class UploadResponse(BaseModel):
    code: int = 0
    data: Dict[str, Any]


class StyleInfo(BaseModel):
    key: str
    label: str
    emoji: str
    desc: str


class StyleListResponse(BaseModel):
    styles: List[StyleInfo]
