#!/usr/bin/env python3
"""! @file migrate.py
@brief Main entry point for the MariaDB to PostgreSQL migration tool.
@author Marie Challet
@organization Formasup Auvergne

This script orchestrates the entire migration process, including data transfer,
cleaning, and synchronization. It provides a command-line interface to
execute the migration in full or in discrete steps.
"""

from __future__ import annotations

import argparse
import json
import sys

from api_enrichment import api_enrich_companies
from cleanup import run_cleanup
from config import Config, TABLE_ORDER
from database import mariadb_connection, postgres_connection
from logger import setup_logger, setup_db_logger
from migration_core import run_migration
from database import init_mariadb_metrics, get_mariadb_metrics, ma_execute
from sync import sync_tables
from temp_tables import create_temp_schema, create_temp_tables, drop_temp_schema


def parse_args() -> argparse.Namespace:
    """! @brief Parse command line arguments.
    @return An argparse.Namespace object containing the parsed arguments.
    """
    p = argparse.ArgumentParser(description="Migrate MariaDB ➜ PostgreSQL")
    p.add_argument(
        "--step",
        choices=["migrate", "cleanup", "sync", "full"],
        default="full",
        help="Step to execute: 'migrate', 'cleanup', 'sync', or 'full'",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in simulation mode without modifying data",
    )
    p.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary tables after migration",
    )
    p.add_argument(
        "--tables", nargs="+", help="Specific tables to migrate (default: all)"
    )
    return p.parse_args()


def main() -> None:
    """! @brief Main migration function.
    
    This function orchestrates the entire migration process based on the
    provided command-line arguments. It handles configuration, logging,
    and the execution of migration, cleanup, and synchronization steps.
    """
    args = parse_args()

    # Load and validate configuration
    cfg = Config()
    try:
        cfg.validate()
    except Exception as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)

    # Configure logger
    logger = setup_logger(cfg.log_file)
    # Specific logger for DB metrics + metric initialization
    if cfg.enable_db_metrics:
        setup_db_logger(cfg.db_metrics_log_file)
        init_mariadb_metrics(cfg)
    logger.info("Starting migration (step=%s, dry_run=%s)", args.step, args.dry_run)

    with mariadb_connection(cfg) as ma_conn, postgres_connection(cfg) as pg_conn:
        # Determine which tables to migrate
        tables_to_migrate = args.tables if args.tables else TABLE_ORDER.copy()

        # Check that the tables exist in MariaDB
        with ma_conn.cursor() as cur:
            ma_execute(cur, "SHOW TABLES")
            available_tables = {r[0] for r in cur.fetchall()}

        # Filter to keep only tables that actually exist
        tables = [t for t in tables_to_migrate if t in available_tables]

        if not tables:
            logger.warning("No tables to migrate were found in MariaDB!")
            return

        logger.info("Tables to migrate: %s", ", ".join(tables))

        if args.step in ("migrate", "full"):
            # Create temporary schema and tables
            if not args.dry_run:
                create_temp_schema(pg_conn, cfg)
                create_temp_tables(pg_conn, cfg, tables)

            # Migrate data from MariaDB to temporary tables
            stats = run_migration(
                ma_conn,
                pg_conn,
                cfg,
                tables,
                mode=("dry-run" if args.dry_run else "live"),
            )

            # Log statistics
            if not args.dry_run:
                with pg_conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO {cfg.pg_schema}.migration_logs (stats, success) VALUES (%s, %s)",
                        (json.dumps(stats), True),
                    )
                    pg_conn.commit()

        if args.step in ("cleanup", "full") and not args.dry_run:
            # Clean data in temporary tables
            run_cleanup(pg_conn, cfg)

        if args.step in ("sync", "full") and not args.dry_run:
            # Synchronize temporary tables with main tables
            sync_stats = sync_tables(pg_conn, cfg, tables)
            logger.info("Synchronization summary: %s", json.dumps(sync_stats))

            # API enrichment after synchronization
            if cfg.api_enabled:
                api_stats = api_enrich_companies(pg_conn, cfg)
                logger.info("Company API summary: %s", json.dumps(api_stats))

            # Log synchronization statistics
            try:
                with pg_conn.cursor() as cur:
                    # First, check if the migration_type column exists
                    cur.execute(
                        """
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s AND table_name = 'migration_logs' 
                        AND column_name = 'migration_type'
                    """,
                        (cfg.pg_schema,),
                    )

                    has_migration_type = cur.fetchone() is not None

                    if has_migration_type:
                        cur.execute(
                            f"INSERT INTO {cfg.pg_schema}.migration_logs (stats, success, migration_type) VALUES (%s, %s, %s)",
                            (json.dumps(sync_stats), True, "sync"),
                        )
                    else:
                        cur.execute(
                            f"INSERT INTO {cfg.pg_schema}.migration_logs (stats, success) VALUES (%s, %s)",
                            (json.dumps(sync_stats), True),
                        )
                    pg_conn.commit()
            except Exception as e:
                logger.error(
                    "Error while saving sync stats: %s",
                    e,
                )
                pg_conn.rollback()

        # Delete temporary tables if requested
        if not args.dry_run and not args.keep_temp and args.step in ("sync", "full"):
            drop_temp_schema(pg_conn, cfg)

    logger.info("Migration finished.")

    # MariaDB impact summary
    if cfg.enable_db_metrics:
        metrics = get_mariadb_metrics()
        if metrics:
            summary = metrics.summary()
            logger.info(
                "MariaDB Impact: %d queries, %.1f ms total (average %.1f ms)",
                summary["total_queries"],
                summary["total_time_ms"],
                summary["avg_ms_per_query"],
            )
            logger.info("Breakdown by operation: %s", summary["by_op"])
            slow = summary.get("slow_queries", [])
            if slow:
                logger.info(
                    "Top slow queries (>%d ms) logged in %s",
                    cfg.db_metrics_slow_ms,
                    cfg.db_metrics_log_file,
                )


if __name__ == "__main__":
    main()
