"""
Superset Configuration for FormaSup BI - 100% French Interface
===================================================================

This configuration file overrides the default Superset settings.
All settings here take precedence over superset/config.py

Key features:
- French language by default (BABEL_DEFAULT_LOCALE = "fr")
- French date/number formats (D3_FORMAT, D3_TIME_FORMAT)
- Security best practices (CSRF, rate limiting)
- Production-ready cache configuration
- Translation fix for Superset 6.0.0 bug #35569
"""

from __future__ import annotations

import os
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

# =============================================================================
# SECURITY
# =============================================================================

# Secret key for session signing - MUST be set via environment variable
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY")

# CSRF protection
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = [
    "superset.charts.data.api.data",
    "superset.dashboards.api.cache_dashboard_screenshot",
]

# Rate limiting for production
RATELIMIT_ENABLED = os.environ.get("SUPERSET_ENV") == "production"
RATELIMIT_APPLICATION = "50 per second"
AUTH_RATE_LIMITED = True
AUTH_RATE_LIMIT = "5 per second"

# Proxy configuration (enable if behind nginx/reverse proxy)
ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {"x_for": 1, "x_proto": 1, "x_host": 1, "x_port": 0, "x_prefix": 1}

# Hide stacktraces in production
SHOW_STACKTRACE = os.environ.get("SUPERSET_ENV") != "production"

# =============================================================================
# DATABASE
# =============================================================================

SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Database connection pool settings for production
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_size": 10,
    "pool_recycle": 3600,
    "pool_pre_ping": True,
}

# =============================================================================
# WEBSERVER
# =============================================================================

# Timeout settings - should be lower than reverse proxy timeout
SUPERSET_WEBSERVER_TIMEOUT = int(timedelta(minutes=1).total_seconds())

# Row limits
ROW_LIMIT = 50000
SAMPLES_ROW_LIMIT = 1000
FILTER_SELECT_ROW_LIMIT = 10000

# =============================================================================
# BRANDING
# =============================================================================

# Legacy branding (kept for compatibility)
APP_NAME = "FormaSup BI"
APP_ICON = "/static/assets/images/logo.png"
LOGO_TARGET_PATH = "/superset/welcome"
LOGO_TOOLTIP = "Accueil FormaSup BI"
LOGO_RIGHT_TEXT = ""

# Custom favicon
FAVICONS = [{"href": "/static/assets/images/favicon.ico"}]

# =============================================================================
# THEMING (Superset 6.0.0+ branding via theme system)
# =============================================================================
# In Superset 6.0.0, APP_ICON is deprecated. Branding is now managed through
# the theming system using THEME_DEFAULT. See: https://github.com/apache/superset/issues/36940

THEME_DEFAULT = {
    "algorithm": "default",
    "token": {
        "brandLogoUrl": "/static/assets/images/logo.png",
        "brandLogoAlt": "FormaSup BI",
        "brandLogoHeight": "40px",
        "brandLogoMargin": "10px 10px 10px 0px",
        "brandIconMaxWidth": 150,
        "brandSpinnerUrl": "/static/assets/images/loading.gif",
    },
}

THEME_DARK = {
    "algorithm": "dark",
    "token": {
        "brandLogoUrl": "/static/assets/images/logo.png",
        "brandLogoAlt": "FormaSup BI",
        "brandLogoHeight": "40px",
        "brandLogoMargin": "10px 10px 10px 0px",
        "brandIconMaxWidth": 150,
        "brandSpinnerUrl": "/static/assets/images/loading.gif",
    },
}

# =============================================================================
# FRENCH LANGUAGE - Main Configuration
# =============================================================================

# Single language = no selector, French forced
LANGUAGES = {
    "fr": {"flag": "fr", "name": "Francais"},
}

# Babel configuration
BABEL_DEFAULT_LOCALE = "fr"
BABEL_DEFAULT_FOLDER = "superset/translations"

# =============================================================================
# FRENCH DATE/NUMBER FORMATS (D3.js localization)
# =============================================================================

D3_TIME_FORMAT = {
    "dateTime": "%A %e %B %Y a %X",
    "date": "%d/%m/%Y",
    "time": "%H:%M:%S",
    "periods": ["", ""],
    "days": ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"],
    "shortDays": ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"],
    "months": [
        "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
        "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"
    ],
    "shortMonths": [
        "Jan", "Fev", "Mar", "Avr", "Mai", "Juin",
        "Juil", "Aout", "Sep", "Oct", "Nov", "Dec"
    ],
}

D3_FORMAT = {
    "decimal": ",",
    "thousands": " ",
    "grouping": [3],
    "currency": ["", " EUR"],
}

CURRENCIES = ["EUR", "USD", "GBP"]

# =============================================================================
# FEATURE FLAGS
# =============================================================================

FEATURE_FLAGS = {
    # Dashboard features
    "DASHBOARD_NATIVE_FILTERS": True,
    "HORIZONTAL_FILTER_BAR": True,
    "DASHBOARD_RBAC": True,
    "DASHBOARD_VIRTUALIZATION": True,
    
    # Drill features
    "DRILL_TO_DETAIL": True,
    "DRILL_BY": True,
    
    # Export features
    "ALLOW_FULL_CSV_EXPORT": True,
    
    # SQL Lab
    "SQLLAB_BACKEND_PERSISTENCE": True,
    
    # UI preferences
    "LISTVIEWS_DEFAULT_CARD_VIEW": True,
    "DATAPANEL_CLOSED_BY_DEFAULT": False,
    "FILTERBAR_CLOSED_BY_DEFAULT": False,
    
    # Security
    "EMBEDDABLE_CHARTS": False,
    "EMBEDDED_SUPERSET": False,
    
    # Advanced features (disabled by default)
    "ENABLE_TEMPLATE_PROCESSING": False,
    "ENABLE_JAVASCRIPT_CONTROLS": False,
    "TAGGING_SYSTEM": False,
    "THUMBNAILS": False,
    "ALERT_REPORTS": False,
}

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes

# Filter state cache
FILTER_STATE_CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_NO_NULL_WARNING": True,
}

# Explore form data cache
EXPLORE_FORM_DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_NO_NULL_WARNING": True,
}

# Data cache (for chart queries)
DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_NO_NULL_WARNING": True,
}

# =============================================================================
# TRANSLATION FIX 6.0.0 - Workaround for issue #35569
# Asynchronous loading of language packs (PR #34119) causes a race condition
# This function forces the loading of the French language pack into the bootstrap
# =============================================================================


def COMMON_BOOTSTRAP_OVERRIDES_FUNC(bootstrap_data: dict) -> dict:
    """
    Workaround for the partial translations bug in Superset 6.0.0.
    
    Loads the French language pack directly into the bootstrap data
    to avoid the race condition of asynchronous loading.
    
    Args:
        bootstrap_data: The bootstrap data dictionary
        
    Returns:
        Modified bootstrap data with language pack included
    """
    try:
        from superset.translations.utils import get_language_pack
        
        locale = bootstrap_data.get("common", {}).get("locale", "fr")
        if locale == "fr":
            language_pack = get_language_pack("fr")
            if language_pack:
                if "common" not in bootstrap_data:
                    bootstrap_data["common"] = {}
                bootstrap_data["common"]["language_pack"] = language_pack
                logger.info("French language pack loaded via bootstrap override")
    except Exception as e:
        logger.warning(f"Error loading language pack: {e}")
    
    return bootstrap_data


# =============================================================================
# FLASK APP MUTATOR - Permissions and custom setup
# =============================================================================


def FLASK_APP_MUTATOR(app):
    """
    Custom Flask app configuration.
    
    - Adds language pack permission to Public/Gamma roles
    - Configures cache headers for translation endpoints
    
    Args:
        app: The Flask application instance
    """
    @app.after_request
    def add_cache_headers(response):
        # Disable cache on translation endpoints for fresh translations
        request_path = response.headers.get("Location", "")
        if "/language_pack/" in request_path or "/api/v1/common/" in request_path:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return response

    with app.app_context():
        try:
            from superset import security_manager
            from superset.extensions import db

            # Find the language pack permission
            perm = security_manager.find_permission_view_menu(
                "can_language_pack", "Superset"
            )

            if perm:
                # Add permission to Public and Gamma roles
                for role_name in ["Public", "Gamma"]:
                    role = security_manager.find_role(role_name)
                    if role and perm not in role.permissions:
                        role.permissions.append(perm)
                        logger.info(
                            f"Permission 'can_language_pack' added to role {role_name}"
                        )

                db.session.commit()
        except Exception as e:
            logger.warning(f"Language pack permission configuration error: {e}")


# =============================================================================
# STARTUP LOG
# =============================================================================

logger.info("FormaSup BI configuration loaded successfully")
logger.info(f"  - Language: {BABEL_DEFAULT_LOCALE}")
logger.info(f"  - App Name: {APP_NAME}")
logger.info(f"  - CSRF Enabled: {WTF_CSRF_ENABLED}")

