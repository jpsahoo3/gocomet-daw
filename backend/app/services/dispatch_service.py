import logging

from sqlalchemy.orm import Session

from app.models.ride import Ride
from app.services.matching_service import find_nearest_driver_for_redispatch, get_redis

logger = logging.getLogger(__name__)

OFFER_TTL = 60


def retry_dispatch(db: Session, ride_id: str):
    """
    Re-offer a declined/expired ride to the next available driver.
    Uses the stored pickup coordinates for the same 5km radius search.
    """
    r = get_redis()

    rejected = set(r.smembers(f"ride:rejected:{ride_id}") or [])
    logger.info("Retry dispatch | ride_id=%s rejected_drivers=%s", ride_id, rejected)

    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        logger.error("Retry dispatch: ride not found | ride_id=%s", ride_id)
        return None, "NOT_FOUND"

    region = "in"   # Ride model doesn't persist region; use tenant default
    tenant = ride.tenant_id

    # Use the ride's stored pickup coordinates for a realistic proximity search
    lat = ride.pickup_lat or 0.0
    lon = ride.pickup_lon or 0.0
    if not ride.pickup_lat:
        logger.warning(
            "Ride has no pickup coordinates; re-dispatch will use wide search | ride_id=%s",
            ride_id,
        )

    driver = find_nearest_driver_for_redispatch(region, tenant, lat, lon, exclude=rejected)

    if not driver:
        logger.warning("Retry dispatch: no driver found | ride_id=%s", ride_id)
        ride.status = "NO_DRIVER"
        db.commit()
        return None, "NO_DRIVER"

    ride.status = "OFFERED"
    db.commit()

    r.setex(f"ride:offer:{ride_id}", OFFER_TTL, driver)
    logger.info("Retry dispatch successful | ride_id=%s new_driver=%s", ride_id, driver)

    return driver, "OFFERED"
