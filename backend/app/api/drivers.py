import logging

from fastapi import APIRouter
from app.core.schemas import DriverLocationRequest, DriverStatusRequest
from app.services.location_service import update_driver_location
from app.services.matching_service import DRIVER_STATUS_PREFIX, get_redis

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/v1/drivers/{driver_id}/location")
def update_location(driver_id: str, req: DriverLocationRequest):
    update_driver_location(driver_id, req.lat, req.lon)
    logger.info(
        "Driver location updated | driver=%s lat=%.4f lon=%.4f",
        driver_id, req.lat, req.lon,
    )
    return {"status": "OK"}


@router.post("/v1/drivers/{driver_id}/status")
def set_driver_status(driver_id: str, req: DriverStatusRequest):
    """
    Toggle a driver online / offline.
    Offline drivers are skipped by the matching engine — no new rides are
    dispatched to them.  Their geo position is retained; going online again
    makes them immediately eligible for dispatch.
    """
    r = get_redis()
    if req.available:
        r.delete(f"{DRIVER_STATUS_PREFIX}{driver_id}")
        status = "online"
    else:
        r.set(f"{DRIVER_STATUS_PREFIX}{driver_id}", "offline")
        status = "offline"

    logger.info("Driver status changed | driver=%s status=%s", driver_id, status)
    return {"driver_id": driver_id, "status": status}


@router.get("/v1/drivers/{driver_id}/status")
def get_driver_status(driver_id: str):
    """Return the current online/offline status of a driver."""
    r = get_redis()
    raw = r.get(f"{DRIVER_STATUS_PREFIX}{driver_id}")
    status = "offline" if raw == "offline" else "online"
    return {"driver_id": driver_id, "status": status}
