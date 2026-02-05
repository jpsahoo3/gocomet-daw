from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Driver(Base):
    __tablename__ = "drivers"

    id = Column(String, primary_key=True)
    is_available = Column(Boolean, default=True)
