from sqlalchemy import Column, String, Boolean
from app.db.base import Base

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String, primary_key=True)
    is_available = Column(Boolean, default=True)
