import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
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
    password_hash = Column(String(256), nullable=False)
    avatar_emoji = Column(String(16), nullable=False, default="🌸")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tasks = relationship("Task", back_populates="user")
    moods = relationship("MoodEntry", back_populates="user")


class Task(Base):
    __tablename__ = "tasks"
    __allow_unmapped__ = True

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    status = Column(String(32), nullable=False, default=TaskStatus.queued.value)
    progress = Column(Integer, nullable=False, default=0)

    input_path = Column(String(1024), nullable=False)
    output_path = Column(String(1024), nullable=True)

    style = Column(String(64), nullable=False, default="warm_cartoon")
    title = Column(String(256), nullable=True)
    params_json = Column(Text, nullable=False, default="{}")
    error_msg = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="tasks")

    output_url: str | None = None
    input_url: str | None = None


class MoodEntry(Base):
    __tablename__ = "moods"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    mood = Column(String(32), nullable=False)
    emoji = Column(String(16), nullable=False, default="😊")
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="moods")
