#!/usr/bin/env python3
"""! @file migration_core.py
@brief Core functions for migrating data from MariaDB to PostgreSQL.
@author Marie Challet
@organization Formasup Auvergne

This module contains the main logic for the data migration process,
including adaptive batching and handling of different table sizes.
"""

import logging
import time
from typing import Any, Dict, Sequence

import psycopg2
import pymysql
from psycopg2.extras import execute_values

from config import Config, TABLE_ORDER
from database import (
    get_pg_columns,
    get_mariadb_columns,
    normalize_names,
    transaction,
    convert_value,
    ma_execute,
    get_mariadb_metrics,
)


def run_migration(
    conn_maria: pymysql.connections.Connection,
    conn_pg: psycopg2.extensions.connection,
    cfg: Config,
    tables: Sequence[str],
    mode: str,
) -> Dict[str, Any]:
    """! @brief Executes the data migration from MariaDB to PostgreSQL.
    @param conn_maria Active MariaDB connection.
    @param conn_pg Active PostgreSQL connection.
    @param cfg Configuration containing schema names.
    @param tables List of tables to migrate.
    @param mode Execution mode ('dry-run' or 'live').
    @return Dictionary containing migration statistics by table.
    """
    logger = logging.getLogger("migration")
    stats: Dict[str, Any] = {}

    # Use the temporary schema for insertion
    target_schema = cfg.temp_schema if mode != "dry-run" else cfg.pg_schema

    # 1. Estimate the total number of required queries
    table_sizes = {}
    total_expected_queries = 0

    # Get the size of all tables in a single connection
    with conn_maria.cursor() as ma_cur:
        for table in TABLE_ORDER:
            if table not in tables:
                continue
            ma_execute(ma_cur, f"SELECT COUNT(*) FROM {table}")
            count = ma_cur.fetchone()[0]
            table_sizes[table] = count
            # For each table: 1 query for the COUNT + estimation of the number of queries by pagination
            if count > 0:
                # If the table is small, we process it in a single query
                # Otherwise we estimate the number of queries by pagination
                if count <= cfg.batch_size:
                    total_expected_queries += 1  # Just one query for the data
                else:
                    total_expected_queries += (
                        count + cfg.batch_size - 1
                    ) // cfg.batch_size

    # 2. Optimize the strategy according to the size of the tables
    query_count = 0  # Query counter (local tracking for progress logs)

    for table in TABLE_ORDER:
        if table not in tables or table not in table_sizes:
            logger.info(f"Skip missing table {table}")
            continue

        table_size = table_sizes[table]
        if table_size == 0:
            logger.info(f"No data in {table}")
            continue

        logger.info(f"Migrating {table} to {target_schema}... ({table_size} rows)")
        start = time.time()

        # Get the structure of the PostgreSQL table
        with conn_pg.cursor() as pg_cur:
            try:
                pg_cols, pg_types = get_pg_columns(pg_cur, cfg.pg_schema, table)
            except RuntimeError as e:
                logger.warning(str(e))
                continue

        # Get the columns from MariaDB and keep only the common columns
        with conn_maria.cursor() as ma_cur:
            maria_cols = get_mariadb_columns(ma_cur, table)

        # Intersection: columns present in both databases
        common_cols = []
        common_types = []
        for i, col in enumerate(pg_cols):
            if col in maria_cols:
                common_cols.append(col)
                common_types.append(pg_types[i])

        if not common_cols:
            logger.warning(f"No common columns between PostgreSQL and MariaDB for table {table}")
            continue

        if len(common_cols) < len(pg_cols):
            missing = set(pg_cols) - set(common_cols)
            logger.info(f"Table {table}: {len(missing)} columns missing in MariaDB: {missing}")

        columns = ", ".join(f"{c}" for c in common_cols)

        # Adaptive strategy according to the size of the table
        inserted = 0
        processed_count = 0
        error_message = None

        try:
            # For small tables (less rows than batch_size), a single query
            if table_size <= cfg.batch_size:
                with conn_maria.cursor() as ma_cur:
                    ma_execute(ma_cur, f"SELECT {columns} FROM {table}")
                    if m := get_mariadb_metrics():
                        query_count = m.total_queries
                    rows = ma_cur.fetchall()

                processed_batch = []
                for rec in rows:
                    d = {
                        common_cols[i]: convert_value(rec[i], common_types[i])
                        for i in range(len(common_cols))
                    }
                    if table == "apprentice":
                        d = normalize_names(d)
                    processed_batch.append(tuple(d[c] for c in common_cols))

                if mode != "dry-run" and processed_batch:
                    sql = f"INSERT INTO {target_schema}.{table} ({columns}) VALUES %s;"
                    with transaction(conn_pg) as tx:
                        execute_values(tx, sql, processed_batch)
                    inserted += len(processed_batch)
                    processed_count += len(processed_batch)
                else:
                    logger.info(
                        f"DRY-RUN: would insert {len(processed_batch)} rows into {table}"
                    )
                    processed_count = len(processed_batch)

            # For large tables, use pagination
            else:
                # Calculate an optimal batch size to minimize queries
                adaptive_batch_size = min(10000, max(cfg.batch_size, table_size // 10))

                offset = 0
                while offset < table_size:
                    with conn_maria.cursor() as ma_cur:
                        ma_execute(
                            ma_cur,
                            f"SELECT {columns} FROM {table} LIMIT %s OFFSET %s",
                            (adaptive_batch_size, offset),
                        )
                        if m := get_mariadb_metrics():
                            query_count = m.total_queries
                        rows = ma_cur.fetchall()

                    if not rows:
                        break

                    processed_batch = []
                    for rec in rows:
                        d = {
                            common_cols[i]: convert_value(rec[i], common_types[i])
                            for i in range(len(common_cols))
                        }
                        if table == "apprentice":
                            d = normalize_names(d)
                        processed_batch.append(tuple(d[c] for c in common_cols))

                    if mode != "dry-run" and processed_batch:
                        sql = f"INSERT INTO {target_schema}.{table} ({columns}) VALUES %s;"
                        for i in range(0, len(processed_batch), cfg.batch_size):
                            sub_batch = processed_batch[i : i + cfg.batch_size]
                            with transaction(conn_pg) as tx:
                                execute_values(tx, sql, sub_batch)
                            inserted += len(sub_batch)
                    else:
                        logger.info(
                            f"DRY-RUN: would insert {len(processed_batch)} rows from batch"
                        )

                    processed_count += len(processed_batch)
                    offset += adaptive_batch_size
                    logger.info(
                        f"Processed {processed_count}/{table_size} rows from {table} (queries: {query_count})"
                    )

            # Final count
            with conn_pg.cursor() as pg_cur:
                pg_cur.execute(f"SELECT COUNT(*) FROM {target_schema}.{table}")
                final = pg_cur.fetchone()[0]  # type: ignore

            duration = time.time() - start
            stats[table] = {
                "processed": processed_count,
                "inserted": inserted,
                "final": final,
                "time_s": round(duration, 2),
            }

            logger.info(
                f"{table}: {inserted}/{processed_count} rows inserted in {duration:.2f}s"
            )

            # Log migration details
            if mode != "dry-run":
                with conn_pg.cursor() as pg_cur:
                    pg_cur.execute(
                        f"""
                        INSERT INTO {cfg.pg_schema}.migration_table_log (
                            migration_name, table_name, processed, inserted, skipped,
                            final_count, duration_seconds, success, error
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                        (
                            "run_migration",
                            table,
                            processed_count,
                            inserted,
                            processed_count - inserted,
                            final,
                            round(duration, 2),
                            error_message is None,
                            error_message,
                        ),
                    )
                    conn_pg.commit()

        except Exception as e:
            error_message = str(e)
            logger.exception(f"Error during migration of table {table}: {e}")

    logger.info(f"Migration completed using {query_count} MariaDB queries")
    return stats
