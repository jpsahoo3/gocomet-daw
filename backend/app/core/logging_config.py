"""
Centralised logging configuration.

Usage in any module:
    import logging
    logger = logging.getLogger(__name__)

Features:
- Coloured console output (WARNING+ only — keeps terminal clean)
- Daily-rotating file: logs/backend.log  (INFO+, plain text, 7-day retention)
- Daily-rotating file: logs/frontend.log (browser-forwarded errors via POST /v1/log)
- Log level controlled by LOG_LEVEL env var (default INFO)
- Rotation happens at midnight; backup suffix is YYYY-MM-DD
"""

import logging
import logging.config
import logging.handlers
import os
from pathlib import Path

LOG_LEVEL       = os.getenv("LOG_LEVEL",       "INFO").upper()
LOG_DIR         = Path(os.getenv("LOG_DIR",    "logs"))
LOG_RETAIN_DAYS = int(os.getenv("LOG_RETAIN_DAYS", "7"))

BACKEND_LOG  = LOG_DIR / "backend.log"
FRONTEND_LOG = LOG_DIR / "frontend.log"

# ---------------------------------------------------------------------------
# ANSI colour codes (console only)
# ---------------------------------------------------------------------------
_RESET = "\x1b[0m"
_LEVEL_COLOURS = {
    "DEBUG":    "\x1b[90m",    # dark grey
    "INFO":     "\x1b[36m",    # cyan
    "WARNING":  "\x1b[33m",    # yellow
    "ERROR":    "\x1b[31m",    # red
    "CRITICAL": "\x1b[1;31m",  # bold red
}

_PLAIN_FMT   = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
_DATEFMT     = "%Y-%m-%d %H:%M:%S"


class ColourFormatter(logging.Formatter):
    """Console formatter that colour-codes each log level name."""

    _fmt = "%(asctime)s | {c}%(levelname)-8s{r} | %(name)s:%(lineno)d | %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        colour = _LEVEL_COLOURS.get(record.levelname, "")
        fmt = self._fmt.format(c=colour, r=_RESET)
        return logging.Formatter(fmt, datefmt=_DATEFMT).format(record)


# ---------------------------------------------------------------------------
# Build dictConfig
# ---------------------------------------------------------------------------

def _timed_handler(filename: Path) -> dict:
    """Returns a dictConfig handler entry for a daily-rotating file."""
    return {
        "class":       "logging.handlers.TimedRotatingFileHandler",
        "filename":    str(filename),
        "when":        "midnight",
        "interval":    1,
        "backupCount": LOG_RETAIN_DAYS,
        "encoding":    "utf-8",
        "formatter":   "plain",
        "delay":       False,
    }


def _build_config() -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "format":  _PLAIN_FMT,
                "datefmt": _DATEFMT,
            },
        },
        "handlers": {
            # Console: WARNING+ only (quiet terminal)
            "console": {
                "class":     "logging.StreamHandler",
                "stream":    "ext://sys.stderr",
                "level":     "WARNING",
                "formatter": "plain",   # replaced with ColourFormatter after dictConfig
            },
            # Backend app log: daily rotation
            "backend_file": {
                **_timed_handler(BACKEND_LOG),
                "level": "INFO",
            },
            # Frontend log: receives browser-forwarded errors
            "frontend_file": {
                **_timed_handler(FRONTEND_LOG),
                "level": "DEBUG",
            },
        },
        "loggers": {
            # Main application logger
            "app": {
                "level":     LOG_LEVEL,
                "handlers":  ["console", "backend_file"],
                "propagate": False,
            },
            # Browser-forwarded errors — file only, no console noise
            "app.frontend": {
                "level":     "DEBUG",
                "handlers":  ["frontend_file"],
                "propagate": False,
            },
            # Silence noisy uvicorn access log (200 OK spam)
            "uvicorn.access": {
                "level":     "WARNING",
                "handlers":  ["backend_file"],
                "propagate": False,
            },
            # Uvicorn startup / error messages
            "uvicorn.error": {
                "level":     "INFO",
                "handlers":  ["console", "backend_file"],
                "propagate": False,
            },
        },
        "root": {
            "level":    "WARNING",
            "handlers": ["console", "backend_file"],
        },
    }


def setup_logging() -> None:
    """
    Initialise logging. Call once at startup (main.py).
    Console: WARNING+ with colour coding.
    logs/backend.log: INFO+ daily rotation (7 days).
    logs/frontend.log: browser errors daily rotation (7 days).
    """
    cfg = _build_config()
    logging.config.dictConfig(cfg)

    # Attach ColourFormatter to every StreamHandler (but not FileHandlers).
    colour_fmt = ColourFormatter()
    for name in ("app", "uvicorn.access", "uvicorn.error", ""):
        lgr = logging.getLogger(name)
        for handler in lgr.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setFormatter(colour_fmt)

    logging.getLogger("app").info(
        "Logging initialised | level=%s backend=%s frontend=%s",
        LOG_LEVEL, BACKEND_LOG, FRONTEND_LOG,
    )
