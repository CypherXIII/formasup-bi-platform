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
import logging
import os
import re
import sys
import time
from datetime import date, datetime
from pathlib import Path

from api_enrichment import api_enrich_companies, add_company_fk_to_company_info
from cleanup import run_cleanup
from config import Config, TABLE_ORDER
from database import mariadb_connection, postgres_connection
from logger import setup_logger, setup_db_logger
from migration_core import run_migration
from database import init_mariadb_metrics, get_mariadb_metrics, ma_execute
from sync import sync_tables
from temp_tables import create_temp_schema, create_temp_tables, drop_temp_schema


# Constants for daily execution control
DAILY_RUN_MARKER_FILE = "logs/last_run_date.txt"
DEFAULT_RUN_HOUR = 2  # Default hour to run migration (2 AM)


def get_last_run_date(log_file: str) -> date | None:
    """! @brief Get the last successful migration run date from the log file.

    Parses the log file to find the most recent "Migration finished" entry
    and extracts its date.

    Args:
        log_file: Path to the migration log file.

    Returns:
        The date of the last successful migration, or None if not found.
    """
    log_path = Path(log_file)
    if not log_path.exists():
        return None

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Search from the end for the most recent "Migration finished"
        for line in reversed(lines):
            if "Migration finished" in line:
                # Log format: "2026-01-12 02:00:00,123 | INFO     | Migration finished."
                match = re.match(r"(\d{4}-\d{2}-\d{2})", line)
                if match:
                    return datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except (OSError, ValueError):
        pass

    return None


def should_run_today(log_file: str) -> bool:
    """! @brief Check if migration should run today.

    Migration runs only once per day. This function checks the log file
    to determine if a successful migration has already run today.

    Args:
        log_file: Path to the migration log file.

    Returns:
        True if migration should run, False if it has already run today.
    """
    last_run = get_last_run_date(log_file)
    today = date.today()

    if last_run is None:
        return True

    return last_run < today


def is_time_to_run(run_hour: int) -> bool:
    """! @brief Check if current time has reached the scheduled run hour.

    Args:
        run_hour: Hour of the day to run migration (0-23).

    Returns:
        True if current hour >= run_hour, False otherwise.
    """
    current_hour = datetime.now().hour
    return current_hour >= run_hour


def wait_until_run_time(run_hour: int, logger: logging.Logger) -> None:
    """! @brief Wait until the scheduled run time.

    Args:
        run_hour: Hour of the day to run migration (0-23).
        logger: Logger instance for status messages.
    """
    while not is_time_to_run(run_hour):
        current_time = datetime.now()
        target_time = current_time.replace(hour=run_hour, minute=0, second=0, microsecond=0)

        # If target time is in the past today, it means we passed it
        if target_time <= current_time:
            return

        wait_seconds = (target_time - current_time).total_seconds()
        wait_minutes = int(wait_seconds / 60)

        logger.info(
            f"Waiting {wait_minutes} minutes until scheduled run time ({run_hour:02d}:00)..."
        )

        # Sleep for 5 minutes and check again
        time.sleep(min(300, wait_seconds))

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
    p.add_argument(
        "--force",
        action="store_true",
        help="Force migration even if already run today",
    )
    p.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (do not wait for next day)",
    )
    p.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon: execute once per day, wait and repeat",
    )
    return p.parse_args()


def run_migration_cycle(args: argparse.Namespace, cfg: Config, logger: "logging.Logger") -> None:
    """! @brief Execute a single migration cycle.

    Args:
        args: Parsed command line arguments.
        cfg: Configuration object.
        logger: Logger instance.
    """
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
                # Ensure company_info is properly linked to company
                add_company_fk_to_company_info(pg_conn, cfg)
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


def main() -> None:
    """! @brief Main migration function.

    This function orchestrates the entire migration process based on the
    provided command-line arguments. It handles configuration, logging,
    and the execution of migration, cleanup, and synchronization steps.

    The migration runs only once per day unless --force is specified.
    With --daemon flag, it will wait and run again the next day.
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

    # Daemon mode: run once per day in a loop
    if args.daemon:
        logger.info(
            f"Starting migration daemon (runs once per day at {cfg.migration_run_hour:02d}:00)..."
        )
        while True:
            # Check if migration should run today
            if args.force or should_run_today(cfg.log_file):
                # Only wait if we haven't reached the scheduled time yet
                # If we're past the scheduled time, run immediately
                if not args.force and not is_time_to_run(cfg.migration_run_hour):
                    wait_until_run_time(cfg.migration_run_hour, logger)

                run_migration_cycle(args, cfg, logger)
                # Reset force flag after first run in daemon mode
                args.force = False
            else:
                logger.info(
                    "Migration already completed today (last run: %s)",
                    get_last_run_date(cfg.log_file)
                )

            # Wait for 1 hour before checking again
            logger.info("Sleeping for 1 hour before next check...")
            time.sleep(3600)

    # Single run mode (default or --once)
    else:
        if not args.force and not should_run_today(cfg.log_file):
            last_run = get_last_run_date(cfg.log_file)
            logger.info(
                "Migration already completed today (last run: %s). "
                "Use --force to run anyway.",
                last_run
            )
            return

        # Wait until scheduled time unless forced
        if not args.force and not is_time_to_run(cfg.migration_run_hour):
            logger.info(
                f"Waiting until scheduled run time ({cfg.migration_run_hour:02d}:00)..."
            )
            wait_until_run_time(cfg.migration_run_hour, logger)

        run_migration_cycle(args, cfg, logger)


if __name__ == "__main__":
    main()

