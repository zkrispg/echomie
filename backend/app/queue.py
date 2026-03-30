import json
import os
from typing import Any, Dict

import redis


QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "ai_tasks")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def get_redis() -> redis.Redis:
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def push_task(payload: Dict[str, Any]) -> None:
    r = get_redis()
    r.rpush(QUEUE_NAME, json.dumps(payload))


def pop_task(block_seconds: int = 5) -> Dict[str, Any] | None:
    r = get_redis()
    item = r.blpop(QUEUE_NAME, timeout=block_seconds)
    if not item:
        return None
    _q, raw = item
    return json.loads(raw)
