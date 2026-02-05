import uuid
from sqlalchemy import Column, String, DateTime
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

    created_at = Column(DateTime(timezone=True), server_default=func.now())
