import enum
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from .db import Base


class TaskStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False, default="")
    avatar_emoji = Column(String(16), nullable=False, default="🌸")
    wx_openid = Column(String(128), unique=True, index=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", back_populates="user")
    moods = relationship("MoodEntry", back_populates="user")
    weekly_summaries = relationship("WeeklySummary", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String(32), nullable=False, default=TaskStatus.queued.value)
    progress = Column(Integer, nullable=False, default=0)

    input_path = Column(String(1024), nullable=False)
    output_path = Column(String(1024), nullable=True)

    # Legacy cartoon field, kept for backwards compat
    style = Column(String(64), nullable=True)
    title = Column(String(256), nullable=True)
    params_json = Column(Text, nullable=False, default="{}")
    error_msg = Column(Text, nullable=True)

    # --- New emotion fields ---
    user_context = Column(Text, nullable=True)
    scene_description = Column(Text, nullable=True)
    emotion = Column(String(32), nullable=True)
    emotion_emoji = Column(String(16), nullable=True)
    generated_title = Column(String(256), nullable=True)
    generated_text = Column(Text, nullable=True)
    tags_json = Column(Text, nullable=True)
    voice_path = Column(String(1024), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="tasks")

    output_url: str | None = None
    input_url: str | None = None
    voice_url: str | None = None


class MoodEntry(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mood = Column(String(32), nullable=False)
    emoji = Column(String(16), nullable=False, default="😊")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="moods")


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    summary_text = Column(Text, nullable=True)
    mood_trend = Column(String(128), nullable=True)
    tags_json = Column(Text, nullable=True)
    encouragement = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="weekly_summaries")
