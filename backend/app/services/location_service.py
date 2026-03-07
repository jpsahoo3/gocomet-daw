from app.core.redis_client import get_redis

def update_driver_location(driver_id: str, lat: float, lon: float):
    r = get_redis()
    r.geoadd("drivers:geo", (lon, lat, driver_id))
