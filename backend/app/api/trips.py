from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.trip_service import start_trip, pause_trip, resume_trip, end_trip
from app.websocket.ws import manager

router = APIRouter()


@router.post("/v1/trips/{ride_id}/start")
def api_start_trip(
    ride_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        trip = start_trip(db, ride_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(
        manager.broadcast,
        f"Trip started for ride {ride_id}",
    )

    return {"status": "ONGOING", "trip_id": str(trip.id)}


@router.post("/v1/trips/{ride_id}/pause")
def api_pause_trip(
    ride_id: str,
    db: Session = Depends(get_db),
):
    try:
        trip = pause_trip(db, ride_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": trip.status}


@router.post("/v1/trips/{ride_id}/resume")
def api_resume_trip(
    ride_id: str,
    db: Session = Depends(get_db),
):
    try:
        trip = resume_trip(db, ride_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"status": trip.status}


@router.post("/v1/trips/{ride_id}/end")
def api_end_trip(
    ride_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    try:
        trip = end_trip(db, ride_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(
        manager.broadcast,
        f"Trip completed for ride {ride_id}, fare={trip.fare}",
    )

    return {
        "status": "COMPLETED",
        "fare": trip.fare,
        "distance_km": trip.distance_km,
    }
