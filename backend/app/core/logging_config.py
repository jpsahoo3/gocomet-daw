"""
Centralised logging configuration.

Usage in any module:
    import logging
    logger = logging.getLogger(__name__)

Features:
- Coloured console output by level (DEBUG grey, INFO cyan, WARNING yellow,
  ERROR red, CRITICAL bold red)
- Rotating file handler -> logs/app.log (plain text, no ANSI codes)
- Log level controlled by LOG_LEVEL env var (default INFO)
"""

import logging
import logging.config
import logging.handlers
import os
from pathlib import Path

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_FILE = LOG_DIR / "app.log"

# ---------------------------------------------------------------------------
# ANSI colour codes
# ---------------------------------------------------------------------------
_RESET = "\x1b[0m"
_LEVEL_COLOURS = {
    "DEBUG":    "\x1b[90m",       # dark grey
    "INFO":     "\x1b[36m",       # cyan
    "WARNING":  "\x1b[33m",       # yellow
    "ERROR":    "\x1b[31m",       # red
    "CRITICAL": "\x1b[1;31m",     # bold red
}


class ColourFormatter(logging.Formatter):
    """Console formatter that colour-codes each log level name."""

    _fmt = "%(asctime)s | {colour}%(levelname)-8s{reset} | %(name)s:%(lineno)d | %(message)s"
    _datefmt = "%Y-%m-%d %H:%M:%S"

    def format(self, record: logging.LogRecord) -> str:
        colour = _LEVEL_COLOURS.get(record.levelname, "")
        fmt = self._fmt.format(colour=colour, reset=_RESET)
        return logging.Formatter(fmt, datefmt=self._datefmt).format(record)


# Plain formatter for the log file (no ANSI codes)
_PLAIN_FMT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
_PLAIN_DATEFMT = "%Y-%m-%d %H:%M:%S"


def _build_config() -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "plain": {
                "format": _PLAIN_FMT,
                "datefmt": _PLAIN_DATEFMT,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "plain",   # overridden with ColourFormatter below
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": str(LOG_FILE),
                "maxBytes": 10 * 1024 * 1024,   # 10 MB per file
                "backupCount": 5,
                "encoding": "utf-8",
                "formatter": "plain",
            },
        },
        "loggers": {
            "app": {
                "level": LOG_LEVEL,
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "WARNING",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
        "root": {
            "level": "WARNING",
            "handlers": ["console", "file"],
        },
    }


def setup_logging() -> None:
    """
    Initialise logging. Call once at startup (main.py).
    Console output is colour-coded by level; file output is plain text.
    """
    cfg = _build_config()
    logging.config.dictConfig(cfg)

    # Replace the plain formatter on every StreamHandler (console) with the
    # colour-aware one.  FileHandlers keep the plain formatter.
    colour_fmt = ColourFormatter()
    for logger_name in ("app", "uvicorn.access", "uvicorn.error", ""):
        lgr = logging.getLogger(logger_name)
        for handler in lgr.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setFormatter(colour_fmt)

    logging.getLogger("app").info(
        "Logging initialised | level=%s log_file=%s", LOG_LEVEL, LOG_FILE
    )
