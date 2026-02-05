from app.services.matching_service import get_redis


MIN_SURGE = 1.0
MAX_SURGE = 3.0


def _compute_surge(active_rides: int, available_drivers: int) -> float:
    """
    Simple real-time surge formula.
    Safe, bounded, production-style.
    """
    if available_drivers <= 0:
        return MAX_SURGE

    ratio = active_rides / available_drivers

    surge = max(MIN_SURGE, min(MAX_SURGE, 1 + ratio))
    return round(surge, 2)


def get_surge_multiplier(cell: str) -> float:
    """
    Read cached surge from Redis.
    Default = 1.0
    """
    r = get_redis()

    value = r.get(f"surge:{cell}")
    if not value:
        return 1.0

    return float(value)


def update_surge(cell: str):
    """
    Recalculate surge based on live demand.
    """
    r = get_redis()

    active = int(r.get(f"area:{cell}:active_rides") or 0)
    drivers = int(r.get(f"area:{cell}:available_drivers") or 0)

    surge = _compute_surge(active, drivers)

    r.set(f"surge:{cell}", surge)
