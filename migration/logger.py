#!/usr/bin/env python3
"""! @file logger.py
@brief Logging configuration for the MariaDB to PostgreSQL migration.
@author Marie Challet
@organization Formasup Auvergne

This module sets up the logging infrastructure for the migration tool,
including a main logger and a dedicated logger for database metrics.
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def _resolve_log_level(env_value: str | None, default: int) -> int:
    """Resolve a logging level name (e.g., "DEBUG") to its numeric value."""
    if not env_value:
        return default

    level = logging.getLevelName(env_value.upper())
    return level if isinstance(level, int) else default


def setup_logger(log_file: str) -> logging.Logger:
    """! @brief Configures and returns a logger with formatting and rotation.
    @param log_file Path to the log file.
    @return Configured logger.
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("migration")
    log_level = _resolve_log_level(os.getenv("MIGRATION_LOG_LEVEL"), logging.INFO)
    logger.setLevel(log_level)
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | pid=%(process)d | %(name)s | %(message)s"
    )

    # Avoid duplicates if the configuration is called multiple times
    if not logger.handlers:
        handlers = [
            RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
            ),
            logging.StreamHandler(sys.stdout),
        ]
        for h in handlers:
            h.setFormatter(fmt)
            logger.addHandler(h)
    return logger


def setup_db_logger(metrics_log_file: str) -> logging.Logger:
    """! @brief Configures a child logger dedicated to MariaDB SQL metrics.

    - Logger name: "migration.db"
    - Only writes to a dedicated file (no propagation to the console)
    @param metrics_log_file Path to the database metrics log file.
    @return Configured database logger.
    """
    # Ensure log directory exists
    log_path = Path(metrics_log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    db_logger = logging.getLogger("migration.db")
    log_level = _resolve_log_level(os.getenv("MIGRATION_LOG_LEVEL"), logging.INFO)
    db_logger.setLevel(log_level)
    db_logger.propagate = False  # avoid duplication to the parent logger

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | pid=%(process)d | %(name)s | %(message)s"
    )

    # Avoid adding multiple handlers if called multiple times
    if not db_logger.handlers:
        file_h = RotatingFileHandler(
            metrics_log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_h.setFormatter(fmt)
        db_logger.addHandler(file_h)

    return db_logger
