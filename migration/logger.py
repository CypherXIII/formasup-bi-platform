#!/usr/bin/env python3
"""! @file logger.py
@brief Logging configuration for the MariaDB to PostgreSQL migration.
@author Marie Challet
@organization Formasup Auvergne
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Shared format: timestamp | level | message (concise, no pid/name clutter)
_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
_LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def _resolve_log_level(env_value: str | None, default: int) -> int:
    """Resolve a logging level name (e.g., DEBUG) to its numeric value."""
    if not env_value:
        return default
    level = logging.getLevelName(env_value.upper())
    return level if isinstance(level, int) else default


def setup_logger(log_file: str) -> logging.Logger:
    """! @brief Configures the main migration logger with file rotation.
    @param log_file Path to the log file.
    @return Configured logger.
    """
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("migration")
    logger.setLevel(_resolve_log_level(os.getenv("MIGRATION_LOG_LEVEL"), logging.INFO))

    if not logger.handlers:
        fmt = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)
        file_h = RotatingFileHandler(
            log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_h.setFormatter(fmt)
        console_h = logging.StreamHandler(sys.stdout)
        console_h.setFormatter(fmt)
        logger.addHandler(file_h)
        logger.addHandler(console_h)

    return logger


def setup_db_logger(metrics_log_file: str) -> logging.Logger:
    """! @brief Configures a dedicated logger for DB metrics (file only).
    @param metrics_log_file Path to the database metrics log file.
    @return Configured database logger.
    """
    Path(metrics_log_file).parent.mkdir(parents=True, exist_ok=True)

    db_logger = logging.getLogger("migration.db")
    db_logger.setLevel(_resolve_log_level(os.getenv("MIGRATION_LOG_LEVEL"), logging.INFO))
    db_logger.propagate = False

    if not db_logger.handlers:
        fmt = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FORMAT)
        file_h = RotatingFileHandler(
            metrics_log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        )
        file_h.setFormatter(fmt)
        db_logger.addHandler(file_h)

    return db_logger
