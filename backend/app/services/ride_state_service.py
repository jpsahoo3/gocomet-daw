import redis
import os

def get_redis():
    url = os.getenv("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL not set")
    return redis.Redis.from_url(url)

def set_ride_state(ride_id, state):
    r = get_redis()
    r.hset(f"ride:{ride_id}", "state", state)

def get_ride_state(ride_id):
    r = get_redis()
    return r.hget(f"ride:{ride_id}", "state")
