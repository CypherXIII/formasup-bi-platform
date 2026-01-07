"""
Superset Configuration for FormaSup BI - 100% French Interface
===================================================================

According to the official Superset documentation, all that is needed is:
- BABEL_DEFAULT_LOCALE = "fr" 
- LANGUAGES = {"fr": {"flag": "fr", "name": "Français"}}

Translations are compiled during the Docker build with BUILD_TRANSLATIONS=true
"""

import os
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# SECURITY
# =============================================================================
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY')
WTF_CSRF_ENABLED = True

# =============================================================================
# DATABASE
# =============================================================================
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

# =============================================================================
# BRANDING
# =============================================================================
APP_NAME = "FormaSup BI"
APP_ICON = "/static/assets/images/logo.png"
LOGO_TARGET_PATH = "/superset/welcome"
LOGO_TOOLTIP = "Home"
LOGO_RIGHT_TEXT = ""

# =============================================================================
# FRENCH LANGUAGE - Main Configuration (official doc)
# =============================================================================

# A single language = no selector, French forced
LANGUAGES = {
    "fr": {"flag": "fr", "name": "Français"},
}

# Babel configuration - This is all that is needed according to the official doc
BABEL_DEFAULT_LOCALE = "fr"
BABEL_DEFAULT_TIMEZONE = "Europe/Paris"

# =============================================================================
# FRENCH DATE/NUMBER FORMATS
# =============================================================================
D3_TIME_FORMAT = {
    "dateTime": "%d/%m/%Y, %H:%M:%S",
    "date": "%d/%m/%Y",
    "time": "%H:%M:%S",
    "periods": ["AM", "PM"],
    "days": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    "shortDays": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
    "months": ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"],
    "shortMonths": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
}

D3_FORMAT = {
    "decimal": ",",
    "thousands": " ",
    "grouping": [3],
    "currency": ["", " €"]
}

CURRENCIES = ["EUR"]

# =============================================================================
# FEATURE FLAGS
# =============================================================================
FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "HORIZONTAL_FILTER_BAR": True,
    "DASHBOARD_RBAC": True,
    "DRILL_TO_DETAIL": True,
    "DRILL_BY": True,
    "ALLOW_FULL_CSV_EXPORT": True,
    "EMBEDDABLE_CHARTS": False,
    "SQLLAB_BACKEND_PERSISTENCE": True,
    "LISTVIEWS_DEFAULT_CARD_VIEW": True,
}

# =============================================================================
# CACHE
# =============================================================================
CACHE_DEFAULT_TIMEOUT = 300
FILTER_STATE_CACHE_CONFIG = {'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300}
EXPLORE_FORM_DATA_CACHE_CONFIG = {'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': 300}

# =============================================================================
# TRANSLATION FIX 6.0.0 - Workaround for issue #35569
# Asynchronous loading of language packs (PR #34119) causes a race condition
# This function forces the loading of the French language pack into the bootstrap
# =============================================================================
def COMMON_BOOTSTRAP_OVERRIDES_FUNC(bootstrap_data):
    """
    Workaround for the partial translations bug in Superset 6.0.0
    Loads the French language pack directly into the bootstrap data
    to avoid the race condition of asynchronous loading.
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
                logger.info("French language pack loaded via COMMON_BOOTSTRAP_OVERRIDES_FUNC")
    except Exception as e:
        logger.warning(f"Error loading language pack: {e}")
    return bootstrap_data

# =============================================================================
# PERMISSIONS - Add language_pack permission to the Public role
# =============================================================================
def FLASK_APP_MUTATOR(app):
    """
    Adds the 'can language pack Superset' permission to the Public and Gamma roles
    to allow non-admin users to access translations.
    """
    @app.after_request
    def add_header(response):
        # Disable cache on translation endpoints
        if '/language_pack/' in response.headers.get('Location', '') or \
           '/api/v1/common/' in response.headers.get('Location', ''):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    with app.app_context():
        try:
            from superset import security_manager
            from superset.extensions import db
            
            # Find or create the permission
            perm = security_manager.find_permission_view_menu(
                'can_language_pack', 'Superset'
            )
            
            if perm:
                # Add to Public and Gamma roles
                for role_name in ['Public', 'Gamma']:
                    role = security_manager.find_role(role_name)
                    if role and perm not in role.permissions:
                        role.permissions.append(perm)
                        logger.info(f"Permission 'can language pack' added to role {role_name}")
                
                db.session.commit()
        except Exception as e:
            logger.warning(f"Language pack permission configuration error: {e}")

logger.info("FormaSup BI configuration loaded - Language: French")

