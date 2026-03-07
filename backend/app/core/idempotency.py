from app.core.redis_client import get_redis

def check_idempotency(key):
    r = get_redis()
    return r.get(f"idempotency:{key}")

def save_idempotency(key, response):
    r = get_redis()
    r.setex(f"idempotency:{key}", 300, response)
