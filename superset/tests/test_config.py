#!/usr/bin/env python3
"""
Tests for Superset FormaSup configuration.
"""

import pytest
import os
from unittest.mock import patch

# Import configuration (must be in PYTHONPATH)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config.superset_config import (
    SECRET_KEY, WTF_CSRF_ENABLED, SQLALCHEMY_DATABASE_URI,
    APP_NAME, APP_ICON, LOGO_TARGET_PATH, LOGO_TOOLTIP, LOGO_RIGHT_TEXT,
    LANGUAGES, BABEL_DEFAULT_LOCALE
)


class TestSupersetConfig:
    """Tests for Superset configuration."""

    def test_secret_key_configuration(self):
        """Test secret key configuration."""
        # With environment variable
        with patch.dict(os.environ, {'SUPERSET_SECRET_KEY': 'test_secret_key'}):
            # Reload module to apply new value
            import importlib
            import config.superset_config as config_module
            importlib.reload(config_module)

            assert config_module.SECRET_KEY == 'test_secret_key'

    def test_secret_key_default(self):
        """Test SECRET_KEY behavior without environment variable."""
        # Without environment variable, SECRET_KEY should be None
        # This forces explicit configuration in production
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import config.superset_config as config_module
            importlib.reload(config_module)

            # SECRET_KEY is None when not set (security: forces explicit config)
            assert config_module.SECRET_KEY is None

    def test_csrf_enabled(self):
        """Test that CSRF is enabled."""
        assert WTF_CSRF_ENABLED is True

    def test_database_uri_configuration(self):
        """Test database URI configuration."""
        # With environment variable
        test_uri = 'postgresql://test:test@localhost/test_db'
        with patch.dict(os.environ, {'DATABASE_URL': test_uri}):
            import importlib
            import config.superset_config as config_module
            importlib.reload(config_module)

            assert config_module.SQLALCHEMY_DATABASE_URI == test_uri

    def test_database_uri_default(self):
        """Test DATABASE_URL behavior without environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import config.superset_config as config_module
            importlib.reload(config_module)

            # DATABASE_URL is None when not set (secure default)
            assert config_module.SQLALCHEMY_DATABASE_URI is None

    def test_app_branding(self):
        """Test application branding configuration."""
        assert APP_NAME == "FormaSup BI"
        assert APP_ICON == "/static/assets/images/logo.png"
        assert LOGO_TARGET_PATH == "/superset/welcome"
        assert LOGO_TOOLTIP == "Accueil FormaSup BI"
        assert LOGO_RIGHT_TEXT == ""

    def test_language_configuration(self):
        """Test French language configuration."""
        # Verify that only French is configured
        assert len(LANGUAGES) == 1
        assert "fr" in LANGUAGES

        french_config = LANGUAGES["fr"]
        assert french_config["flag"] == "fr"
        assert french_config["name"] == "Francais"

    def test_babel_configuration(self):
        """Test Babel configuration for French."""
        assert BABEL_DEFAULT_LOCALE == "fr"

    @patch('config.superset_config.logging.getLogger')
    def test_logger_initialization(self, mock_get_logger):
        """Test logger initialization."""
        mock_logger = mock_get_logger.return_value

        # Reload module to trigger initialization
        import importlib
        import config.superset_config as config_module
        importlib.reload(config_module)

        # Verify that getLogger was called with the config module name
        mock_get_logger.assert_called_with('config.superset_config')


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_config_values_are_strings_or_expected_types(self):
        """Test that configuration values have expected types."""
        # SECRET_KEY can be None (when env var not set) or string
        assert SECRET_KEY is None or isinstance(SECRET_KEY, str)

        # Booleans
        assert isinstance(WTF_CSRF_ENABLED, bool)

        # Strings (may be None when env vars not set)
        assert SQLALCHEMY_DATABASE_URI is None or isinstance(SQLALCHEMY_DATABASE_URI, str)
        assert isinstance(APP_NAME, str)
        assert isinstance(APP_ICON, str)
        assert isinstance(LOGO_TARGET_PATH, str)
        assert isinstance(LOGO_TOOLTIP, str)
        assert isinstance(LOGO_RIGHT_TEXT, str)
        assert isinstance(BABEL_DEFAULT_LOCALE, str)

        # Language dictionary
        assert isinstance(LANGUAGES, dict)
        assert all(isinstance(k, str) for k in LANGUAGES.keys())
        assert all(isinstance(v, dict) for v in LANGUAGES.values())

    def test_database_uri_format(self):
        """Test database URI format when set."""
        uri = SQLALCHEMY_DATABASE_URI

        # Skip test if URI is not set (None when env var missing)
        if uri is None:
            pytest.skip("DATABASE_URL not set in environment")

        # Must start with postgresql://
        assert uri.startswith('postgresql://')

        # Must contain connection info
        assert '@' in uri  # user:password@
        assert ':' in uri  # host:port
        assert '/' in uri  # /database

    def test_french_locale_settings(self):
        """Test that all locale settings are French."""
        # Default locale
        assert BABEL_DEFAULT_LOCALE == "fr"

        # French language in configuration
        assert "fr" in LANGUAGES
        assert LANGUAGES["fr"]["name"] == "Francais"


class TestConfigEnvironmentIsolation:
    """Tests for environment variable isolation."""

    def test_config_does_not_modify_environment(self):
        """Test that configuration does not modify the environment."""
        original_env = os.environ.copy()

        # Load configuration
        import importlib
        import config.superset_config as config_module
        importlib.reload(config_module)

        # Verify that environment has not changed
        assert os.environ == original_env

    def test_config_handles_missing_env_vars(self):
        """Test that configuration handles missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            import importlib
            import config.superset_config as config_module
            importlib.reload(config_module)

            # SECRET_KEY and DATABASE_URL are None when not set (secure default)
            # This forces explicit configuration in production
            # Other values should have defaults
            assert config_module.APP_NAME is not None
            assert config_module.BABEL_DEFAULT_LOCALE == "fr"


if __name__ == "__main__":
    pytest.main([__file__])