#!/usr/bin/env python3
"""! @file database.py
@brief Database connection management for the MariaDB to PostgreSQL migration.
@author Marie Challet
@organization Formasup Auvergne

This module provides context managers for handling database connections
to MariaDB and PostgreSQL, as well as utility functions for database
interactions.
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Tuple

import psycopg2
from psycopg2 import pool
import pymysql

from config import Config


# --- MariaDB Metrics ------------------------------------------------------


class MariaDBMetrics:
    """! @brief Collects client-side impact metrics for MariaDB (read-only).

    Measures the number of queries, total duration, and logs slow queries.
    """

    def __init__(self, slow_ms: int, db_logger: logging.Logger | None = None) -> None:
        """! @brief Initializes the metrics collector.
        @param slow_ms The threshold in milliseconds for a query to be considered slow.
        @param db_logger A dedicated logger for database metrics.
        """
        self.slow_ms = slow_ms
        self.db_logger = db_logger
        self.total_queries: int = 0
        self.total_time_s: float = 0.0
        self.ops_count: Dict[str, int] = {}
        self.ops_time_s: Dict[str, float] = {}
        self.slow_queries: List[Dict[str, Any]] = []

    def _op(self, sql: str) -> str:
        """! @brief Extracts the operation type from an SQL query.
        @param sql The SQL query string.
        @return The uppercase operation type (e.g., 'SELECT', 'INSERT').
        """
        return (sql or "").strip().split(" ", 1)[0].upper()

    def record(self, sql: str, params: Any, duration_s: float) -> None:
        """! @brief Records a single query execution.
        @param sql The executed SQL query.
        @param params The parameters used in the query.
        @param duration_s The query duration in seconds.
        """
        self.total_queries += 1
        self.total_time_s += duration_s
        op = self._op(sql)
        self.ops_count[op] = self.ops_count.get(op, 0) + 1
        self.ops_time_s[op] = self.ops_time_s.get(op, 0.0) + duration_s

        dur_ms = duration_s * 1000
        if dur_ms >= self.slow_ms:
            info = {
                "op": op,
                "duration_ms": round(dur_ms, 1),
                "sql": self._shorten_sql(sql),
            }
            # Avoid logging large parameters
            if params is not None and params != ():
                info["params"] = self._shorten_params(params)
            self.slow_queries.append(info)
            if self.db_logger:
                self.db_logger.info(
                    "SLOW %s %.1fms | %s | params=%r",
                    op,
                    dur_ms,
                    self._shorten_sql(sql),
                    self._shorten_params(params),
                )

    def summary(self) -> Dict[str, Any]:
        """! @brief Generates a summary of all recorded metrics.
        @return A dictionary containing the metrics summary.
        """
        avg_ms = (
            (self.total_time_s / self.total_queries * 1000)
            if self.total_queries
            else 0.0
        )
        by_op = {
            op: {
                "count": self.ops_count.get(op, 0),
                "time_ms": round(self.ops_time_s.get(op, 0.0) * 1000, 1),
            }
            for op in sorted(self.ops_count.keys())
        }
        return {
            "total_queries": self.total_queries,
            "total_time_ms": round(self.total_time_s * 1000, 1),
            "avg_ms_per_query": round(avg_ms, 1),
            "by_op": by_op,
            "slow_threshold_ms": self.slow_ms,
            "slow_queries": self.slow_queries[:20],  # limit size
        }

    def _shorten_sql(self, sql: str, max_len: int = 500) -> str:
        """! @brief Shortens a SQL string for logging.
        @param sql The SQL string to shorten.
        @param max_len The maximum length of the string.
        @return The shortened SQL string.
        """
        s = (sql or "").strip().replace("\n", " ")
        return (s[: max_len - 3] + "...") if len(s) > max_len else s

    def _shorten_params(self, params: Any, max_len: int = 200) -> Any:
        """! @brief Shortens query parameters for logging.
        @param params The parameters to shorten.
        @param max_len The maximum length of the string representation.
        @return The shortened parameters.
        """
        try:
            s = repr(params)
            return (s[: max_len - 3] + "...") if len(s) > max_len else params
        except Exception:
            return None


_maria_metrics: MariaDBMetrics | None = None
_pg_pool: pool.ThreadedConnectionPool | None = None


def init_mariadb_metrics(cfg: Config) -> None:
    """! @brief Initializes MariaDB metrics if enabled in the configuration.
    @param cfg The application configuration.
    """
    global _maria_metrics
    if cfg and getattr(cfg, "enable_db_metrics", False):
        db_logger = logging.getLogger("migration.db")
        _maria_metrics = MariaDBMetrics(cfg.db_metrics_slow_ms, db_logger)
    else:
        _maria_metrics = None


def get_mariadb_metrics() -> MariaDBMetrics | None:
    """! @brief Gets the MariaDB metrics collector instance.
    @return The MariaDBMetrics instance, or None if not initialized.
    """
    return _maria_metrics


def ma_execute(
    cur: pymysql.cursors.Cursor, sql: str, params: Any | None = None
) -> None:
    """! @brief Executes a MariaDB query while measuring its duration and recording metrics.
    @param cur The MariaDB cursor.
    @param sql The SQL query to execute.
    @param params The parameters for the SQL query.
    """
    start = time.perf_counter()
    if params is None:
        cur.execute(sql)
    else:
        cur.execute(sql, params)
    duration = time.perf_counter() - start
    if _maria_metrics:
        _maria_metrics.record(sql, params, duration)


@contextmanager
def mariadb_connection(cfg: Config) -> Iterator[pymysql.connections.Connection]:
    """! @brief Connects to MariaDB with context management for automatic closing.
    @param cfg Configuration containing connection information.
    @yield Active MariaDB connection.
    """
    conn = pymysql.connect(
        host=cfg.mariadb_host,
        user=cfg.mariadb_user,
        password=cfg.mariadb_password,
        database=cfg.mariadb_db,
        port=cfg.mariadb_port,
        connect_timeout=10,
    )
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def postgres_connection(cfg: Config) -> Iterator[psycopg2.extensions.connection]:
    """! @brief Connects to PostgreSQL with context management and initial configuration.

    Implements retry logic with exponential backoff to handle cases where
    the database system is still starting up.

    @param cfg Configuration containing connection information.
    @yield Active PostgreSQL connection.
    @raises Exception In case of connection or configuration error after all retries.
    """
    max_retries = 10
    base_delay = 2  # seconds
    max_delay = 60  # seconds
    logger = logging.getLogger("migration")

    def _configure_connection(conn: psycopg2.extensions.connection) -> None:
        """Apply standard session settings for migration connections."""
        conn.set_session(autocommit=False)
        with conn.cursor() as cur:
            cur.execute(f"SET search_path TO {cfg.pg_schema}")
            cur.execute("SET session_replication_role = 'replica'")
        conn.commit()

    global _pg_pool

    if cfg.use_pg_pool:
        # Lazily initialize a thread-safe pool and reuse it for all callers
        if _pg_pool is None:
            _pg_pool = pool.ThreadedConnectionPool(
                cfg.pg_pool_min,
                cfg.pg_pool_max,
                host=cfg.pg_host,
                user=cfg.pg_user,
                password=cfg.pg_password,
                dbname=cfg.pg_db,
                connect_timeout=10,
            )

        conn = _pg_pool.getconn()
        try:
            _configure_connection(conn)
            yield conn
        finally:
            try:
                if conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
                    conn.rollback()
                with conn.cursor() as cur:
                    cur.execute("SET session_replication_role = 'origin'")
                    conn.commit()
            except Exception as e:
                logger.warning("Error cleaning pooled connection: %s", e)
            _pg_pool.putconn(conn)
        return

    conn = None
    last_exception = None

    for attempt in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=cfg.pg_host,
                user=cfg.pg_user,
                password=cfg.pg_password,
                dbname=cfg.pg_db,
                connect_timeout=10,
            )
            break
        except psycopg2.OperationalError as e:
            last_exception = e
            error_msg = str(e).lower()
            # Retry on startup or connection errors
            if "starting up" in error_msg or "connection refused" in error_msg:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(
                    "PostgreSQL not ready (attempt %d/%d): %s. Retrying in %ds...",
                    attempt + 1, max_retries, e, delay
                )
                time.sleep(delay)
            else:
                # Non-retryable error
                raise

    if conn is None:
        raise last_exception or psycopg2.OperationalError(
            "Failed to connect to PostgreSQL after all retries"
        )
    _configure_connection(conn)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        try:
            if conn.status == psycopg2.extensions.STATUS_IN_TRANSACTION:
                conn.rollback()
            with conn.cursor() as cur:
                cur.execute("SET session_replication_role = 'origin'")
                conn.commit()
        except Exception as e:
            logging.getLogger("migration").warning(
                "Error cleaning up connection: %s", e
            )
        finally:
            conn.close()


@contextmanager
def transaction(
    conn: psycopg2.extensions.connection,
) -> Iterator[psycopg2.extensions.cursor]:
    """! @brief Manages a PostgreSQL transaction with automatic commit/rollback.
    @param conn Active PostgreSQL connection.
    @yield Active PostgreSQL cursor within the transaction.
    @raises Exception Propagates all exceptions after rollback.
    """
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def get_mariadb_columns(
    cur: pymysql.cursors.Cursor,
    table: str,
) -> List[str]:
    """! @brief Retrieves column names from a MariaDB table.
    @param cur Active MariaDB cursor.
    @param table Name of the table from which to retrieve columns.
    @return List of column names.
    """
    cur.execute(f"SHOW COLUMNS FROM {table}")
    cols = cur.fetchall()
    return [col[0] for col in cols]


def get_pg_columns(
    cur: psycopg2.extensions.cursor,
    schema: str,
    table: str,
) -> Tuple[List[str], List[str]]:
    """! @brief Retrieves column names and types from a PostgreSQL table.
    @param cur Active PostgreSQL cursor.
    @param schema Name of the schema containing the table.
    @param table Name of the table from which to retrieve columns.
    @return A tuple containing two lists:
            - List of column names in order of their position
            - List of corresponding data types
    @raises RuntimeError If no columns are found in the table.
    """
    cur.execute(
        """
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (schema, table),
    )
    cols = cur.fetchall()
    if not cols:
        raise RuntimeError(f"No columns in {schema}.{table}")
    names, types = zip(*cols)
    return list(names), list(types)


def convert_value(value: Any, target_type: str) -> Any:
    """! @brief Converts a value to its appropriate PostgreSQL type based on the specified target type.
    @param value The value to convert.
    @param target_type The target PostgreSQL type (e.g., 'integer', 'boolean', etc.).
    @return The converted value in the appropriate type or the original value if conversion is not necessary or fails.
    @note NULL values are returned as is.
    @note In case of a conversion error, the error is logged but the function does not raise an exception.
    """
    if value is None:
        return None
    t = target_type.lower()
    try:
        if t in {"boolean"}:
            return bool(int(value))
        if t in {"integer", "int", "smallint", "bigint"}:
            return int(value)
        if t in {"real", "numeric", "decimal"}:
            return float(value)
        if t in {"character varying", "varchar", "text"}:
            return str(value)
    except Exception as e:
        logging.getLogger("migration").exception(
            "Error converting %r to %s: %s", value, target_type, e
        )
    return value


def normalize_names(row: Dict[str, Any]) -> Dict[str, Any]:
    """! @brief Normalizes first and last names in a data dictionary.
    @param row Dictionary potentially containing 'first_name' and 'last_name' keys.
    @return The updated dictionary with normalized names:
            - first name: first letter capitalized
            - last name: all uppercase
    """
    if row.get("first_name"):
        row["first_name"] = row["first_name"].strip().title()
    if row.get("last_name"):
        row["last_name"] = row["last_name"].strip().upper()
    return row
