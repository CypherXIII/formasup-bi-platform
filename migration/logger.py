#!/usr/bin/env python3
"""! @file logger.py
@brief Logging configuration for the MariaDB to PostgreSQL migration.
@author Marie Challet
@organization Formasup Auvergne

This module sets up the logging infrastructure for the migration tool,
including a main logger and a dedicated logger for database metrics.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logger(log_file: str) -> logging.Logger:
    """! @brief Configures and returns a logger with formatting and rotation.
    @param log_file Path to the log file.
    @return Configured logger.
    """
    logger = logging.getLogger("migration")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")

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
    db_logger = logging.getLogger("migration.db")
    db_logger.setLevel(logging.INFO)
    db_logger.propagate = False  # avoid duplication to the parent logger

    fmt = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s")

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
