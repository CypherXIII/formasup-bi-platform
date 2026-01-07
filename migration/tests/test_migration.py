#!/usr/bin/env python3
"""
Tests for MariaDB -> PostgreSQL migration module.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from contextlib import contextmanager

# Modules to test
from config import Config
from database import MariaDBMetrics
from migrate import parse_args


class TestConfig:
    """Tests for Config class."""

    def test_config_has_required_fields(self):
        """Test that configuration has all required fields."""
        config = Config()
        
        # Verify that fields exist (even if empty)
        assert hasattr(config, 'mariadb_host')
        assert hasattr(config, 'mariadb_user')
        assert hasattr(config, 'mariadb_password')
        assert hasattr(config, 'mariadb_db')
        assert hasattr(config, 'pg_host')
        assert hasattr(config, 'pg_user')
        assert hasattr(config, 'pg_password')
        assert hasattr(config, 'pg_db')
        assert hasattr(config, 'pg_schema')
        assert hasattr(config, 'batch_size')
        assert hasattr(config, 'temp_schema')

    def test_config_default_values(self):
        """Test configuration default values."""
        config = Config()
        
        # Default batch size
        assert isinstance(config.batch_size, int)
        assert config.batch_size > 0
        
        # Default port
        assert config.mariadb_port == 3306 or config.mariadb_port > 0

    def test_config_validation_with_valid_env(self):
        """Test validation with valid configuration."""
        # Configuration is loaded from .env, should be valid
        config = Config()
        
        # If values are defined in .env, validation should pass
        if config.mariadb_host and config.pg_host:
            config.validate()  # Should not raise exception


class TestMariaDBMetrics:
    """Tests for MariaDBMetrics class."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = MariaDBMetrics(slow_ms=100)

        assert metrics.slow_ms == 100
        assert metrics.total_queries == 0
        assert metrics.total_time_s == 0.0
        assert metrics.ops_count == {}
        assert metrics.ops_time_s == {}
        assert metrics.slow_queries == []

    def test_record_query(self):
        """Test recording a single query."""
        metrics = MariaDBMetrics(slow_ms=100)

        metrics.record("SELECT * FROM test", None, 0.05)  # 50ms

        assert metrics.total_queries == 1
        assert metrics.total_time_s == 0.05
        assert metrics.ops_count["SELECT"] == 1
        assert metrics.ops_time_s["SELECT"] == 0.05

    def test_record_multiple_queries(self):
        """Test recording multiple queries."""
        metrics = MariaDBMetrics(slow_ms=100)

        metrics.record("SELECT * FROM test1", None, 0.05)
        metrics.record("SELECT * FROM test2", None, 0.03)
        metrics.record("INSERT INTO test VALUES (1)", None, 0.02)

        assert metrics.total_queries == 3
        assert metrics.ops_count["SELECT"] == 2
        assert metrics.ops_count["INSERT"] == 1

    def test_record_slow_query(self):
        """Test recording a slow query."""
        metrics = MariaDBMetrics(slow_ms=100)

        metrics.record("SELECT * FROM test", None, 0.15)  # 150ms > 100ms

        assert len(metrics.slow_queries) == 1
        assert metrics.slow_queries[0]["op"] == "SELECT"
        assert metrics.slow_queries[0]["duration_ms"] == 150.0

    def test_record_slow_query_with_logger(self):
        """Test recording a slow query with logger."""
        mock_logger = Mock()
        metrics = MariaDBMetrics(slow_ms=100, db_logger=mock_logger)

        metrics.record("SELECT * FROM test", None, 0.15)  # 150ms > 100ms

        # Logger uses .info() not .warning()
        mock_logger.info.assert_called_once()

    def test_summary(self):
        """Test metrics summary generation."""
        metrics = MariaDBMetrics(slow_ms=100)
        
        metrics.record("SELECT * FROM test", None, 0.05)
        metrics.record("INSERT INTO test VALUES (1)", None, 0.02)
        
        summary = metrics.summary()
        
        assert summary["total_queries"] == 2
        assert "by_op" in summary
        assert "SELECT" in summary["by_op"]
        assert "INSERT" in summary["by_op"]


class TestMigrationArgs:
    """Tests for migration argument parsing."""

    def test_parse_args_default(self):
        """Test default argument parsing."""
        with patch('sys.argv', ['migrate.py']):
            args = parse_args()

            assert args.step == "full"
            assert args.dry_run is False
            assert args.keep_temp is False
            assert args.tables is None

    def test_parse_args_step_migrate(self):
        """Test parsing with step=migrate."""
        with patch('sys.argv', ['migrate.py', '--step', 'migrate']):
            args = parse_args()
            assert args.step == "migrate"

    def test_parse_args_step_cleanup(self):
        """Test parsing with step=cleanup."""
        with patch('sys.argv', ['migrate.py', '--step', 'cleanup']):
            args = parse_args()
            assert args.step == "cleanup"

    def test_parse_args_step_sync(self):
        """Test parsing with step=sync."""
        with patch('sys.argv', ['migrate.py', '--step', 'sync']):
            args = parse_args()
            assert args.step == "sync"

    def test_parse_args_dry_run(self):
        """Test parsing with --dry-run."""
        with patch('sys.argv', ['migrate.py', '--dry-run']):
            args = parse_args()
            assert args.dry_run is True

    def test_parse_args_keep_temp(self):
        """Test parsing with --keep-temp."""
        with patch('sys.argv', ['migrate.py', '--keep-temp']):
            args = parse_args()
            assert args.keep_temp is True

    def test_parse_args_tables(self):
        """Test parsing with --tables."""
        with patch('sys.argv', ['migrate.py', '--tables', 'table1', 'table2']):
            args = parse_args()
            assert args.tables == ['table1', 'table2']

    def test_parse_args_combined(self):
        """Test parsing with multiple arguments."""
        with patch('sys.argv', [
            'migrate.py',
            '--step', 'migrate',
            '--dry-run',
            '--keep-temp',
            '--tables', 'table1', 'table2'
        ]):
            args = parse_args()

            assert args.step == "migrate"
            assert args.dry_run is True
            assert args.keep_temp is True
            assert args.tables == ['table1', 'table2']


class TestConfigDataclass:
    """Tests for Config dataclass."""

    def test_config_is_frozen(self):
        """Test that configuration is immutable."""
        config = Config()
        
        # Config is frozen, so attributes cannot be modified
        with pytest.raises(AttributeError):
            config.mariadb_host = "new_host"

    def test_config_env_variables(self):
        """Test that environment variables are read."""
        # Values come from .env or defaults
        config = Config()
        
        # Types must be correct
        assert isinstance(config.mariadb_port, int)
        assert isinstance(config.batch_size, int)
        assert isinstance(config.enable_db_metrics, bool)
        assert isinstance(config.api_enabled, bool)


if __name__ == "__main__":
    pytest.main([__file__])