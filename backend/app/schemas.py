from typing import Any, Dict, List, Optional, Literal
from datetime import datetime, date
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


class WxLoginRequest(BaseModel):
    code: str


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
# Cartoon Styles (for image/video stylization)
# =====================

CARTOON_STYLES = {
    "none": {"label": "不处理", "emoji": "🖼️", "desc": "仅情绪分析，不加卡通效果"},
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
    "none", "warm_cartoon", "soft_anime", "watercolor", "dreamy",
    "ghibli", "chibi", "pixel_art", "sketch",
]

# =====================
# Emotion types
# =====================

EMOTION_TYPES = {
    "happy": {"label": "开心", "emoji": "😊", "color": "#FFD93D"},
    "calm": {"label": "平静", "emoji": "😌", "color": "#A8D8EA"},
    "sad": {"label": "难过", "emoji": "😢", "color": "#B0C4DE"},
    "lonely": {"label": "孤独", "emoji": "🥺", "color": "#DDA0DD"},
    "tired": {"label": "疲惫", "emoji": "😴", "color": "#D3D3D3"},
    "anxious": {"label": "焦虑", "emoji": "😰", "color": "#FFB347"},
    "hopeful": {"label": "期待", "emoji": "✨", "color": "#98FB98"},
    "nostalgic": {"label": "怀念", "emoji": "🌅", "color": "#F4A460"},
    "peaceful": {"label": "安宁", "emoji": "🍃", "color": "#90EE90"},
    "excited": {"label": "兴奋", "emoji": "🎉", "color": "#FF69B4"},
}


# =====================
# Task (emotion card)
# =====================

TaskStatus = Literal["queued", "processing", "completed", "failed"]
TaskSort = Literal["id_desc", "created_desc", "progress_desc"]


class StyleInfo(BaseModel):
    key: str
    label: str
    emoji: str
    desc: str


class StyleListResponse(BaseModel):
    styles: List[StyleInfo]


class TaskStatusResponse(BaseModel):
    task_id: int
    status: TaskStatus
    progress: int
    style: Optional[str] = None
    error_msg: Optional[str] = None
    # Emotion card fields
    user_context: Optional[str] = None
    scene_description: Optional[str] = None
    emotion: Optional[str] = None
    emotion_emoji: Optional[str] = None
    generated_title: Optional[str] = None
    generated_text: Optional[str] = None
    tags: List[str] = []
    voice_url: Optional[str] = None
    input_url: Optional[str] = None
    output_url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DownloadResponse(BaseModel):
    download_url: str


class TaskItem(BaseModel):
    task_id: int
    user_id: int
    status: TaskStatus
    progress: int
    style: Optional[str] = None
    error_msg: Optional[str] = None
    # Emotion card fields
    user_context: Optional[str] = None
    scene_description: Optional[str] = None
    emotion: Optional[str] = None
    emotion_emoji: Optional[str] = None
    generated_title: Optional[str] = None
    generated_text: Optional[str] = None
    tags: List[str] = []
    voice_url: Optional[str] = None
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
# Weekly Summary
# =====================

class WeeklySummaryItem(BaseModel):
    id: int
    week_start: date
    week_end: date
    summary_text: Optional[str] = None
    mood_trend: Optional[str] = None
    tags: List[str] = []
    encouragement: Optional[str] = None
    created_at: datetime


class WeeklySummaryListResponse(BaseModel):
    items: List[WeeklySummaryItem]
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


# =====================
# Chat
# =====================

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = None
