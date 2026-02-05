import redis
import os

def get_redis():
    url = os.getenv("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL not set")
    return redis.Redis.from_url(url)

def check_idempotency(key):
    r = get_redis()
    return r.get(f"idempotency:{key}")

def save_idempotency(key, response):
    r = get_redis()
    r.setex(f"idempotency:{key}", 300, response)
