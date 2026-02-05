from pydantic import BaseModel

class RideCreateRequest(BaseModel):
    pickup_lat: float
    pickup_lon: float

class DriverLocationRequest(BaseModel):
    lat: float
    lon: float
