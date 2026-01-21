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
LOGO_TOOLTIP = "Accueil"
LOGO_RIGHT_TEXT = ""

# Custom favicon
FAVICONS = [{"href": "/static/assets/images/favicon.ico"}]

# =============================================================================
# THEMING (Superset 6.0.0+ branding via theme system)
# =============================================================================
# In Superset 6.0.0, APP_ICON is deprecated. Branding is now managed through
# the theming system using THEME_DEFAULT. See: https://github.com/apache/superset/issues/36940
#
# FormaSup color palette:
# - Primary (dark blue): #134169
# - Secondary (light blue): #7EB0C1
# - Accent (gold): #f3be72

THEME_DEFAULT = {
    "algorithm": "default",
    "token": {
        # Custom font - BoosterNextFY (self-hosted)
        "fontUrls": [
            "/static/assets/fonts/booster-next-fy.css",
        ],
        "fontFamily": "'BoosterNextFY', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        "fontFamilyCode": "'Fira Code', 'Monaco', 'Consolas', monospace",

        # Branding (Superset-specific tokens)
        "brandLogoUrl": "/static/assets/images/logo.png",
        "brandLogoAlt": "FormaSup BI",
        "brandLogoHeight": "40px",
        "brandLogoMargin": "5px 5px 5px 0px",
        "brandIconMaxWidth": 150,
        "brandSpinnerUrl": "/static/assets/images/loading.gif",

        # Primary color palette
        "colorPrimary": "#134169",
        "colorPrimaryBg": "#e8f4f7",
        "colorPrimaryBgHover": "#d1e9ef",
        "colorPrimaryBorder": "#134169",
        "colorPrimaryBorderHover": "#0f3457",
        "colorPrimaryHover": "#0f3457",
        "colorPrimaryActive": "#0a2239",
        "colorPrimaryText": "#134169",
        "colorPrimaryTextHover": "#0f3457",
        "colorPrimaryTextActive": "#0a2239",

        # Info color palette (Secondary blue)
        "colorInfo": "#7EB0C1",
        "colorInfoBg": "#e8f4f7",
        "colorInfoBgHover": "#d1e9ef",
        "colorInfoBorder": "#7EB0C1",
        "colorInfoBorderHover": "#5a9fb3",
        "colorInfoHover": "#5a9fb3",
        "colorInfoActive": "#4a8fa3",
        "colorInfoText": "#7EB0C1",
        "colorInfoTextHover": "#5a9fb3",
        "colorInfoTextActive": "#4a8fa3",

        # Warning color palette (Accent gold)
        "colorWarning": "#f3be72",
        "colorWarningBg": "#fdf5e6",
        "colorWarningBgHover": "#fbe8c7",
        "colorWarningBorder": "#f3be72",
        "colorWarningBorderHover": "#f0ad4e",
        "colorWarningHover": "#f0ad4e",
        "colorWarningActive": "#e79d31",
        "colorWarningText": "#f3be72",
        "colorWarningTextHover": "#f0ad4e",
        "colorWarningTextActive": "#e79d31",

        # Text colors
        "colorTextBase": "#2d3748",
        "colorText": "#134169",
        "colorTextSecondary": "#4a5568",
        "colorTextTertiary": "#718096",
        "colorTextQuaternary": "#a0aec0",

        # Background colors
        "colorBgBase": "#ffffff",
        "colorBgContainer": "#ffffff",
        "colorBgElevated": "#ffffff",
        "colorBgLayout": "#ffffff",

        # Border colors
        "colorBorder": "#7EB0C1",
        "colorBorderSecondary": "#7EB0C1",

        # Border radius
        "borderRadius": 6,
        "borderRadiusXS": 2,
        "borderRadiusSM": 4,
        "borderRadiusLG": 8,

        # Spacing
        "padding": 16,
        "paddingSM": 12,
        "paddingLG": 20,
        "margin": 16,
        "marginSM": 12,
        "marginLG": 20,

        # Shadows
        "boxShadow": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
        "boxShadowSecondary": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    },
}

# Disable dark mode and theme switching
# Setting THEME_DARK = None forces light theme only (no switcher shown)
THEME_DARK = None

# Disable UI theme administration
ENABLE_UI_THEME_ADMINISTRATION = False

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

CURRENCIES = ["EUR"]

# =============================================================================
# FEATURE FLAGS
# =============================================================================

FEATURE_FLAGS = {
    # Dashboard features
    "DASHBOARD_NATIVE_FILTERS": True,
    "HORIZONTAL_FILTER_BAR": True,
    "DASHBOARD_RBAC": True,  # Required for dashboard-only access
    "DASHBOARD_VIRTUALIZATION": True,

    # Drill features
    "DRILL_TO_DETAIL": True,
    "DRILL_BY": True,

    # Export features
    "ALLOW_FULL_CSV_EXPORT": True,

    # SQL Lab - disabled for non-admin users via role permissions
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
# DASHBOARD-ONLY ACCESS FOR NON-ADMIN USERS
# =============================================================================
# This configuration restricts non-admin users to only view dashboards.
# - Users are redirected to their dashboard after login
# - Navigation menu is simplified (no SQL Lab, no Chart creation, etc.)
# - Only Admin role has full access

# Menu items visible to dashboard-only users (Viewer role)
# Admin users will see the full menu
MENU_HIDE_USER_INFO_ITEMS = [
    "Security",
    "List Users",
    "List Roles",
]

# Require authentication: disable anonymous (Public) access
# Hides Superset UI and menu for non-logged-in users
PUBLIC_ROLE_NAME = None

# Do not grant Public role permissions
PUBLIC_ROLE_LIKE = None


# Custom security manager to enforce dashboard-only access
class FormaSupersetSecurityManager:
    """
    Custom configuration for role-based access control.

    Role hierarchy:
    - Admin: Full access to everything
    - Viewer: Dashboard access only (no SQL Lab, no chart creation)
    """
    pass


# Role configuration for dashboard-only access
# These permissions should be configured via Superset UI:
# Settings > List Roles > Create "Viewer" role with only:
# - can read on Dashboard
# - can read on DashboardFilterStateRestApi
# - can read on DashboardPermalinkRestApi
# - datasource access on [database].[schema].[table] (for filters)
# - can_language_pack on Superset

# After login, redirect non-admin users to dashboard list
# Admin detection is done in FLASK_APP_MUTATOR below

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
    - Redirects non-admin users to dashboard list after login

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

    # Redirect non-admin users to dashboard list after login
    @app.after_request
    def redirect_non_admin_to_dashboards(response):
        """Redirect non-admin users to dashboard list instead of welcome page."""
        from flask import request, redirect, g
        from flask_login import current_user

        # Only intercept redirects to welcome page after successful login
        if (response.status_code == 302 and
            response.headers.get("Location", "").endswith("/superset/welcome/")):
            try:
                if current_user.is_authenticated:
                    # Check if user is NOT admin
                    user_roles = [role.name for role in current_user.roles]
                    if "Admin" not in user_roles:
                        # Redirect to dashboard list instead
                        return redirect("/dashboard/list/")
            except Exception:
                pass
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

            # Create Viewer role if it does not exist
            viewer_role = security_manager.find_role("Viewer")
            if not viewer_role:
                viewer_role = security_manager.add_role("Viewer")
                logger.info("Created 'Viewer' role for dashboard-only access")

                # Add basic dashboard permissions to Viewer role
                dashboard_perms = [
                    ("can_read", "Dashboard"),
                    ("can_read", "DashboardFilterStateRestApi"),
                    ("can_read", "DashboardPermalinkRestApi"),
                    ("can_dashboard", "Superset"),
                    ("can_explore_json", "Superset"),
                    ("can_slice", "Superset"),
                    ("can_language_pack", "Superset"),
                ]

                for perm_name, view_name in dashboard_perms:
                    perm = security_manager.find_permission_view_menu(perm_name, view_name)
                    if perm and perm not in viewer_role.permissions:
                        viewer_role.permissions.append(perm)

                db.session.commit()
                logger.info("Viewer role permissions configured")

        except Exception as e:
            logger.warning(f"Role/permission configuration error: {e}")


# =============================================================================
# CUSTOM FONTS
# =============================================================================

# Custom font configuration
# Load external fonts at runtime without rebuilding the application
# For local fonts, use the path to your CSS file
CUSTOM_FONT_URLS = [
    "/static/assets/fonts/booster-next-fy.css",
]


# =============================================================================
# STARTUP LOG
# =============================================================================

logger.info("FormaSup BI configuration loaded successfully")
logger.info(f"  - Language: {BABEL_DEFAULT_LOCALE}")
logger.info(f"  - App Name: {APP_NAME}")
logger.info(f"  - CSRF Enabled: {WTF_CSRF_ENABLED}")

