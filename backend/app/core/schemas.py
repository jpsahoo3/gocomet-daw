from pydantic import BaseModel
from typing import Optional


class RideCreateRequest(BaseModel):
    pickup_lat: float
    pickup_lon: float
    drop_lat: Optional[float] = None
    drop_lon: Optional[float] = None


class DriverLocationRequest(BaseModel):
    lat: float
    lon: float


class DriverStatusRequest(BaseModel):
    available: bool


class FareEstimateRequest(BaseModel):
    pickup_lat: float
    pickup_lon: float
    drop_lat: float
    drop_lon: float
