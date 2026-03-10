import logging

from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine

# Import models so metadata is registered
from app.models.ride import Ride  # noqa
from app.models.trip import Trip  # noqa
from app.models.payment import Payment  # noqa
from app.models.driver import Driver  # noqa

logger = logging.getLogger(__name__)


def _apply_migrations():
    """
    Idempotent schema migrations for columns added after initial table creation.
    Uses IF NOT EXISTS so it is safe to run on every startup.
    """
    migrations = [
        "ALTER TABLE rides ADD COLUMN IF NOT EXISTS pickup_lat FLOAT",
        "ALTER TABLE rides ADD COLUMN IF NOT EXISTS pickup_lon FLOAT",
        # v2 — drop coords, estimated fare, cancellation
        "ALTER TABLE rides ADD COLUMN IF NOT EXISTS drop_lat FLOAT",
        "ALTER TABLE rides ADD COLUMN IF NOT EXISTS drop_lon FLOAT",
        "ALTER TABLE rides ADD COLUMN IF NOT EXISTS estimated_fare FLOAT",
        "ALTER TABLE rides ADD COLUMN IF NOT EXISTS cancelled_at TIMESTAMPTZ",
        "ALTER TABLE rides ADD COLUMN IF NOT EXISTS cancellation_fee FLOAT",
        "ALTER TABLE rides ADD COLUMN IF NOT EXISTS cancellation_reason VARCHAR",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                logger.debug("Migration applied | sql=%s", sql)
            except Exception as exc:  # pragma: no cover
                logger.warning("Migration skipped | sql=%s error=%s", sql, exc)
        conn.commit()
    logger.info("Schema migrations complete")


def init_db():
    """
    Create tables if they do not exist, then apply incremental migrations.
    Safe to call multiple times.
    """
    Base.metadata.create_all(bind=engine)
    _apply_migrations()
