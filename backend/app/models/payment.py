import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(String, nullable=False, index=True)

    ride_id = Column(UUID(as_uuid=True), ForeignKey("rides.id"), nullable=False)

    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="PENDING")
    provider_ref = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
