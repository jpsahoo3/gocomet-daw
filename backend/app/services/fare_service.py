from datetime import datetime

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

    duration_min = (end_time - start_time).total_seconds() / 60

    surge = get_surge_multiplier(cell)

    fare = (
        BASE_FARE
        + (DISTANCE_RATE * distance_km)
        + (TIME_RATE * duration_min)
    ) * surge

    return round(fare, 2)
