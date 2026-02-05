import redis
import os

def get_redis():
    url = os.getenv("REDIS_URL")
    if not url:
        raise RuntimeError("REDIS_URL not set")
    return redis.Redis.from_url(url)

def update_driver_location(driver_id: str, lat: float, lon: float):
    r = get_redis()

    # Correct redis-py GEOADD format
    r.geoadd(
        "drivers:geo",
        (lon, lat, driver_id)
    )
