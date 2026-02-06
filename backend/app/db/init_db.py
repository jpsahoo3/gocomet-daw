from app.db.base import Base
from app.db.session import engine

# Import models so metadata is registered
from app.models.ride import Ride  # noqa
from app.models.trip import Trip  # noqa
from app.models.payment import Payment  # noqa
from app.models.driver import Driver  # noqa


def init_db():
    """
    Create tables if they do not exist.
    Safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)
