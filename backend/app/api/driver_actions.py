from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.ride import Ride
from app.services.matching_service import get_redis
from app.services.dispatch_service import retry_dispatch
from app.websocket.ws import manager
import logging

router = APIRouter()


def get_db() -> Session:
    return SessionLocal()


@router.post("/v1/drivers/{driver_id}/accept/{ride_id}")
def accept_ride(driver_id: str, ride_id: str, background_tasks: BackgroundTasks):
    db = get_db()
    r = get_redis()

    key = f"ride:offer:{ride_id}"
    offered_driver = r.get(key)
    logger = logging.getLogger(__name__)
    try:
        keys = r.keys("ride:offer:*")
        logger.info("Checking offer key=%s value=%s all_offer_keys=%s", key, offered_driver, keys)
    except Exception:
        pass
    # fallback print to ensure visibility
    try:
        print(f"Checking offer key={key} value={offered_driver} all_offer_keys={r.keys('ride:offer:*')}")
    except Exception:
        pass

    if not offered_driver or offered_driver != driver_id:
        raise HTTPException(status_code=404, detail="Offer expired or invalid")

    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    ride.status = "ASSIGNED"
    ride.driver_id = driver_id
    db.commit()

    r.delete(f"ride:offer:{ride_id}")

    background_tasks.add_task(
        manager.broadcast,
        f"Ride {ride_id} accepted by driver {driver_id}",
    )

    return {"status": "ASSIGNED"}


@router.post("/v1/drivers/{driver_id}/decline/{ride_id}")
def decline_ride(driver_id: str, ride_id: str, background_tasks: BackgroundTasks):
    db = get_db()
    r = get_redis()

    offered_driver = r.get(f"ride:offer:{ride_id}")

    if not offered_driver or offered_driver != driver_id:
        raise HTTPException(status_code=404, detail="Offer expired or invalid")

    r.sadd(f"ride:rejected:{ride_id}", driver_id)
    r.delete(f"ride:offer:{ride_id}")

    new_driver, status = retry_dispatch(db, ride_id)

    if status == "NO_DRIVER":
        background_tasks.add_task(
            manager.broadcast,
            f"Ride {ride_id} has no available drivers",
        )
        return {"status": "NO_DRIVER"}

    background_tasks.add_task(
        manager.broadcast,
        f"Ride {ride_id} re-offered to driver {new_driver}",
    )

    return {
        "status": "REOFFERED",
        "driver_id": new_driver,
    }
