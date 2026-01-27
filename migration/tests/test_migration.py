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
from sync import ensure_updated_at_trigger, ensure_company_indexes, analyze_tables


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

    def test_config_pool_defaults(self):
        """Test that pool settings load with sane defaults."""
        config = Config()
        assert isinstance(config.use_pg_pool, bool)
        assert config.pg_pool_min > 0
        assert config.pg_pool_max >= config.pg_pool_min

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


class TestUpdatedAtTrigger:
    """Tests for ensure_updated_at_trigger helper."""

    def test_ensure_updated_at_trigger_generates_sql(self, monkeypatch):
        """Ensure the trigger DDL block is executed."""

        executed: list[tuple] = []

        class FakeCursor:
            def execute(self, sql: str, params=None) -> None:
                executed.append((sql, params))

            def fetchone(self):
                # Simulate that column exists, function/trigger don't exist
                if "updated_at" in executed[-1][0]:
                    return (True,)
                return (False,)

        class FakeCtx:
            def __enter__(self) -> FakeCursor:
                return FakeCursor()

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        def fake_transaction(_conn):
            return FakeCtx()

        monkeypatch.setattr("sync.transaction", fake_transaction)

        cfg = Config()
        ensure_updated_at_trigger(object(), cfg, "company")

        assert executed, "Trigger helper should execute SQL queries"
        # Should have queries for checking column, function, trigger, and creating them
        assert len(executed) >= 4, "Should check and create function and trigger"
        assert any("CREATE FUNCTION" in sql for sql, _ in executed)
        assert any("CREATE TRIGGER" in sql for sql, _ in executed)

    def test_ensure_updated_at_trigger_handles_exception(self, monkeypatch):
        """Function should not raise if transaction fails."""

        def failing_transaction(_conn):
            raise RuntimeError("boom")

        monkeypatch.setattr("sync.transaction", failing_transaction)

        cfg = Config()
        # Should swallow exceptions and log
        ensure_updated_at_trigger(object(), cfg, "company")


class TestIndexHelpers:
    """Tests for index and analyze helpers."""

    def test_ensure_company_indexes_creates_all_targets(self, monkeypatch):
        executed: list[str] = []

        class FakeCursor:
            def __init__(self) -> None:
                self.step = 0

            def execute(self, sql: str, params=None) -> None:
                executed.append(sql)

            def fetchone(self):
                return (False,)

        class FakeCtx:
            def __enter__(self) -> FakeCursor:
                return FakeCursor()

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        def fake_tx(_conn):
            return FakeCtx()

        monkeypatch.setattr("sync.transaction", fake_tx)

        cfg = Config()
        ensure_company_indexes(object(), cfg)

        # We expect existence checks and create statements for 6 indexes (3 tables * 2 schemas)
        create_statements = [sql for sql in executed if "CREATE INDEX" in sql]
        assert len(create_statements) == 6
        assert any("registration" in sql for sql in create_statements)
        assert any("billing" in sql for sql in create_statements)

    def test_analyze_tables_runs_analyze(self, monkeypatch):
        executed: list[str] = []

        class FakeCursor:
            def execute(self, sql: str, params=None) -> None:
                executed.append(sql)

        class FakeCtx:
            def __enter__(self) -> FakeCursor:
                return FakeCursor()

            def __exit__(self, exc_type, exc, tb) -> None:
                return None

        def fake_tx(_conn):
            return FakeCtx()

        monkeypatch.setattr("sync.transaction", fake_tx)

        cfg = Config()
        analyze_tables(object(), cfg, ["company", "registration"])

        assert any("ANALYZE" in sql for sql in executed)

class TestCleanupObsoleteCompanies:
    """Tests for cleanup_obsolete_companies function."""

    def test_cleanup_obsolete_companies_with_mock_connection(self):
        """Test cleanup of obsolete companies with mocked PostgreSQL connection."""
        from cleanup import cleanup_obsolete_companies

        # Mock connection and cursor
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock config
        config = Config()

        # Setup cursor responses
        # First query returns 3 obsolete company IDs
        mock_cursor.fetchall.return_value = [(1,), (2,), (3,)]
        mock_cursor.rowcount = 3

        # Execute cleanup
        cleanup_obsolete_companies(mock_conn, config)

        # Verify queries were executed
        assert mock_cursor.execute.called

        # Verify commit was called
        assert mock_conn.commit.called

    def test_cleanup_no_obsolete_companies(self):
        """Test cleanup when there are no obsolete companies."""
        from cleanup import cleanup_obsolete_companies

        # Mock connection and cursor
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Mock config
        config = Config()

        # Setup cursor responses - no obsolete companies
        mock_cursor.fetchall.return_value = []

        # Execute cleanup
        cleanup_obsolete_companies(mock_conn, config)

        # Verify queries were executed
        assert mock_cursor.execute.called

    def test_cleanup_obsolete_companies_error_handling(self):
        """Test error handling in cleanup_obsolete_companies."""
        from cleanup import cleanup_obsolete_companies

        # Mock connection that raises an exception
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.side_effect = Exception("Database error")

        # Mock config
        config = Config()

        # Should not raise exception but handle it gracefully
        try:
            cleanup_obsolete_companies(mock_conn, config)
        except Exception:
            pytest.fail("cleanup_obsolete_companies should handle exceptions gracefully")

        # Verify rollback was called
        assert mock_conn.rollback.called


class TestSyncCorrectedSirets:
    """Tests for sync_corrected_sirets function."""

    def test_sync_corrected_sirets_finds_and_updates(self):
        """Test that corrected SIRETs are detected and staging is updated."""
        from cleanup import sync_corrected_sirets

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        config = Config()

        # First query returns one corrected SIRET
        # Second query (replacement lookup) returns a replacement company
        mock_cursor.fetchall.return_value = [("77363330800017", 100)]
        mock_cursor.fetchone.return_value = (200,)  # replacement company id
        mock_cursor.rowcount = 1

        sync_corrected_sirets(mock_conn, config)

        # Verify queries were executed
        assert mock_cursor.execute.called
        assert mock_conn.commit.called

    def test_sync_corrected_sirets_no_corrections(self):
        """Test when there are no corrected SIRETs."""
        from cleanup import sync_corrected_sirets

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        config = Config()

        # No corrected SIRETs found
        mock_cursor.fetchall.return_value = []

        sync_corrected_sirets(mock_conn, config)

        # Should return early without error
        assert mock_cursor.execute.called

    def test_sync_corrected_sirets_error_handling(self):
        """Test error handling in sync_corrected_sirets."""
        from cleanup import sync_corrected_sirets

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.side_effect = Exception("DB error")

        config = Config()

        # Should not raise but handle gracefully
        try:
            sync_corrected_sirets(mock_conn, config)
        except Exception:
            pytest.fail("sync_corrected_sirets should handle exceptions gracefully")

        assert mock_conn.rollback.called


class TestCleanupStagingTempCompanies:
    """Tests for cleanup_staging_temp_companies function."""

    def test_cleanup_staging_temp_companies(self):
        """Test deletion of temp companies from staging."""
        from cleanup import cleanup_staging_temp_companies

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        config = Config()
        mock_cursor.rowcount = 5

        cleanup_staging_temp_companies(mock_conn, config)

        assert mock_cursor.execute.called
        assert mock_conn.commit.called


class TestCleanupStagingUnreferencedCompanies:
    """Tests for cleanup_staging_unreferenced_companies."""

    def test_cleanup_unreferenced(self):
        from cleanup import cleanup_staging_unreferenced_companies

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.rowcount = 4

        config = Config()

        cleanup_staging_unreferenced_companies(mock_conn, config)

        assert mock_cursor.execute.called
        assert mock_conn.commit.called


class TestCleanupUnreferencedTraining:
    """Tests for cleanup_unreferenced_training function."""

    def test_cleanup_unreferenced_training_deletes_records(self):
        """Test deletion of training records with no valid registrations."""
        from cleanup import cleanup_unreferenced_training

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        config = Config()
        # First batch deletes 3, second batch deletes 0 (end of batching)
        mock_cursor.rowcount = 3

        cleanup_unreferenced_training(mock_conn, config)

        assert mock_cursor.execute.called
        assert mock_conn.commit.called
        # Verify DELETE query contains the signature_date condition
        call_args = mock_cursor.execute.call_args_list[0][0][0]
        assert "signature_date" in call_args
        assert "2022-06-01" in call_args

    def test_cleanup_unreferenced_training_no_records(self):
        """Test cleanup when no unreferenced training records exist."""
        from cleanup import cleanup_unreferenced_training

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        config = Config()
        mock_cursor.rowcount = 0

        cleanup_unreferenced_training(mock_conn, config)

        assert mock_cursor.execute.called
        assert mock_conn.commit.called

    def test_cleanup_unreferenced_training_error_handling(self):
        """Test error handling in cleanup_unreferenced_training."""
        from cleanup import cleanup_unreferenced_training

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.side_effect = Exception("DB error")

        config = Config()

        try:
            cleanup_unreferenced_training(mock_conn, config)
        except Exception:
            pytest.fail("cleanup_unreferenced_training should handle exceptions gracefully")

        assert mock_conn.rollback.called


class TestCleanupUnreferencedRncp:
    """Tests for cleanup_unreferenced_rncp function."""

    def test_cleanup_unreferenced_rncp_deletes_records(self):
        """Test deletion of RNCP records not referenced by training."""
        from cleanup import cleanup_unreferenced_rncp

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        config = Config()
        mock_cursor.rowcount = 5

        cleanup_unreferenced_rncp(mock_conn, config)

        assert mock_cursor.execute.called
        assert mock_conn.commit.called
        # Verify DELETE query checks both rncp_id and rncp_number
        call_args = mock_cursor.execute.call_args_list[0][0][0]
        assert "rncp_id" in call_args
        assert "rncp_number" in call_args

    def test_cleanup_unreferenced_rncp_no_records(self):
        """Test cleanup when no unreferenced RNCP records exist."""
        from cleanup import cleanup_unreferenced_rncp

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        config = Config()
        mock_cursor.rowcount = 0

        cleanup_unreferenced_rncp(mock_conn, config)

        assert mock_cursor.execute.called
        assert mock_conn.commit.called

    def test_cleanup_unreferenced_rncp_error_handling(self):
        """Test error handling in cleanup_unreferenced_rncp."""
        from cleanup import cleanup_unreferenced_rncp

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.side_effect = Exception("DB error")

        config = Config()

        try:
            cleanup_unreferenced_rncp(mock_conn, config)
        except Exception:
            pytest.fail("cleanup_unreferenced_rncp should handle exceptions gracefully")

        assert mock_conn.rollback.called


if __name__ == "__main__":
    pytest.main([__file__])
