import logging

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)

GEO_KEY = "drivers:geo"
DRIVER_LOCK_PREFIX = "driver:lock:"
DRIVER_STATUS_PREFIX = "driver:status:"   # value: "offline" means unavailable
SEARCH_RADIUS_KM = 5


def _lock_driver(region: str, tenant: str, driver_id: str) -> bool:
    """Atomically lock a driver (NX). Returns True if lock was acquired."""
    r = get_redis()
    acquired = bool(r.set(f"{DRIVER_LOCK_PREFIX}{driver_id}", "1", nx=True, ex=60))
    if not acquired:
        logger.debug("Driver already locked | driver=%s", driver_id)
    return acquired


def _is_driver_online(driver_id: str) -> bool:
    """Return True unless the driver has explicitly gone offline."""
    r = get_redis()
    status = r.get(f"{DRIVER_STATUS_PREFIX}{driver_id}")
    return status != "offline"


def find_nearest_driver(region: str, tenant: str, lat: float, lon: float, exclude=None):
    """Return the closest available, online, unlocked driver within SEARCH_RADIUS_KM."""
    exclude = exclude or set()
    r = get_redis()

    nearby = r.georadius(GEO_KEY, lon, lat, SEARCH_RADIUS_KM, unit="km")
    logger.debug(
        "Geo search | lat=%.4f lon=%.4f radius=%dkm candidates=%s",
        lat, lon, SEARCH_RADIUS_KM, nearby,
    )

    for driver_id in nearby:
        if driver_id in exclude:
            logger.debug("Skipping excluded driver | driver=%s", driver_id)
            continue
        if not _is_driver_online(driver_id):
            logger.debug("Skipping offline driver | driver=%s", driver_id)
            continue
        if _lock_driver(region, tenant, driver_id):
            logger.info("Driver matched | driver=%s lat=%.4f lon=%.4f", driver_id, lat, lon)
            return driver_id

    logger.warning(
        "No driver available within %dkm | lat=%.4f lon=%.4f excluded=%s",
        SEARCH_RADIUS_KM, lat, lon, exclude,
    )
    return None


def find_nearest_driver_for_redispatch(
    region: str, tenant: str, lat: float, lon: float, exclude=None
):
    """
    Re-dispatch: try same 5km radius first, then widen if no one is nearby.
    The widened fallback keeps the system working in low-density / dev environments
    while production deployments will almost always find a driver in the 5km pass.
    """
    driver = find_nearest_driver(region, tenant, lat, lon, exclude=exclude)
    if driver:
        return driver

    # Widen search — any registered, unlocked driver on the platform
    logger.info(
        "Re-dispatch: no driver in %dkm, widening search | lat=%.4f lon=%.4f",
        SEARCH_RADIUS_KM, lat, lon,
    )
    exclude = exclude or set()
    r = get_redis()
    all_drivers = r.georadius(GEO_KEY, lon, lat, 20015, unit="km")

    for driver_id in all_drivers:
        if driver_id in exclude:
            continue
        if not _is_driver_online(driver_id):
            continue
        if _lock_driver(region, tenant, driver_id):
            logger.info("Re-dispatch wide-search matched | driver=%s", driver_id)
            return driver_id

    logger.error("Re-dispatch exhausted all drivers | excluded=%s", exclude)
    return None
