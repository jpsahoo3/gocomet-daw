"""
Health check endpoint.

Returns the status of all critical dependencies:
  - Database (PostgreSQL)
  - Redis (real or FallbackRedis)

Useful for:
  - Load-balancer readiness probes
  - Monitoring dashboards
  - Quick sanity check during local development
"""

import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.core.redis_client import get_redis, FallbackRedis
from app.db.session import engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health_check():
    result = {
        "status": "ok",
        "database": "unknown",
        "redis": "unknown",
        "redis_mode": "unknown",
    }

    # ---- Database probe ----
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["database"] = "connected"
    except Exception as exc:
        result["database"] = f"error: {exc}"
        result["status"] = "degraded"
        logger.error("Health check: DB probe failed | error=%s", exc)

    # ---- Redis probe ----
    try:
        r = get_redis()
        r.ping()
        if isinstance(r, FallbackRedis):
            result["redis"] = "fallback (in-memory)"
            result["redis_mode"] = "fallback"
        else:
            result["redis"] = "connected"
            result["redis_mode"] = "redis"
    except Exception as exc:
        result["redis"] = f"error: {exc}"
        result["status"] = "degraded"
        logger.error("Health check: Redis probe failed | error=%s", exc)

    logger.debug("Health check | %s", result)
    return result
