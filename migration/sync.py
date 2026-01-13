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


def sync_company_sirets(
    conn_pg: psycopg2.extensions.connection, cfg: Config
) -> Dict[str, int]:
    """! @brief Synchronizes only new SIRETs from temp company to staging company.

    This function handles company specially:
    - Inserts new companies (by SIRET) that don't exist in staging
    - Maps temp IDs to staging IDs for use by other tables
    - Does NOT update existing companies (API enrichment handles that)

    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing schema names.
    @return Dictionary with insert count and mapping count.
    """
    logger = logging.getLogger("migration")
    logger.info("=== Synchronizing company SIRETs ===")

    stats = {"inserts": 0, "mappings": 0}

    try:
        with conn_pg.cursor() as cur:
            # 1. Insert new companies (SIRETs that don't exist in staging)
            # Only insert siret - other fields are populated by API enrichment
            cur.execute(f"""
                INSERT INTO {cfg.pg_schema}.company (siret, discr)
                SELECT tc.siret, tc.discr
                FROM {cfg.temp_schema}.company tc
                WHERE tc.siret IS NOT NULL
                  AND tc.siret != ''
                  AND NOT EXISTS (
                      SELECT 1 FROM {cfg.pg_schema}.company sc
                      WHERE sc.siret = tc.siret
                  );
            """)
            stats["inserts"] = cur.rowcount
            logger.info(f"Inserted {stats['inserts']} new companies with unique SIRETs")

            # 2. Update updated_at only if temp has a more recent date
            cur.execute(f"""
                UPDATE {cfg.pg_schema}.company sc
                SET updated_at = tc.updated_at
                FROM {cfg.temp_schema}.company tc
                WHERE sc.siret = tc.siret
                  AND tc.siret IS NOT NULL
                  AND tc.siret != ''
                  AND (sc.updated_at IS NULL OR tc.updated_at > sc.updated_at);
            """)
            updates = cur.rowcount
            logger.info(f"Updated {updates} companies with more recent updated_at")

            # 3. Create ID mapping table (temp_id -> staging_id)
            cur.execute(f"""
                DROP TABLE IF EXISTS {cfg.temp_schema}.company_id_mapping;

                SELECT tc.id AS temp_id, sc.id AS staging_id
                INTO {cfg.temp_schema}.company_id_mapping
                FROM {cfg.temp_schema}.company tc
                JOIN {cfg.pg_schema}.company sc ON tc.siret = sc.siret
                WHERE tc.siret IS NOT NULL AND tc.siret != '';
            """)

            cur.execute(f"SELECT COUNT(*) FROM {cfg.temp_schema}.company_id_mapping")
            stats["mappings"] = cur.fetchone()[0]
            logger.info(f"Created {stats['mappings']} company ID mappings")

            # 3. Update references in temp tables to use staging IDs
            # Update registration.host_company_id
            cur.execute(f"""
                UPDATE {cfg.temp_schema}.registration r
                SET host_company_id = m.staging_id
                FROM {cfg.temp_schema}.company_id_mapping m
                WHERE r.host_company_id = m.temp_id
                  AND m.temp_id != m.staging_id;
            """)
            reg_updates = cur.rowcount
            logger.info(f"Updated {reg_updates} registration.host_company_id references")

            # Update billing.company_id
            cur.execute(f"""
                UPDATE {cfg.temp_schema}.billing b
                SET company_id = m.staging_id
                FROM {cfg.temp_schema}.company_id_mapping m
                WHERE b.company_id = m.temp_id
                  AND m.temp_id != m.staging_id;
            """)
            bill_updates = cur.rowcount
            logger.info(f"Updated {bill_updates} billing.company_id references")

            # Clean up mapping table
            cur.execute(f"DROP TABLE IF EXISTS {cfg.temp_schema}.company_id_mapping;")

        conn_pg.commit()
        logger.info(f"Company SIRET sync complete: {stats['inserts']} inserts, {stats['mappings']} mappings")

    except Exception as e:
        conn_pg.rollback()
        logger.exception(f"Error during company SIRET sync: {e}")

    return stats


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

    # Handle company specially - sync only new SIRETs
    if "company" in tables:
        sync_company_sirets(conn_pg, cfg)

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
