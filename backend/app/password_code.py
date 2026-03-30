import json
import os
import random
import time
from typing import Optional

import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

PWD_RESET_CODE_TTL_SECONDS = int(os.getenv("PWD_RESET_CODE_TTL_SECONDS", "600"))
PWD_RESET_CODE_COOLDOWN_SECONDS = int(os.getenv("PWD_RESET_CODE_COOLDOWN_SECONDS", "60"))

_rds: Optional[redis.Redis] = None


def _get_redis() -> redis.Redis:
    global _rds
    if _rds is None:
        _rds = redis.from_url(REDIS_URL, decode_responses=True)
    return _rds


def _key(email: str) -> str:
    return f"pwd_reset_code:{email.lower().strip()}"


def _cooldown_key(email: str) -> str:
    return f"pwd_reset_code_cd:{email.lower().strip()}"


def generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def can_send_code(email: str) -> bool:
    try:
        return _get_redis().get(_cooldown_key(email)) is None
    except redis.ConnectionError:
        return True


def set_cooldown(email: str) -> None:
    try:
        _get_redis().setex(_cooldown_key(email), PWD_RESET_CODE_COOLDOWN_SECONDS, "1")
    except redis.ConnectionError:
        pass


def save_reset_code(email: str, user_id: int, code: str) -> None:
    payload = {
        "code": code,
        "user_id": int(user_id),
        "expire_at": int(time.time()) + PWD_RESET_CODE_TTL_SECONDS,
    }
    _get_redis().setex(_key(email), PWD_RESET_CODE_TTL_SECONDS, json.dumps(payload))


def verify_reset_code(email: str, code: str) -> Optional[int]:
    rds = _get_redis()
    raw = rds.get(_key(email))
    if not raw:
        return None

    try:
        data = json.loads(raw)
    except Exception:
        return None

    if str(data.get("code")) != str(code):
        return None

    user_id = data.get("user_id")
    if user_id is None:
        return None

    rds.delete(_key(email))
    return int(user_id)
