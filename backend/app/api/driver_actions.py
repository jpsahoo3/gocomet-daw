import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.ride import Ride
from app.services.matching_service import get_redis
from app.services.dispatch_service import retry_dispatch
from app.websocket.ws import manager

logger = logging.getLogger(__name__)

router = APIRouter()


def get_db() -> Session:
    return SessionLocal()


@router.post("/v1/drivers/{driver_id}/accept/{ride_id}")
def accept_ride(driver_id: str, ride_id: str, background_tasks: BackgroundTasks):
    db = get_db()
    r = get_redis()

    key = f"ride:offer:{ride_id}"
    offered_driver = r.get(key)

    logger.info("Accept attempt | driver=%s ride_id=%s offer_on_record=%s", driver_id, ride_id, offered_driver)

    if offered_driver is None:
        logger.warning("Accept failed: offer expired | driver=%s ride_id=%s", driver_id, ride_id)
        raise HTTPException(status_code=410, detail="Offer expired — please request a new ride")

    if offered_driver != driver_id:
        logger.warning(
            "Accept failed: wrong driver | attempting=%s assigned=%s ride_id=%s",
            driver_id, offered_driver, ride_id,
        )
        raise HTTPException(status_code=403, detail="This offer was not assigned to you")

    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        logger.error("Accept failed: ride missing from DB | ride_id=%s", ride_id)
        raise HTTPException(status_code=404, detail="Ride not found")

    ride.status = "ASSIGNED"
    ride.driver_id = driver_id
    db.commit()
    r.delete(key)

    logger.info("Ride accepted | ride_id=%s driver=%s", ride_id, driver_id)
    background_tasks.add_task(manager.broadcast, f"Ride {ride_id} accepted by driver {driver_id}")

    return {"status": "ASSIGNED"}


@router.post("/v1/drivers/{driver_id}/decline/{ride_id}")
def decline_ride(driver_id: str, ride_id: str, background_tasks: BackgroundTasks):
    db = get_db()
    r = get_redis()

    offered_driver = r.get(f"ride:offer:{ride_id}")

    logger.info("Decline attempt | driver=%s ride_id=%s offer_on_record=%s", driver_id, ride_id, offered_driver)

    if offered_driver is None:
        logger.warning("Decline failed: offer expired | driver=%s ride_id=%s", driver_id, ride_id)
        raise HTTPException(status_code=410, detail="Offer expired — please request a new ride")

    if offered_driver != driver_id:
        logger.warning(
            "Decline failed: wrong driver | attempting=%s assigned=%s ride_id=%s",
            driver_id, offered_driver, ride_id,
        )
        raise HTTPException(status_code=403, detail="This offer was not assigned to you")

    r.sadd(f"ride:rejected:{ride_id}", driver_id)
    r.delete(f"ride:offer:{ride_id}")
    logger.info("Ride declined | ride_id=%s driver=%s — re-dispatching", ride_id, driver_id)

    new_driver, status = retry_dispatch(db, ride_id)

    if status == "NO_DRIVER":
        logger.warning("Re-dispatch exhausted | ride_id=%s", ride_id)
        background_tasks.add_task(manager.broadcast, f"Ride {ride_id} — no drivers available after decline")
        return {"status": "NO_DRIVER"}

    logger.info("Re-dispatch success | ride_id=%s new_driver=%s", ride_id, new_driver)
    background_tasks.add_task(manager.broadcast, f"Ride {ride_id} re-offered to driver {new_driver}")

    return {"status": "REOFFERED", "driver_id": new_driver}
