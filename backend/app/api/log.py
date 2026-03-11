"""
POST /v1/log — receives browser-forwarded log entries and writes them to
logs/frontend.log via the app.frontend logger.
"""

import logging
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
logger = logging.getLogger("app.frontend")

_LEVEL_MAP = {
    "debug":    logger.debug,
    "info":     logger.info,
    "warn":     logger.warning,
    "warning":  logger.warning,
    "error":    logger.error,
    "critical": logger.critical,
}


class FrontendLogEntry(BaseModel):
    level:   str             = "error"
    message: str
    context: Optional[str]  = None   # e.g. component name
    stack:   Optional[str]  = None   # JS stack trace


@router.post("/v1/log", status_code=204)
def ingest_frontend_log(entry: FrontendLogEntry):
    log_fn = _LEVEL_MAP.get(entry.level.lower(), logger.error)
    extra = ""
    if entry.context:
        extra += f" | ctx={entry.context}"
    if entry.stack:
        extra += f"\n{entry.stack}"
    log_fn("[browser] %s%s", entry.message, extra)
