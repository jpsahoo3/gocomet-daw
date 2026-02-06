import uuid
import json

from fastapi import APIRouter, Header, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.schemas import RideCreateRequest
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.request_context import get_request_context
from app.services.matching_service import find_nearest_driver, get_redis
from app.websocket.ws import manager
import logging

from app.db.deps import get_db
from app.models.ride import Ride

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

    if idempotency_key:
        cached = check_idempotency(idempotency_key)
        if cached:
            return json.loads(cached)

    ride_id = uuid.uuid4()

    ride = Ride(
        id=ride_id,
        tenant_id=tenant,
        rider_id="rider-1",
        status="REQUESTED",
    )
    db.add(ride)
    db.commit()

    driver = find_nearest_driver(region, tenant, req.pickup_lat, req.pickup_lon)

    if not driver:
        response = {"ride_id": str(ride_id), "status": "NO_DRIVER"}
    else:
        ride.status = "OFFERED"
        db.commit()

        r = get_redis()
        key = f"ride:offer:{str(ride_id)}"
        r.setex(key, OFFER_TTL_SECONDS, driver)
        logger = logging.getLogger(__name__)
        try:
            logger.info("Set ride offer: %s -> %s", key, driver)
        except Exception:
            pass
        # fallback print to ensure visibility in simple development setups
        try:
            print(f"Set ride offer: {key} -> {driver}")
        except Exception:
            pass

        response = {
            "ride_id": str(ride_id),
            "status": "OFFERED",
            "driver_id": driver,
        }

        background_tasks.add_task(
            manager.broadcast,
            f"[{tenant}/{region}] Ride {ride_id} offered to driver {driver}",
        )

    if idempotency_key:
        save_idempotency(idempotency_key, json.dumps(response))

    return response
