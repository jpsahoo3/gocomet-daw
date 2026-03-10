import uuid
from sqlalchemy import Column, Float, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Ride(Base):
    __tablename__ = "rides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(String, nullable=False, index=True)

    rider_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    driver_id = Column(String, nullable=True)

    # Pickup coordinates — stored so re-dispatch uses the actual pickup point
    pickup_lat = Column(Float, nullable=True)
    pickup_lon = Column(Float, nullable=True)

    # Drop-off coordinates — used for actual distance / fare calculation
    drop_lat = Column(Float, nullable=True)
    drop_lon = Column(Float, nullable=True)

    # Pre-computed estimate shown to rider before booking
    estimated_fare = Column(Float, nullable=True)

    # Cancellation metadata
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancellation_fee = Column(Float, nullable=True)
    cancellation_reason = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
