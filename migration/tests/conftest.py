#!/usr/bin/env python3
"""
Shared pytest fixtures for migration tests.

This module provides common fixtures used across multiple test modules to reduce
code duplication and ensure consistent test setup.
"""

import pytest
import logging
from unittest.mock import Mock

from config import Config
from database import MariaDBMetrics


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_config() -> Mock:
    """
    Create a mock Config object with default values.
    
    Returns:
        Mock object configured with typical Config attributes
    """
    config = Mock(spec=Config)
    
    # Database settings
    config.mariadb_host = "localhost"
    config.mariadb_port = 3306
    config.mariadb_user = "test_user"
    config.mariadb_password = "test_password"
    config.mariadb_db = "test_db"
    
    config.pg_host = "localhost"
    config.pg_port = 5432
    config.pg_user = "test_user"
    config.pg_password = "test_password"
    config.pg_db = "test_db"
    config.pg_schema = "public"
    
    # Migration settings
    config.batch_size = 1000
    config.temp_schema = "migration_temp"
    
    # Logging settings
    config.log_file = "test_migration.log"
    config.db_metrics_log_file = "test_db_metrics.log"
    
    # Metrics settings
    config.enable_db_metrics = True
    config.db_metrics_slow_ms = 100
    
    # API settings
    config.api_enabled = False
    config.requests_per_second = 5
    
    # OPCO settings
    config.opco_enabled = False
    config.opco_resource_id = ""
    
    return config


@pytest.fixture
def real_config() -> Config:
    """
    Load the real Config object from environment.
    
    Returns:
        Real Config instance loaded from .env
    """
    return Config()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def mock_cursor() -> Mock:
    """
    Create a mock database cursor.
    
    Returns:
        Mock cursor with common database operations
    """
    cursor = Mock()
    cursor.fetchall.return_value = []
    cursor.fetchone.return_value = None
    cursor.rowcount = 0
    cursor.description = None
    return cursor


@pytest.fixture
def mock_cursor_with_columns() -> Mock:
    """
    Create a mock cursor that returns column information.
    
    Returns:
        Mock cursor configured for column queries
    """
    cursor = Mock()
    cursor.fetchall.return_value = [
        ("id",), ("name",), ("email",), ("created_at",)
    ]
    return cursor


@pytest.fixture
def mock_pg_cursor_with_columns() -> Mock:
    """
    Create a mock PostgreSQL cursor with column type information.
    
    Returns:
        Mock cursor configured for PostgreSQL column queries
    """
    cursor = Mock()
    cursor.fetchall.return_value = [
        ("id", "integer"),
        ("name", "character varying"),
        ("email", "character varying"),
        ("created_at", "timestamp without time zone")
    ]
    return cursor


@pytest.fixture
def mock_connection(mock_cursor: Mock) -> Mock:
    """
    Create a mock database connection.
    
    Args:
        mock_cursor: Mock cursor to return from cursor() calls
    
    Returns:
        Mock connection with cursor, commit, and rollback
    """
    connection = Mock()
    connection.cursor.return_value = mock_cursor
    return connection


@pytest.fixture
def mock_mariadb_connection(mock_cursor: Mock) -> Mock:
    """
    Create a mock MariaDB connection.
    
    Args:
        mock_cursor: Mock cursor to return from cursor() calls
    
    Returns:
        Mock MariaDB connection
    """
    connection = Mock()
    connection.cursor.return_value = mock_cursor
    connection.cursor.return_value.connection = connection
    return connection


@pytest.fixture
def mock_pg_connection(mock_cursor: Mock) -> Mock:
    """
    Create a mock PostgreSQL connection.
    
    Args:
        mock_cursor: Mock cursor to return from cursor() calls
    
    Returns:
        Mock PostgreSQL connection
    """
    connection = Mock()
    connection.cursor.return_value = mock_cursor
    return connection


# ============================================================================
# Logging Fixtures
# ============================================================================

@pytest.fixture
def mock_logger() -> Mock:
    """
    Create a mock logger.
    
    Returns:
        Mock logger with standard logging methods
    """
    logger = Mock(spec=logging.Logger)
    return logger


@pytest.fixture
def temp_log_file(tmp_path) -> str:
    """
    Create a temporary log file path.
    
    Args:
        tmp_path: pytest temporary path fixture
    
    Returns:
        Path to temporary log file
    """
    return str(tmp_path / "test.log")


@pytest.fixture
def cleanup_loggers():
    """
    Fixture to clean up loggers after tests.
    
    Yields control to test, then cleans up logging handlers.
    """
    yield
    
    # Clean up all handlers from migration loggers
    for logger_name in ["migration", "migration.db"]:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)


# ============================================================================
# Metrics Fixtures
# ============================================================================

@pytest.fixture
def mock_metrics() -> Mock:
    """
    Create a mock MariaDBMetrics object.
    
    Returns:
        Mock metrics object with recording methods
    """
    metrics = Mock(spec=MariaDBMetrics)
    metrics.slow_ms = 100
    metrics.total_queries = 0
    metrics.total_time_s = 0.0
    metrics.ops_count = {}
    metrics.ops_time_s = {}
    metrics.slow_queries = []
    
    return metrics


@pytest.fixture
def real_metrics() -> MariaDBMetrics:
    """
    Create a real MariaDBMetrics object for testing.
    
    Returns:
        Real MariaDBMetrics instance
    """
    return MariaDBMetrics(slow_ms=100)


# ============================================================================
# API Fixtures
# ============================================================================

@pytest.fixture
def mock_api_response() -> Mock:
    """
    Create a mock API response.
    
    Returns:
        Mock response with status_code and json methods
    """
    response = Mock()
    response.status_code = 200
    response.json.return_value = {}
    response.text = ""
    response.ok = True
    return response


@pytest.fixture
def mock_api_session(mock_api_response: Mock) -> Mock:
    """
    Create a mock requests session.
    
    Args:
        mock_api_response: Mock response to return from requests
    
    Returns:
        Mock session for API testing
    """
    session = Mock()
    session.request.return_value = mock_api_response
    session.get.return_value = mock_api_response
    session.post.return_value = mock_api_response
    return session


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_table_data() -> list:
    """
    Provide sample table data for testing.
    
    Returns:
        List of sample rows
    """
    return [
        (1, "John Doe", "john@example.com"),
        (2, "Jane Smith", "jane@example.com"),
        (3, "Bob Wilson", "bob@example.com"),
    ]


@pytest.fixture
def sample_enterprise_data() -> list:
    """
    Provide sample enterprise data for testing.
    
    Returns:
        List of sample enterprise rows
    """
    return [
        (1, "12345678901234", "Enterprise A", "Paris"),
        (2, "98765432109876", "Enterprise B", "Lyon"),
    ]


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_directory(tmp_path) -> str:
    """
    Provide a temporary directory path.
    
    Args:
        tmp_path: pytest temporary path fixture
    
    Returns:
        String path to temporary directory
    """
    return str(tmp_path)


@pytest.fixture
def cleanup_temp_files(tmp_path):
    """
    Fixture to ensure temporary files are cleaned up.
    
    Args:
        tmp_path: pytest temporary path fixture
    
    Yields:
        Path to use, then cleans up
    """
    yield tmp_path
    
    # Clean up any remaining files
    for file in tmp_path.iterdir():
        if file.is_file():
            file.unlink()
