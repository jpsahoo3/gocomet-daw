import uuid
from sqlalchemy import Column, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Trip(Base):
    __tablename__ = "trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(String, nullable=False, index=True)

    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=False)

    status = Column(String, nullable=False, default="ONGOING")

    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)

    distance_km = Column(Float, nullable=True)
    fare = Column(Float, nullable=True)
