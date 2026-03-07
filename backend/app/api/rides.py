import logging
import uuid
import json

from fastapi import APIRouter, Header, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.schemas import RideCreateRequest
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.request_context import get_request_context
from app.services.matching_service import find_nearest_driver, get_redis
from app.websocket.ws import manager
from app.db.deps import get_db
from app.models.ride import Ride

logger = logging.getLogger(__name__)

router = APIRouter()

OFFER_TTL_SECONDS = 60


@router.post("/v1/rides")
def create_ride(
    req: RideCreateRequest,
    background_tasks: BackgroundTasks,
    ctx: dict = Depends(get_request_context),
    db: Session = Depends(get_db),
    idempotency_key: str | None = Header(default=None),
):
    tenant = ctx["tenant_id"]
    region = ctx["region"]

    logger.info(
        "Ride request received | tenant=%s region=%s lat=%.4f lon=%.4f idempotency_key=%s",
        tenant, region, req.pickup_lat, req.pickup_lon, idempotency_key,
    )

    if idempotency_key:
        cached = check_idempotency(idempotency_key)
        if cached:
            logger.info("Idempotency hit | key=%s", idempotency_key)
            return json.loads(cached)

    ride_id = uuid.uuid4()

    ride = Ride(
        id=ride_id,
        tenant_id=tenant,
        rider_id="rider-1",
        status="REQUESTED",
        pickup_lat=req.pickup_lat,
        pickup_lon=req.pickup_lon,
    )
    db.add(ride)
    db.commit()
    logger.debug("Ride persisted | ride_id=%s status=REQUESTED", ride_id)

    driver = find_nearest_driver(region, tenant, req.pickup_lat, req.pickup_lon)

    if not driver:
        logger.warning(
            "No driver found | ride_id=%s lat=%.4f lon=%.4f",
            ride_id, req.pickup_lat, req.pickup_lon,
        )
        response = {"ride_id": str(ride_id), "status": "NO_DRIVER"}
    else:
        ride.status = "OFFERED"
        db.commit()

        r = get_redis()
        key = f"ride:offer:{str(ride_id)}"
        r.setex(key, OFFER_TTL_SECONDS, driver)

        logger.info(
            "Ride offered | ride_id=%s driver=%s ttl=%ds",
            ride_id, driver, OFFER_TTL_SECONDS,
        )

        response = {
            "ride_id": str(ride_id),
            "status": "OFFERED",
            "driver_id": driver,
        }

        background_tasks.add_task(
            manager.broadcast,
            f"[{tenant}/{region}] Ride {ride_id} offered to {driver}",
        )

    if idempotency_key:
        save_idempotency(idempotency_key, json.dumps(response))

    return response
