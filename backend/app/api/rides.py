import logging
import math
import uuid
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Header, BackgroundTasks, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.schemas import RideCreateRequest
from app.core.idempotency import check_idempotency, save_idempotency
from app.core.request_context import get_request_context
from app.services.matching_service import find_nearest_driver, get_redis
from app.services.fare_service import BASE_FARE, DISTANCE_RATE
from app.services.surge_service import get_surge_multiplier
from app.websocket.ws import manager
from app.db.deps import get_db
from app.models.ride import Ride

logger = logging.getLogger(__name__)

router = APIRouter()

OFFER_TTL_SECONDS = 60
CANCELLATION_FEE_ASSIGNED = 50.0   # flat fee when driver was already assigned


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return round(2.0 * R * math.asin(math.sqrt(a)), 2)


def _estimate(pickup_lat, pickup_lon, drop_lat, drop_lon) -> tuple[float, float]:
    """Returns (distance_km, estimated_fare)."""
    dist = _haversine_km(pickup_lat, pickup_lon, drop_lat, drop_lon)
    surge = get_surge_multiplier("default")
    fare = round((BASE_FARE + DISTANCE_RATE * dist) * surge, 2)
    return dist, fare


# ---------------------------------------------------------------------------
# Fare estimate — no DB write, pure calculation
# ---------------------------------------------------------------------------

@router.get("/v1/rides/estimate")
def estimate_fare(
    pickup_lat: float = Query(...),
    pickup_lon: float = Query(...),
    drop_lat: float = Query(...),
    drop_lon: float = Query(...),
    ctx: dict = Depends(get_request_context),
):
    distance_km, estimated = _estimate(pickup_lat, pickup_lon, drop_lat, drop_lon)
    surge = get_surge_multiplier("default")
    dist_charge = round(DISTANCE_RATE * distance_km, 2)

    logger.info(
        "Fare estimate | distance_km=%.2f surge=%.2f estimated=%.2f",
        distance_km, surge, estimated,
    )

    return {
        "distance_km": distance_km,
        "estimated_fare": estimated,
        "surge_multiplier": surge,
        "breakdown": {
            "base_fare": BASE_FARE,
            "distance_charge": dist_charge,
            "surge_multiplier": surge,
        },
    }


# ---------------------------------------------------------------------------
# Create ride
# ---------------------------------------------------------------------------

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
        "Ride request received | tenant=%s region=%s lat=%.4f lon=%.4f "
        "drop_lat=%s drop_lon=%s idempotency_key=%s",
        tenant, region, req.pickup_lat, req.pickup_lon,
        req.drop_lat, req.drop_lon, idempotency_key,
    )

    if idempotency_key:
        cached = check_idempotency(idempotency_key)
        if cached:
            logger.info("Idempotency hit | key=%s", idempotency_key)
            return json.loads(cached)

    ride_id = uuid.uuid4()

    # Pre-compute estimated fare when drop coords are supplied
    estimated_fare = None
    if req.drop_lat is not None and req.drop_lon is not None:
        _, estimated_fare = _estimate(req.pickup_lat, req.pickup_lon, req.drop_lat, req.drop_lon)

    ride = Ride(
        id=ride_id,
        tenant_id=tenant,
        rider_id="rider-1",
        status="REQUESTED",
        pickup_lat=req.pickup_lat,
        pickup_lon=req.pickup_lon,
        drop_lat=req.drop_lat,
        drop_lon=req.drop_lon,
        estimated_fare=estimated_fare,
    )
    db.add(ride)
    db.commit()
    logger.debug("Ride persisted | ride_id=%s estimated_fare=%s", ride_id, estimated_fare)

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
        r.setex(f"ride:offer:{str(ride_id)}", OFFER_TTL_SECONDS, driver)

        logger.info(
            "Ride offered | ride_id=%s driver=%s ttl=%ds estimated_fare=%s",
            ride_id, driver, OFFER_TTL_SECONDS, estimated_fare,
        )

        response = {
            "ride_id": str(ride_id),
            "status": "OFFERED",
            "driver_id": driver,
            "estimated_fare": estimated_fare,
        }

        background_tasks.add_task(
            manager.broadcast,
            f"[{tenant}/{region}] Ride {ride_id} offered to {driver}",
        )

    if idempotency_key:
        save_idempotency(idempotency_key, json.dumps(response))

    return response


# ---------------------------------------------------------------------------
# Ride status — polling fallback when WebSocket is unavailable
# ---------------------------------------------------------------------------

@router.get("/v1/rides/{ride_id}")
def get_ride_status(ride_id: str, db: Session = Depends(get_db)):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    return {
        "ride_id": str(ride.id),
        "status": ride.status,
        "driver_id": ride.driver_id,
        "pickup_lat": ride.pickup_lat,
        "pickup_lon": ride.pickup_lon,
        "drop_lat": ride.drop_lat,
        "drop_lon": ride.drop_lon,
        "estimated_fare": ride.estimated_fare,
        "cancellation_fee": ride.cancellation_fee,
        "cancellation_reason": ride.cancellation_reason,
        "created_at": ride.created_at.isoformat() if ride.created_at else None,
    }


# ---------------------------------------------------------------------------
# Cancel ride
# ---------------------------------------------------------------------------

_CANCELLABLE = {"REQUESTED", "OFFERED", "ASSIGNED"}


@router.post("/v1/rides/{ride_id}/cancel")
def cancel_ride(
    ride_id: str,
    background_tasks: BackgroundTasks,
    reason: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    ride = db.query(Ride).filter(Ride.id == ride_id).first()
    if not ride:
        raise HTTPException(status_code=404, detail="Ride not found")

    if ride.status not in _CANCELLABLE:
        logger.warning("Cancel rejected | ride_id=%s status=%s", ride_id, ride.status)
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot cancel a ride in status '{ride.status}'. "
                "Only REQUESTED, OFFERED, or ASSIGNED rides can be cancelled."
            ),
        )

    r = get_redis()
    cancellation_fee = 0.0

    # Release driver lock and charge cancellation fee when driver was assigned
    if ride.status == "ASSIGNED" and ride.driver_id:
        r.delete(f"driver:lock:{ride.driver_id}")
        cancellation_fee = CANCELLATION_FEE_ASSIGNED
        logger.info(
            "Cancel: releasing driver lock | driver=%s ride_id=%s fee=%.2f",
            ride.driver_id, ride_id, cancellation_fee,
        )

    # Purge Redis keys so no driver can accept a stale offer
    r.delete(f"ride:offer:{ride_id}")
    r.delete(f"ride:rejected:{ride_id}")

    ride.status = "CANCELLED"
    ride.cancelled_at = datetime.now(timezone.utc)
    ride.cancellation_fee = cancellation_fee
    ride.cancellation_reason = reason
    db.commit()

    logger.info(
        "Ride cancelled | ride_id=%s fee=%.2f reason=%s",
        ride_id, cancellation_fee, reason,
    )

    background_tasks.add_task(
        manager.broadcast,
        f"Ride {ride_id} cancelled by rider (fee: ₹{cancellation_fee})",
    )

    return {
        "status": "CANCELLED",
        "cancellation_fee": cancellation_fee,
        "message": (
            "Ride cancelled successfully."
            if cancellation_fee == 0
            else f"A cancellation fee of ₹{cancellation_fee} will be charged."
        ),
    }
