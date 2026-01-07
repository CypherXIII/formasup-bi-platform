#!/usr/bin/env python3
"""! @file temp_tables.py
@brief Management of temporary tables for the MariaDB to PostgreSQL migration.
@author Marie Challet
@organization Formasup Auvergne

This module provides functions for creating and deleting the temporary schema
and tables used during the migration process.
"""

import logging

import psycopg2

from config import Config
from database import transaction


def create_temp_schema(conn_pg: psycopg2.extensions.connection, cfg: Config) -> None:
    """! @brief Creates a temporary schema in PostgreSQL if it does not already exist.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the temporary schema name.
    @raises Exception In case of an error during schema creation.
    """
    logger = logging.getLogger("migration")
    logger.info("Creating temporary schema %s...", cfg.temp_schema)
    try:
        with transaction(conn_pg) as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {cfg.temp_schema}")
            logger.info("Schema %s created successfully", cfg.temp_schema)
    except Exception as e:
        logger.exception("Error during temporary schema creation: %s", e)
        raise


def create_temp_tables(
    conn_pg: psycopg2.extensions.connection, cfg: Config, tables: list[str]
) -> None:
    """! @brief Creates copies of tables in the temporary schema from the tables in the main schema.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the schema names.
    @param tables List of table names to create in the temporary schema.
    @note - First deletes the tables if they already exist.
          - Creates tables with the same structure as the original tables.
          - Disables triggers to facilitate data import.
    @raises Exception In case of an error during table creation.
    """
    logger = logging.getLogger("migration")
    logger.info("Creating temporary tables...")

    try:
        with transaction(conn_pg) as cur:
            for table in tables:
                logger.info("Creating %s.%s...", cfg.temp_schema, table)
                # Delete the temporary table if it already exists
                cur.execute(f"DROP TABLE IF EXISTS {cfg.temp_schema}.{table} CASCADE")

                # Create the temporary table with the same structure as the main table
                cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {cfg.temp_schema}.{table} (
                    LIKE {cfg.pg_schema}.{table} INCLUDING ALL
                )
                """)

                # Disable constraints to allow import operations
                cur.execute(
                    f"ALTER TABLE {cfg.temp_schema}.{table} DISABLE TRIGGER ALL"
                )

                logger.info("Table %s.%s created successfully", cfg.temp_schema, table)

        logger.info("All temporary tables have been created")
    except Exception as e:
        logger.exception("Error during temporary table creation: %s", e)
        raise


def drop_temp_schema(conn_pg: psycopg2.extensions.connection, cfg: Config) -> None:
    """! @brief Deletes the temporary schema and all its tables.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing the temporary schema name.
    """
    logger = logging.getLogger("migration")
    logger.info("Deleting temporary schema %s...", cfg.temp_schema)

    try:
        with transaction(conn_pg) as cur:
            cur.execute(f"DROP SCHEMA IF EXISTS {cfg.temp_schema} CASCADE")
            logger.info("Schema %s deleted successfully", cfg.temp_schema)
    except Exception as e:
        logger.exception("Error during temporary schema deletion: %s", e)
        raise
