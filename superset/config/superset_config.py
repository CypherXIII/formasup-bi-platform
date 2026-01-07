"""
Configuration Superset pour FormaSup BI - Interface 100% Française
===================================================================

Selon la documentation officielle de Superset, il suffit de:
- BABEL_DEFAULT_LOCALE = "fr" 
- LANGUAGES = {"fr": {"flag": "fr", "name": "Français"}}

Les traductions sont compilées lors du build Docker avec BUILD_TRANSLATIONS=true
"""

import os
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# SÉCURITÉ
# =============================================================================
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY') or \
    "eiJBxyBH2wY/WPoKpAtytlL62pFDOLhu025PNVt0Z5foxRFM+lFUgwvT"
WTF_CSRF_ENABLED = True

# =============================================================================
# BASE DE DONNÉES
# =============================================================================
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
    'postgresql://superset:superset@superset-db:5432/superset'

# =============================================================================
# BRANDING
# =============================================================================
APP_NAME = "FormaSup BI"
APP_ICON = "/static/assets/images/logo.png"
LOGO_TARGET_PATH = "/superset/welcome"
LOGO_TOOLTIP = "Accueil"
LOGO_RIGHT_TEXT = ""

# =============================================================================
# LANGUE FRANÇAISE - Configuration Principale (doc officielle)
# =============================================================================

# Une seule langue = pas de sélecteur, français forcé
LANGUAGES = {
    "fr": {"flag": "fr", "name": "Français"},
}

# Babel configuration - C'est tout ce qu'il faut selon la doc officielle
BABEL_DEFAULT_LOCALE = "fr"
BABEL_DEFAULT_TIMEZONE = "Europe/Paris"

# =============================================================================
# FORMATS DE DATE/NOMBRE FRANÇAIS
# =============================================================================
D3_TIME_FORMAT = {
    "dateTime": "%d/%m/%Y, %H:%M:%S",
    "date": "%d/%m/%Y",
    "time": "%H:%M:%S",
    "periods": ["AM", "PM"],
    "days": ["Dimanche", "Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"],
    "shortDays": ["Dim", "Lun", "Mar", "Mer", "Jeu", "Ven", "Sam"],
    "months": ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
               "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"],
    "shortMonths": ["Jan", "Fév", "Mar", "Avr", "Mai", "Jun",
                    "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"]
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
# FIX TRADUCTIONS 6.0.0 - Workaround pour issue #35569
# Le chargement asynchrone des language packs (PR #34119) cause une race condition
# Cette fonction force le chargement du language pack français dans le bootstrap
# =============================================================================
def COMMON_BOOTSTRAP_OVERRIDES_FUNC(bootstrap_data):
    """
    Workaround pour le bug de traductions partielles dans Superset 6.0.0
    Charge le language pack français directement dans les données bootstrap
    pour éviter la race condition du chargement asynchrone.
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
                logger.info("Language pack français chargé via COMMON_BOOTSTRAP_OVERRIDES_FUNC")
    except Exception as e:
        logger.warning(f"Erreur chargement language pack: {e}")
    return bootstrap_data

# =============================================================================
# PERMISSIONS - Ajouter permission language_pack au rôle Public
# =============================================================================
def FLASK_APP_MUTATOR(app):
    """
    Ajoute la permission 'can language pack Superset' aux rôles Public et Gamma
    pour permettre aux utilisateurs non-admin d'accéder aux traductions.
    """
    @app.after_request
    def add_header(response):
        # Désactiver le cache sur les endpoints de traduction
        if '/language_pack/' in response.headers.get('Location', '') or \
           '/api/v1/common/' in response.headers.get('Location', ''):
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response

    with app.app_context():
        try:
            from superset import security_manager
            from superset.extensions import db
            
            # Trouver ou créer la permission
            perm = security_manager.find_permission_view_menu(
                'can_language_pack', 'Superset'
            )
            
            if perm:
                # Ajouter aux rôles Public et Gamma
                for role_name in ['Public', 'Gamma']:
                    role = security_manager.find_role(role_name)
                    if role and perm not in role.permissions:
                        role.permissions.append(perm)
                        logger.info(f"Permission 'can language pack' ajoutée au rôle {role_name}")
                
                db.session.commit()
        except Exception as e:
            logger.warning(f"Configuration permissions language_pack: {e}")

logger.info("Configuration FormaSup BI chargée - Langue: Français")

