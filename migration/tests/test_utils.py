#!/usr/bin/env python3
"""
Tests for utilities (logger, API, etc.).
"""

import pytest
import logging
import os
from unittest.mock import Mock, patch

from logger import setup_logger, setup_db_logger
from api_client import RateLimitedAPI


class TestLogger:
    """Tests for logging system."""

    def test_setup_logger_returns_logger(self, temp_log_file, cleanup_loggers):
        """Test that setup_logger returns a logger."""
        logger = setup_logger(temp_log_file)
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "migration"
        assert logger.level == logging.INFO

    def test_setup_db_logger_returns_logger(self, temp_log_file, cleanup_loggers):
        """Test that setup_db_logger returns a logger."""
        db_logger = setup_db_logger(temp_log_file)
        
        assert isinstance(db_logger, logging.Logger)
        assert db_logger.name == "migration.db"
        assert db_logger.propagate is False

    def test_logger_no_duplicate_handlers(self, temp_log_file, cleanup_loggers):
        """Test that handlers are not duplicated."""
        # Call twice
        logger1 = setup_logger(temp_log_file)
        initial_handlers = len(logger1.handlers)
        
        logger2 = setup_logger(temp_log_file)
        
        # Should have same number of handlers
        assert len(logger2.handlers) == initial_handlers
        assert logger1 is logger2  # Same instance


class TestRateLimitedAPI:
    """Tests for API client with rate limiting."""

    def test_api_client_initialization(self):
        """Test API client initialization."""
        client = RateLimitedAPI(requests_per_second=5)

        assert client.requests_per_second == 5
        assert client.min_interval == 0.2  # 1/5
        assert client.last_request_time == 0
        assert client.session is not None

    def test_api_client_min_interval(self):
        """Test minimum interval calculation."""
        client1 = RateLimitedAPI(requests_per_second=10)
        assert client1.min_interval == 0.1
        
        client2 = RateLimitedAPI(requests_per_second=2)
        assert client2.min_interval == 0.5

    def test_api_client_has_session(self):
        """Test that client has HTTP session."""
        client = RateLimitedAPI(requests_per_second=5)
        
        assert hasattr(client, 'session')
        assert client.session is not None

    def test_api_client_has_lock(self):
        """Test that client has lock for threading."""
        client = RateLimitedAPI(requests_per_second=5)
        
        assert hasattr(client, 'lock')

    @patch('api_client.requests.Session')
    def test_api_request_method(self, mock_session_class, mock_api_session, mock_api_response):
        """Test request method."""
        mock_session_class.return_value = mock_api_session
        
        client = RateLimitedAPI(requests_per_second=5)
        # Replace session with our mock
        client.session = mock_api_session
        
        result = client.request("GET", "https://api.example.com/test")
        
        assert result == mock_api_response
        mock_api_session.request.assert_called_once()


class TestAPIClientRetry:
    """Tests for retry strategy."""

    def test_session_has_retry_adapter(self):
        """Test that session has retry adapter."""
        client = RateLimitedAPI(requests_per_second=5)
        
        # Verify HTTPS adapter is configured
        adapters = client.session.adapters
        assert "https://" in adapters


if __name__ == "__main__":
    pytest.main([__file__])