from fastapi import APIRouter
from app.core.schemas import DriverLocationRequest
from app.services.location_service import update_driver_location

router = APIRouter()

@router.post("/v1/drivers/{driver_id}/location")
def update_location(driver_id: str, req: DriverLocationRequest):
    update_driver_location(driver_id, req.lat, req.lon)
    return {"status": "OK"}
