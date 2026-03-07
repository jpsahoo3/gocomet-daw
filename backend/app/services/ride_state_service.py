from app.core.redis_client import get_redis

def set_ride_state(ride_id, state):
    r = get_redis()
    r.hset(f"ride:{ride_id}", "state", state)

def get_ride_state(ride_id):
    r = get_redis()
    return r.hget(f"ride:{ride_id}", "state")
