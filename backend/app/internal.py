import os
from typing import Optional, Literal

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .db import get_db
from . import models

router = APIRouter(prefix="/internal", tags=["internal"])

TaskStatus = Literal["queued", "processing", "completed", "failed"]


class TaskCallbackIn(BaseModel):
    task_id: int
    status: TaskStatus
    progress: int = 0
    output_path: Optional[str] = None
    error_msg: Optional[str] = None


class InternalOk(BaseModel):
    code: int = 0
    message: str = "ok"
    data: dict


def _require_internal_token(x_internal_token: Optional[str]):
    expected = os.getenv("INTERNAL_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=500, detail="INTERNAL_TOKEN not configured")
    if x_internal_token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid internal token")


@router.post("/task_callback", response_model=InternalOk)
def task_callback(
    payload: TaskCallbackIn,
    x_internal_token: Optional[str] = Header(default=None, alias="X-Internal-Token"),
    db: Session = Depends(get_db),
):
    _require_internal_token(x_internal_token)

    task = db.query(models.Task).filter(models.Task.id == payload.task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 写入状态/进度（统一字符串）
    task.status = str(payload.status)
    task.progress = max(0, min(100, int(payload.progress)))

    # completed 必须有 output_path
    if payload.status == "completed" and not payload.output_path:
        raise HTTPException(status_code=400, detail="output_path required when completed")

    if payload.output_path is not None:
        task.output_path = payload.output_path

    # error_msg 处理：失败写入；完成默认清空（避免残留）
    if payload.error_msg is not None:
        task.error_msg = payload.error_msg
    else:
        if payload.status == "completed":
            task.error_msg = None

    db.commit()
    return {"code": 0, "message": "ok", "data": {"task_id": payload.task_id}}
