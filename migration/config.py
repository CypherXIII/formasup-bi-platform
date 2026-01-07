#!/usr/bin/env python3
"""! @file config.py
@brief Configuration for the MariaDB to PostgreSQL migration.
@author Marie Challet
@organization Formasup Auvergne

This module defines the configuration settings for the migration tool,
loading values from environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()


@dataclass(frozen=True)
class Config:
    """! @brief Holds all configuration parameters for the migration.
    
    This class loads settings from environment variables and provides a single
    point of access for all configuration values.
    """
    mariadb_host: str = os.getenv("MARIA_HOST", "")
    mariadb_user: str = os.getenv("MARIA_USER", "")
    mariadb_password: str = os.getenv("MARIA_PASSWORD", "")
    mariadb_db: str = os.getenv("MARIA_DB", "")
    mariadb_port: int = int(os.getenv("MARIA_PORT", "3306"))
    pg_host: str = os.getenv("PG_HOST", "")
    pg_user: str = os.getenv("PG_USER", "")
    pg_password: str = os.getenv("PG_PASSWORD", "")
    pg_db: str = os.getenv("PG_DB", "")
    pg_schema: str = os.getenv("PG_SCHEMA", "staging")
    batch_size: int = int(os.getenv("BATCH_SIZE", "500"))
    log_file: str = os.getenv("MIGRATION_LOG", "migration.log")
    temp_schema: str = os.getenv("PG_TEMP_SCHEMA", "temp_staging")

    # DB Metrics (MariaDB)
    enable_db_metrics: bool = os.getenv("ENABLE_DB_METRICS", "true").lower() == "true"
    db_metrics_slow_ms: int = int(os.getenv("DB_METRICS_SLOW_MS", "200"))
    db_metrics_log_file: str = os.getenv("DB_METRICS_LOG", "db_metrics.log")

    requests_per_second: int = int(os.getenv("API_REQUESTS_PER_SECOND", "7"))
    api_enabled: bool = os.getenv("ENABLE_API_ENRICHMENT", "false").lower() == "true"

    # OPCO enrichment
    opco_enabled: bool = os.getenv("ENABLE_OPCO_ENRICHMENT", "false").lower() == "true"
    opco_resource_id: str = os.getenv(
        "OPCO_RESOURCE_ID", "59533036-3c0b-45e6-972c-e967c0a1be17"
    )

    def validate(self) -> None:
        """! @brief Validates that all required environment variables are set.
        @raises EnvironmentError If any required environment variables are missing.
        """
        # Fields that can be empty or False without issue
        optional_fields = {
            "batch_size", "log_file", "temp_schema",
            "enable_db_metrics", "db_metrics_slow_ms", "db_metrics_log_file",
            "requests_per_second", "api_enabled",
            "opco_enabled", "opco_resource_id"
        }
        missing = [
            field
            for field, val in self.__dict__.items()
            if val == "" and field not in optional_fields
        ]
        if missing:
            raise EnvironmentError(
                f"Missing environment variables: {', '.join(missing)}"
            )


# Table structure
CONFLICT_KEYS = {
    "cpne": "id",
    "cerfa_param": "id",
    "degree_level": "id",
    "degree": "id",
    "company": "id",
    "city": "code",
    "institution": "id",
    "component": "id",
    "billing": "id",
    "billing_payment": "id",
    "sector": "id",
    "training": "id",
    "training_course": "id",
    "training_group": "id",
    "training_option": "id",
    "apprentice": "id",
    "opco_address": "id",
    "registration": "id",
    "deadline": "id",
    "billing_line": "id",
}

TABLE_ORDER = [
    "cpne",
    "cerfa_param",
    "degree_level",
    "degree",
    "company",
    "city",
    "institution",
    "component",
    "billing",
    "billing_payment",
    "sector",
    "training",
    "training_course",
    "training_group",
    "training_option",
    "apprentice",
    "opco_address",
    "registration",
    "deadline",
    "billing_line",
]
