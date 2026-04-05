"""
Centralised logging configuration for ResolveNow backend.

Provides a factory function `get_logger(name)` that every module imports
to obtain a pre-configured logger.  Log records are written to both a
rotating file and (in development) to the console.

Log files are stored under  logs/  at the project root:
    logs/app.log        – INFO and above (all regular activity)
    logs/error.log      – WARNING and above (problems only)

Each file rotates at 10 MB and keeps the 5 most-recent backups.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
LOG_DIR = Path(__file__).resolve().parents[3] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

APP_LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"

# ---------------------------------------------------------------------------
# Format
# ---------------------------------------------------------------------------
LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ---------------------------------------------------------------------------
# Internal – build the root handler set once
# ---------------------------------------------------------------------------
_configured = False


def _configure_root_logger() -> None:
    global _configured
    if _configured:
        return

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # ── app.log  (INFO+, rotating 10 MB × 5) ──────────────────────────────
    app_handler = RotatingFileHandler(
        APP_LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    root.addHandler(app_handler)

    # ── error.log  (WARNING+, rotating 10 MB × 5) ─────────────────────────
    error_handler = RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    root.addHandler(error_handler)

    # ── console  (DEBUG+ in development, INFO+ otherwise) ─────────────────
    console_handler = logging.StreamHandler()
    app_env = os.getenv("APP_ENV", "development").lower()
    console_handler.setLevel(logging.DEBUG if app_env == "development" else logging.INFO)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # Silence noisy third-party loggers
    for noisy in ("motor", "pymongo", "httpx", "httpcore", "botocore", "boto3", "s3transfer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_logger(name: str) -> logging.Logger:
    """Return a named logger.  Call _configure_root_logger() on first use."""
    _configure_root_logger()
    return logging.getLogger(name)