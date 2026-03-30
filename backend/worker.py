import json
import os
import signal
import sys
import time

import redis

from app.tasks import process_payload
from app.logging_config import setup_logging, get_logger

setup_logging(os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("worker")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "ai_tasks")

_running = True


def _shutdown(signum, frame):
    global _running
    logger.info("Received signal %s, shutting down gracefully...", signum)
    _running = False


signal.signal(signal.SIGINT, _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


def make_redis():
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def main():
    r = make_redis()
    logger.info("Worker started. queue=%s, redis=%s", QUEUE_NAME, REDIS_URL)

    while _running:
        try:
            item = r.blpop(QUEUE_NAME, timeout=5)
            if not item:
                continue

            _q, raw = item
            payload = json.loads(raw)
            task_id = payload.get("task_id")
            logger.info(
                "Processing task %s (user=%s, params=%s)",
                task_id,
                payload.get("user_id"),
                payload.get("params"),
            )

            process_payload(payload)

            logger.info("Task %s completed", task_id)
            time.sleep(0.1)

        except (redis.exceptions.ConnectionError, ConnectionResetError) as e:
            logger.warning("Redis connection error: %s (reconnect in 2s)", e)
            time.sleep(2)
            try:
                r = make_redis()
            except Exception:
                pass

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in queue: %s", e)

        except Exception as e:
            logger.error("Worker error: %s", e, exc_info=True)
            time.sleep(1)

    logger.info("Worker stopped.")


if __name__ == "__main__":
    main()
