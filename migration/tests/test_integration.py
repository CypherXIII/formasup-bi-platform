#!/usr/bin/env python3
"""
Integration tests for migration system.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from config import Config, TABLE_ORDER


class TestConfigIntegration:
    """Integration tests for configuration."""

    def test_config_loads_from_env(self):
        """Test that config loads from .env."""
        config = Config()
        
        # Values should be loaded (from .env or defaults)
        assert config.mariadb_host is not None
        assert config.pg_host is not None

    def test_config_has_table_order(self):
        """Test that TABLE_ORDER is defined."""
        assert TABLE_ORDER is not None
        assert isinstance(TABLE_ORDER, (list, tuple))

    def test_config_batch_size_positive(self):
        """Test that batch_size is positive."""
        config = Config()
        assert config.batch_size > 0

    def test_config_ports_valid(self):
        """Test that ports are valid."""
        config = Config()
        assert 0 < config.mariadb_port < 65536


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_config_validation_comprehensive(self):
        """Comprehensive configuration validation test."""
        config = Config()
        
        # If config has values, it should be valid
        if config.mariadb_host and config.pg_host:
            # Should not raise exception
            config.validate()

    def test_config_optional_fields(self):
        """Test that optional fields have defaults."""
        config = Config()
        
        # These fields should have default values
        assert config.temp_schema is not None
        assert config.log_file is not None
        assert config.db_metrics_log_file is not None


class TestTableOrder:
    """Tests for table order."""

    def test_table_order_not_empty(self):
        """Test that TABLE_ORDER is not empty."""
        assert len(TABLE_ORDER) > 0

    def test_table_order_unique(self):
        """Test that tables are unique."""
        assert len(TABLE_ORDER) == len(set(TABLE_ORDER))

    def test_table_order_strings(self):
        """Test that elements are strings."""
        for table in TABLE_ORDER:
            assert isinstance(table, str)
            assert len(table) > 0


class TestConfigMetrics:
    """Tests for metrics configuration."""

    def test_metrics_config_types(self):
        """Test metrics configuration types."""
        config = Config()
        
        assert isinstance(config.enable_db_metrics, bool)
        assert isinstance(config.db_metrics_slow_ms, int)
        assert config.db_metrics_slow_ms > 0

    def test_api_config_types(self):
        """Test API configuration types."""
        config = Config()
        
        assert isinstance(config.api_enabled, bool)
        assert isinstance(config.requests_per_second, int)
        assert config.requests_per_second > 0


class TestConfigOPCO:
    """Tests for OPCO configuration."""

    def test_opco_config_exists(self):
        """Test that OPCO config exists."""
        config = Config()
        
        assert hasattr(config, 'opco_enabled')
        assert hasattr(config, 'opco_resource_id')

    def test_opco_config_types(self):
        """Test OPCO configuration types."""
        config = Config()
        
        assert isinstance(config.opco_enabled, bool)
        assert isinstance(config.opco_resource_id, str)


if __name__ == "__main__":
    pytest.main([__file__])