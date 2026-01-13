#!/usr/bin/env python3
"""! @file sync.py
@brief Functions for synchronization between temporary and main tables.
@author Marie Challet
@organization Formasup Auvergne

This module provides functions to synchronize data from the temporary staging
tables to the final production tables.
"""

import logging
import time
from typing import Dict, List

import psycopg2 # type: ignore

from config import Config, CONFLICT_KEYS, TABLE_ORDER, PROTECTED_TABLES
from database import get_pg_columns, transaction


def sync_tables(
    conn_pg: psycopg2.extensions.connection, cfg: Config, tables: List[str]
) -> Dict[str, Dict[str, int]]:
    """! @brief Compares and synchronizes temporary tables with main tables.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing schema names.
    @param tables List of tables to synchronize.
    @return Dictionary of statistics by table containing:
            - inserts: number of insertions performed
            - updates: number of updates performed
            - deletes: number of deletions performed
    @note Insertions and updates are performed in a single operation
          with INSERT ... ON CONFLICT.
    @note For tables with "updated_at", the update is only performed if
          the temporary data is more recent.
    @note For tables that are not fundamental dimensions, records
          that no longer exist in the temporary tables are deleted
          from the main tables.
    @note Tables in PROTECTED_TABLES are skipped (reference data).
    """
    logger = logging.getLogger("migration")
    logger.info(
        "=== Synchronizing temporary tables to main tables ==="
    )

    stats: Dict[str, Dict[str, int]] = {}

    for table in [t for t in TABLE_ORDER if t not in PROTECTED_TABLES]:
        if table not in tables:
            continue

        logger.info("Synchronizing %s...", table)
        stats[table] = {"inserts": 0, "updates": 0, "deletes": 0}
        start_time = time.time()
        success = True
        error_message = None

        # Get the primary key for the table
        key = CONFLICT_KEYS.get(table)
        if not key:
            logger.warning(
                "No primary key found for %s, synchronization impossible", table
            )
            continue

        try:
            # Get the columns of the table
            with conn_pg.cursor() as cur:
                pg_cols, _ = get_pg_columns(cur, cfg.pg_schema, table)

            columns = ", ".join(pg_cols)
            set_clause = ", ".join(
                [f"{col} = excluded.{col}" for col in pg_cols if col != key]
            )

            # Count rows before synchronization
            with conn_pg.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {cfg.pg_schema}.{table}")
                count_before = cur.fetchone()[0]  # type: ignore

            # 1. Insertion and update in a single operation with ON CONFLICT
            if "updated_at" in pg_cols:
                # For tables with updated_at
                with transaction(conn_pg) as cur:
                    cur.execute(f"""
                    INSERT INTO {cfg.pg_schema}.{table} ({columns})
                    SELECT {columns} FROM {cfg.temp_schema}.{table}
                    ON CONFLICT ({key}) DO UPDATE SET
                        {set_clause}
                    WHERE {cfg.pg_schema}.{table}.updated_at < excluded.updated_at
                    """)
                    affected = cur.rowcount
            else:
                # For tables without 'updated_at', compare columns one by one
                where_clause = " OR ".join(
                    [
                        f"{cfg.pg_schema}.{table}.{col} IS DISTINCT FROM excluded.{col}"
                        for col in pg_cols
                        if col != key
                    ]
                )

                with transaction(conn_pg) as cur:
                    cur.execute(f"""
                    INSERT INTO {cfg.pg_schema}.{table} ({columns})
                    SELECT {columns} FROM {cfg.temp_schema}.{table}
                    ON CONFLICT ({key}) DO UPDATE SET
                        {set_clause}
                    WHERE {where_clause}
                    """)
                    affected = cur.rowcount

            # Count rows after to determine actual insertions
            with conn_pg.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {cfg.pg_schema}.{table}")
                count_after = cur.fetchone()[0]  # type: ignore

            # Actual insertions are the difference between before and after
            stats[table]["inserts"] = count_after - count_before
            # Updates are the affected rows minus the insertions
            stats[table]["updates"] = max(0, affected - stats[table]["inserts"])

            # 2. Deletion of records that are no longer in the temporary table
            # (only for tables that are not dimensions)
            if table not in [
                "degree_level",
            ]:
                with transaction(conn_pg) as cur:
                    cur.execute(f"""
                    DELETE FROM {cfg.pg_schema}.{table}
                    WHERE {key} NOT IN (SELECT {key} FROM {cfg.temp_schema}.{table})
                    """)
                    stats[table]["deletes"] = cur.rowcount

            # Get the final count of records in the table
            with conn_pg.cursor() as cur:
                cur.execute(f"SELECT COUNT(*) FROM {cfg.pg_schema}.{table}")
                final_count = cur.fetchone()[0]  # type: ignore

            logger.info(
                "Synchronization of %s finished: %d inserts/updates, %d deletes",
                table,
                stats[table]["inserts"] + stats[table]["updates"],
                stats[table]["deletes"],
            )

        except Exception as e:
            logger.exception("Error during synchronization of %s: %s", table, e)
            conn_pg.rollback()
            success = False
            error_message = str(e)
            final_count = 0

        # Calculate the duration
        duration = time.time() - start_time

        # Record statistics in update_log
        try:
            with transaction(conn_pg) as cur:
                cur.execute(
                    f"""
                INSERT INTO {cfg.pg_schema}.update_log (
                    migration_name, table_name, inserted, updates, deletes,
                    final_count, duration_seconds, success, error
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    (
                        "sync_tables",
                        table,
                        stats[table]["inserts"],
                        stats[table]["updates"],
                        stats[table]["deletes"],
                        final_count,
                        round(duration, 2),
                        success,
                        error_message,
                    ),
                )
        except Exception as e:
            logger.exception(
                "Error while recording statistics in update_log for %s: %s",
                table,
                e,
            )

    return stats
