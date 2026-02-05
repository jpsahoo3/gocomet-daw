from sqlalchemy.orm import Session

from app.models.ride import Ride
from app.services.matching_service import find_nearest_driver, get_redis


OFFER_TTL = 15


def retry_dispatch(db: Session, ride_id: str):
    """
    Try offering ride to next available driver.
    """

    r = get_redis()

    # drivers who already rejected
    rejected = set(r.smembers(f"ride:rejected:{ride_id}") or [])

    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        return None, "NOT_FOUND"

    driver = find_nearest_driver(0, 0, exclude=rejected)  # simplified geo reuse

    if not driver:
        ride.status = "NO_DRIVER"
        db.commit()
        return None, "NO_DRIVER"

    ride.status = "OFFERED"
    db.commit()

    r.setex(f"ride:offer:{ride_id}", OFFER_TTL, driver)

    return driver, "OFFERED"
