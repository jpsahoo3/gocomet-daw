import os
import redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

r = redis.Redis.from_url(REDIS_URL, decode_responses=True)


def get_redis():
    return r


def _key(region: str, tenant: str, name: str) -> str:
    return f"{region}:{tenant}:{name}"


GEO_KEY = "drivers:geo"
DRIVER_LOCK_PREFIX = "driver:lock:"


def _lock_driver(region: str, tenant: str, driver_id: str) -> bool:
    return r.set(_key(region, tenant, DRIVER_LOCK_PREFIX + driver_id), "1", nx=True, ex=60)


def find_nearest_driver(region: str, tenant: str, lat: float, lon: float, exclude=None):
    exclude = exclude or set()

    nearby = r.georadius(GEO_KEY, lon, lat, 5, unit="km")

    for driver_id in nearby:
        if driver_id in exclude:
            continue

        if _lock_driver(region, tenant, driver_id):
            return driver_id

    return None
