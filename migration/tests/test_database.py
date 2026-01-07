#!/usr/bin/env python3
"""
Tests for database functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager

from database import (
    MariaDBMetrics,
    get_mariadb_columns,
    get_pg_columns,
    ma_execute,
    transaction,
    init_mariadb_metrics,
    get_mariadb_metrics,
)
from config import Config


class TestMariaDBMetricsClass:
    """Tests for MariaDBMetrics class."""

    def test_init_with_slow_ms(self):
        """Test initialization with slow_ms."""
        metrics = MariaDBMetrics(slow_ms=200)
        assert metrics.slow_ms == 200
        assert metrics.db_logger is None

    def test_init_with_logger(self):
        """Test initialization with logger."""
        mock_logger = Mock()
        metrics = MariaDBMetrics(slow_ms=100, db_logger=mock_logger)
        assert metrics.db_logger == mock_logger

    def test_op_extraction(self):
        """Test SQL operation extraction."""
        metrics = MariaDBMetrics(slow_ms=100)
        
        # Test different operations
        assert metrics._op("SELECT * FROM test") == "SELECT"
        assert metrics._op("INSERT INTO test VALUES (1)") == "INSERT"
        assert metrics._op("UPDATE test SET x = 1") == "UPDATE"
        assert metrics._op("DELETE FROM test") == "DELETE"
        assert metrics._op("  select * from test") == "SELECT"

    def test_shorten_sql(self):
        """Test shortening of long SQL statements."""
        metrics = MariaDBMetrics(slow_ms=100)
        
        short_sql = "SELECT * FROM test"
        assert metrics._shorten_sql(short_sql) == short_sql
        
        long_sql = "SELECT " + "x" * 600
        shortened = metrics._shorten_sql(long_sql, max_len=500)
        assert len(shortened) == 500
        assert shortened.endswith("...")


class TestMaExecute:
    """Tests for ma_execute function."""

    def test_ma_execute_without_params(self, mock_cursor):
        """Test ma_execute without parameters."""
        ma_execute(mock_cursor, "SELECT * FROM test")
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test")

    def test_ma_execute_with_params(self, mock_cursor):
        """Test ma_execute with parameters."""
        ma_execute(mock_cursor, "SELECT * FROM test WHERE id = %s", (1,))
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM test WHERE id = %s", (1,))


class TestTransaction:
    """Tests for transaction context manager."""

    def test_transaction_success(self, mock_connection, mock_cursor):
        """Test successful transaction with commit."""
        mock_connection.cursor.return_value = mock_cursor
        
        with transaction(mock_connection) as cur:
            assert cur == mock_cursor
        
        mock_connection.commit.assert_called_once()
        mock_cursor.close.assert_called_once()

    def test_transaction_failure(self, mock_connection, mock_cursor):
        """Test failed transaction with rollback."""
        mock_connection.cursor.return_value = mock_cursor
        
        with pytest.raises(ValueError):
            with transaction(mock_connection) as cur:
                raise ValueError("Test error")
        
        mock_connection.rollback.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_connection.commit.assert_not_called()


class TestGetMariaDBColumns:
    """Tests for get_mariadb_columns."""

    def test_get_columns(self, mock_cursor_with_columns):
        """Test column retrieval."""
        # Override to match expected test data
        mock_cursor_with_columns.fetchall.return_value = [
            ("id",), ("name",), ("email",)
        ]
        
        columns = get_mariadb_columns(mock_cursor_with_columns, "users")
        
        assert columns == ["id", "name", "email"]
        mock_cursor_with_columns.execute.assert_called_once()


class TestGetPGColumns:
    """Tests for get_pg_columns."""

    def test_get_columns_success(self, mock_pg_cursor_with_columns):
        """Test PostgreSQL column retrieval."""
        # Override to match expected test data
        mock_pg_cursor_with_columns.fetchall.return_value = [
            ("id", "integer"),
            ("name", "character varying"),
            ("email", "character varying")
        ]
        
        names, types = get_pg_columns(mock_pg_cursor_with_columns, "public", "users")
        
        # Function returns lists, not tuples
        assert list(names) == ["id", "name", "email"]
        assert list(types) == ["integer", "character varying", "character varying"]

    def test_get_columns_empty_table(self, mock_cursor):
        """Test with empty table."""
        mock_cursor.fetchall.return_value = []
        
        with pytest.raises(RuntimeError, match="No columns"):
            get_pg_columns(mock_cursor, "public", "empty_table")


class TestMetricsGlobals:
    """Tests for global metrics functions."""

    def test_init_mariadb_metrics_enabled(self, mock_config):
        """Test initialization with metrics enabled."""
        mock_config.enable_db_metrics = True
        mock_config.db_metrics_slow_ms = 100
        
        init_mariadb_metrics(mock_config)
        
        metrics = get_mariadb_metrics()
        assert metrics is not None
        assert isinstance(metrics, MariaDBMetrics)

    def test_init_mariadb_metrics_disabled(self, mock_config):
        """Test initialization with metrics disabled."""
        mock_config.enable_db_metrics = False
        
        init_mariadb_metrics(mock_config)
        
        metrics = get_mariadb_metrics()
        assert metrics is None


if __name__ == "__main__":
    pytest.main([__file__])