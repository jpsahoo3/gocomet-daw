from datetime import datetime, timezone

from app.services.surge_service import get_surge_multiplier


BASE_FARE = 50
DISTANCE_RATE = 10      # per km
TIME_RATE = 2           # per minute


def calculate_fare(
    distance_km: float,
    start_time: datetime,
    end_time: datetime,
    cell: str = "default",
) -> float:
    """
    Realistic fare computation.
    """

    # Normalize datetimes: make both timezone-aware in UTC if needed
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    else:
        start_time = start_time.astimezone(timezone.utc)

    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    else:
        end_time = end_time.astimezone(timezone.utc)

    duration_min = (end_time - start_time).total_seconds() / 60

    surge = get_surge_multiplier(cell)

    fare = (
        BASE_FARE
        + (DISTANCE_RATE * distance_km)
        + (TIME_RATE * duration_min)
    ) * surge

    return round(fare, 2)
