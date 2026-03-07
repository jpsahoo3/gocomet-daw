import logging

from app.services.matching_service import get_redis

logger = logging.getLogger(__name__)

MIN_SURGE = 1.0
MAX_SURGE = 3.0


def _compute_surge(active_rides: int, available_drivers: int) -> float:
    if available_drivers <= 0:
        return MAX_SURGE
    ratio = active_rides / available_drivers
    return round(max(MIN_SURGE, min(MAX_SURGE, 1 + ratio)), 2)


def get_surge_multiplier(cell: str) -> float:
    r = get_redis()
    value = r.get(f"surge:{cell}")
    multiplier = float(value) if value else 1.0
    logger.debug("Surge multiplier | cell=%s value=%.2f", cell, multiplier)
    return multiplier


def update_surge(cell: str):
    r = get_redis()
    active = int(r.get(f"area:{cell}:active_rides") or 0)
    drivers = int(r.get(f"area:{cell}:available_drivers") or 0)
    surge = _compute_surge(active, drivers)
    r.set(f"surge:{cell}", surge)
    logger.info(
        "Surge updated | cell=%s active_rides=%d available_drivers=%d surge=%.2f",
        cell, active, drivers, surge,
    )
