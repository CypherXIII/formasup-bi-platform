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


def _get_login_html(error_msg=None, csrf_token=None):
    """Generate custom French login page HTML."""
    error_html = ""
    if error_msg:
        error_html = f'''
        <div class="alert-error">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18Z" stroke="currentColor" stroke-width="1.5"/>
            <path d="M10 6V10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <circle cx="10" cy="13" r="0.75" fill="currentColor"/>
          </svg>
          <span>{error_msg}</span>
        </div>'''

    csrf_input = ""
    if csrf_token:
        csrf_input = f'<input type="hidden" name="csrf_token" value="{csrf_token}">'

    return f'''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Connexion - FormaSup BI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <style>
    * {{
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }}

    :root {{
      --primary: #134169;
      --primary-dark: #0f344f;
      --secondary: #7EB0C1;
      --text-primary: #1a202c;
      --text-secondary: #4a5568;
      --border: #e2e8f0;
      --bg-input: #f7fafc;
      --error: #c53030;
      --error-bg: #fff5f5;
    }}

    html {{
      font-size: 16px;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }}

    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      background: linear-gradient(to bottom right, #f7fafc 0%, #edf2f7 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 32px;
      position: relative;
    }}

    body::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      background: linear-gradient(90deg, var(--primary) 0%, var(--secondary) 100%);
    }}

    .login-card {{
      background: white;
      width: 100%;
      max-width: 420px;
      border-radius: 12px;
      box-shadow:
        0 1px 3px rgba(0, 0, 0, 0.05),
        0 10px 30px rgba(0, 0, 0, 0.08);
      overflow: hidden;
    }}

    .login-header {{
      padding: 48px 48px 32px;
      text-align: center;
      background: linear-gradient(180deg, #ffffff 0%, #fafbfc 100%);
      border-bottom: 1px solid var(--border);
    }}

    .login-logo {{
      margin-bottom: 24px;
    }}

    .login-logo img {{
      max-width: 160px;
      height: auto;
      margin: 0 auto;
      display: block;
    }}

    .login-logo .fallback-text {{
      font-size: 22px;
      font-weight: 700;
      color: var(--primary);
      text-align: center;
      display: none;
    }}

    .login-title {{
      color: var(--text-primary);
      font-size: 24px;
      font-weight: 600;
      letter-spacing: -0.025em;
      margin-bottom: 8px;
    }}

    .login-subtitle {{
      color: var(--text-secondary);
      font-size: 14px;
      font-weight: 400;
    }}

    .login-body {{
      padding: 40px 48px 48px;
    }}

    .alert-error {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 16px;
      background: var(--error-bg);
      border: 1px solid #feb2b2;
      border-radius: 8px;
      color: var(--error);
      font-size: 14px;
      margin-bottom: 28px;
      line-height: 1.5;
    }}

    .alert-error svg {{
      flex-shrink: 0;
      margin-top: 2px;
    }}

    .form-group {{
      margin-bottom: 20px;
    }}

    .form-label {{
      display: block;
      color: var(--text-primary);
      font-size: 14px;
      font-weight: 500;
      margin-bottom: 8px;
    }}

    .form-control {{
      width: 100%;
      height: 44px;
      padding: 0 14px;
      border: 1.5px solid var(--border);
      border-radius: 6px;
      font-size: 15px;
      color: var(--text-primary);
      background: var(--bg-input);
      transition: all 0.2s ease;
    }}

    .form-control:hover {{
      background: white;
      border-color: #cbd5e0;
    }}

    .form-control:focus {{
      outline: none;
      background: white;
      border-color: var(--primary);
      box-shadow: 0 0 0 3px rgba(19, 65, 105, 0.08);
    }}

    .form-control::placeholder {{
      color: #a0aec0;
    }}

    .btn-login {{
      width: 100%;
      height: 44px;
      padding: 0 24px;
      background: var(--primary);
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 15px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      margin-top: 8px;
    }}

    .btn-login:hover {{
      background: var(--primary-dark);
      box-shadow: 0 4px 12px rgba(19, 65, 105, 0.2);
    }}

    .btn-login:active {{
      transform: translateY(1px);
    }}

    .login-footer {{
      padding: 20px 48px;
      text-align: center;
      background: #fafbfc;
      border-top: 1px solid var(--border);
    }}

    .login-footer-text {{
      color: var(--text-secondary);
      font-size: 13px;
      margin-bottom: 8px;
    }}

    .login-cookie-notice {{
      color: var(--text-secondary);
      font-size: 11px;
      opacity: 0.8;
    }}

    @media (max-width: 540px) {{
      body {{
        padding: 20px;
      }}

      .login-header,
      .login-body,
      .login-footer {{
        padding-left: 32px;
        padding-right: 32px;
      }}

      .login-header {{
        padding-top: 40px;
        padding-bottom: 28px;
      }}

      .login-body {{
        padding-top: 32px;
        padding-bottom: 40px;
      }}
    }}
  </style>
</head>
<body>
  <div class="login-card">
    <div class="login-header">
      <div class="login-logo">
        <img src="/static/assets/images/logo.png" alt="FormaSup BI">
        <div class="fallback-text">FormaSup BI</div>
      </div>
      <h1 class="login-title">Connexion</h1>
      <p class="login-subtitle">Accédez à votre plateforme Business Intelligence</p>
    </div>

    <div class="login-body">
      {error_html}
      <form method="post" action="/login/" autocomplete="on" novalidate>
        {csrf_input}
        <div class="form-group">
          <label class="form-label" for="username">Identifiant</label>
          <input
            type="text"
            name="username"
            id="username"
            class="form-control"
            placeholder="nom.prenom"
            autocomplete="username"
            autofocus
            required
          >
        </div>
        <div class="form-group">
          <label class="form-label" for="password">Mot de passe</label>
          <input
            type="password"
            name="password"
            id="password"
            class="form-control"
            placeholder="••••••••"
            autocomplete="current-password"
            required
          >
        </div>
        <button type="submit" class="btn-login">Se connecter</button>
      </form>
    </div>

    <div class="login-footer">
      <p class="login-footer-text">© 2026 FormaSup Auvergne</p>
      <p class="login-cookie-notice">Ce site utilise des cookies strictement necessaires a l'authentification (art. 82 RGPD).</p>
    </div>
  </div>
</body>
</html>'''

# =============================================================================
# SECURITY - Security by Design Best Practices
# =============================================================================
# This section implements comprehensive security measures following:
# - OWASP Security Guidelines
# - GDPR/RGPD compliance requirements
# - Defense in depth principle
# - Principle of least privilege

# -----------------------------------------------------------------------------
# 1. SECRET KEY - Foundation of all cryptographic operations
# -----------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY")
if not SECRET_KEY:
    raise ValueError(
        "SUPERSET_SECRET_KEY environment variable is required. "
        "Generate one with: openssl rand -base64 42"
    )

# -----------------------------------------------------------------------------
# 2. CSRF PROTECTION - Prevent Cross-Site Request Forgery
# -----------------------------------------------------------------------------
WTF_CSRF_ENABLED = True
WTF_CSRF_EXEMPT_LIST = [
    "superset.charts.data.api.data",
    "superset.dashboards.api.cache_dashboard_screenshot",
]
WTF_CSRF_SSL_STRICT = os.environ.get("SUPERSET_ENV") == "production"
WTF_CSRF_TIME_LIMIT = 3600  # Token expires after 1 hour

# -----------------------------------------------------------------------------
# 3. RATE LIMITING - Prevent brute force and DoS attacks
# -----------------------------------------------------------------------------
RATELIMIT_ENABLED = True
RATELIMIT_APPLICATION = "100 per minute"
RATELIMIT_STORAGE_URI = "memory://"
AUTH_RATE_LIMITED = True
AUTH_RATE_LIMIT = "5 per minute"  # Strict limit on login attempts

# -----------------------------------------------------------------------------
# 4. SESSION SECURITY - Secure session management
# -----------------------------------------------------------------------------
SESSION_COOKIE_NAME = "formasup_session"
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to cookies
SESSION_COOKIE_SECURE = os.environ.get("SUPERSET_ENV") == "production"
SESSION_COOKIE_SAMESITE = "Lax"  # Prevent CSRF via cookies
SESSION_COOKIE_PATH = "/"
REMEMBER_COOKIE_NAME = "formasup_remember"
REMEMBER_COOKIE_HTTPONLY = True
REMEMBER_COOKIE_SECURE = os.environ.get("SUPERSET_ENV") == "production"
REMEMBER_COOKIE_SAMESITE = "Lax"
REMEMBER_COOKIE_DURATION = timedelta(days=7)

# Session lifetime
from datetime import timedelta as td  # noqa: E402
PERMANENT_SESSION_LIFETIME = td(hours=8)  # 8 hours max session

# -----------------------------------------------------------------------------
# 5. HTTP SECURITY HEADERS - Defense in depth
# -----------------------------------------------------------------------------
# These are applied via FLASK_APP_MUTATOR and Talisman if available
TALISMAN_ENABLED = os.environ.get("SUPERSET_ENV") == "production"
TALISMAN_CONFIG = {
    "force_https": os.environ.get("SUPERSET_ENV") == "production",
    "strict_transport_security": True,
    "strict_transport_security_max_age": 31536000,  # 1 year
    "strict_transport_security_include_subdomains": True,
    "content_security_policy": {
        "default-src": "'self'",
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        "style-src": ["'self'", "'unsafe-inline'", "fonts.googleapis.com"],
        "font-src": ["'self'", "fonts.gstatic.com", "data:"],
        "img-src": ["'self'", "data:", "blob:"],
        "connect-src": ["'self'"],
        "frame-ancestors": "'none'",
        "form-action": "'self'",
    },
    "referrer_policy": "strict-origin-when-cross-origin",
    "permissions_policy": {
        "geolocation": "()",
        "microphone": "()",
        "camera": "()",
    },
}

# Additional security headers (applied in FLASK_APP_MUTATOR)
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Cache-Control": "no-store, no-cache, must-revalidate, private",
    "Pragma": "no-cache",
}

# -----------------------------------------------------------------------------
# 6. AUTHENTICATION SECURITY
# -----------------------------------------------------------------------------
# Password policy (enforced by Flask-AppBuilder)
FAB_PASSWORD_COMPLEXITY_ENABLED = True
FAB_PASSWORD_COMPLEXITY_VALIDATOR = (
    "^(?=.*[a-z])(?=.*[A-Z])(?=.*\\d)(?=.*[@$!%*?&])[A-Za-z\\d@$!%*?&]{12,}$"
)

# Account lockout after failed attempts
AUTH_LOCKOUT_ENABLED = True
AUTH_LOCKOUT_THRESHOLD = 5  # Lock after 5 failed attempts
AUTH_LOCKOUT_DURATION = timedelta(minutes=15)  # Lock for 15 minutes

# Disable user self-registration
AUTH_USER_REGISTRATION = False

# Disable password recovery (handled externally if needed)
AUTH_PASSWORD_RECOVERY = False

# -----------------------------------------------------------------------------
# 7. AUTHORIZATION - Principle of least privilege
# -----------------------------------------------------------------------------
# Public role configuration - deny all by default
PUBLIC_ROLE_LIKE = None
PUBLIC_ROLE_NAME = None

# Strict permission checking
FAB_ADD_SECURITY_VIEWS = True
FAB_ADD_SECURITY_PERMISSION_VIEW = True
FAB_ADD_SECURITY_VIEW_MENU_VIEW = True
FAB_ADD_SECURITY_PERMISSION_VIEWS_VIEW = True

# -----------------------------------------------------------------------------
# 8. LOGGING & AUDITING - Security event logging
# -----------------------------------------------------------------------------
LOG_FORMAT = "%(asctime)s:%(levelname)s:%(name)s:%(message)s"
LOG_LEVEL = "INFO"

# Enable query logging for audit trail
QUERY_LOGGER = True

# Log security events
ENABLE_ACCESS_REQUEST = True
ENABLE_ACCESS_REQUEST_LOG = True

# -----------------------------------------------------------------------------
# 9. DATA PROTECTION - GDPR compliance
# -----------------------------------------------------------------------------
# Anonymize user data in logs
ANONYMIZE_AUDIT_LOGS = True

# Data export restrictions
ALLOW_FULL_CSV_EXPORT = False  # Disable bulk data export

# -----------------------------------------------------------------------------
# 10. PROXY & NETWORK SECURITY
# -----------------------------------------------------------------------------
ENABLE_PROXY_FIX = True
PROXY_FIX_CONFIG = {
    "x_for": 1,
    "x_proto": 1,
    "x_host": 1,
    "x_port": 0,
    "x_prefix": 1,
}

# Trusted proxy headers only
PREFERRED_URL_SCHEME = "https" if os.environ.get("SUPERSET_ENV") == "production" else "http"

# -----------------------------------------------------------------------------
# 11. ERROR HANDLING - Prevent information disclosure
# -----------------------------------------------------------------------------
SHOW_STACKTRACE = os.environ.get("SUPERSET_ENV") != "production"
PROPAGATE_EXCEPTIONS = False

# Custom error messages (no internal details exposed)
CUSTOM_ERRORS = True

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

        # Links
        "colorLink": "#134169",
        "colorLinkHover": "#0f344f",
        "colorLinkActive": "#0a2239",

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

        # Semantic colors (success / error)
        "colorSuccess": "#2e7d32",
        "colorSuccessBg": "#edf7ed",
        "colorSuccessBorder": "#b7e1cd",
        "colorError": "#c53030",
        "colorErrorBg": "#fff5f5",
        "colorErrorBorder": "#feb2b2",

        # Text colors
        "colorTextBase": "#2d4830",
        "colorText": "#134169",
        "colorTextSecondary": "#4a5568",
        "colorTextTertiary": "#718096",
        "colorTextQuaternary": "#a0aec0",

        # Fills for subtle UI elements
        "colorFill": "#f8fafb",
        "colorFillSecondary": "#eef3f8",
        "colorFillTertiary": "#e8eef4",
        "colorFillQuaternary": "#dfebf5",

        # Background colors (soft light theme)
        "colorBgBase": "#ffffff",           # Main content background (white)
        "colorBgContainer": "#f8fafb",      # Cards / panels (very light gray)
        "colorBgElevated": "#ffffff",       # Modals / popovers (white)
        "colorBgLayout": "#f8fafb",         # Layout chrome (soft gray so content stays white #f4f7fb)

        # Navbar/Header specific (make navbar stand out)
        "colorBgHeader": "#134169",         # Navbar background (FormaSup blue)
        "colorHeaderBg": "#134169",         # Alt token used by some components
        "colorTextLightSolid": "#ffffff",   # Text on dark backgrounds (navbar text)
        "colorHeaderText": "#ffffff",       # Alt token for header text

        # Border colors (subtle separators)
        "colorBorder": "#d5e3ee",
        "colorBorderSecondary": "#c7d6e4",

        # Border radius
        "borderRadius": 8,
        "borderRadiusXS": 3,
        "borderRadiusSM": 6,
        "borderRadiusLG": 12,

        # Spacing and control heights
        "padding": 16,
        "paddingSM": 12,
        "paddingLG": 20,
        "margin": 16,
        "marginSM": 12,
        "marginLG": 20,
        "controlHeight": 40,
        "controlHeightSM": 32,
        "controlHeightLG": 44,

        # Typography sizing (slightly more readable)
        "fontSize": 14,
        "fontSizeHeading5": 16,
        "fontSizeHeading4": 18,

        # Shadows (softer, premium feel)
        "boxShadow": "0 10px 30px rgba(19, 65, 105, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04)",
        "boxShadowSecondary": "0 6px 18px rgba(19, 65, 105, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)",
    },
    # Component-level refinements for a more polished look
    "components": {
      # Header/Navbar
      "Layout": {
        "headerBg": "#134169",
        "headerColor": "#ffffff",
      },
      # Sidebar & menus
      "Menu": {
        "itemSelectedBg": "#e8f4f7",
        "itemHoverBg": "#f0f6fa",
        "itemSelectedColor": "#0f344f",
      },
      # Primary buttons
      "Button": {
        "colorPrimary": "#134169",
        "colorPrimaryHover": "#0f344f",
        "colorPrimaryActive": "#0a2239",
        "controlHeight": 40,
      },
      # Tabs
      "Tabs": {
        "itemSelectedColor": "#134169",
        "inkBarColor": "#134169",
      },
      # Tables
      "Table": {
        "headerBg": "#f4f7fb",
        "rowHoverBg": "#fbfdff",
      },
      # Tag & Badge
      "Tag": {
        "defaultBg": "#eef3f8",
        "defaultColor": "#134169",
      },
      "Badge": {
        "colorBgContainer": "#eef3f8",
        "colorText": "#134169",
      },
      # Tooltip
      "Tooltip": {
        "colorBgSpotlight": "#134169",
      },
      # Pagination
      "Pagination": {
        "itemActiveBg": "#e8f4f7",
      },
      # Select
      "Select": {
        "optionSelectedBg": "#e8f4f7",
      },
      # Cards/Panels
      "Card": {
        "colorBgContainer": "#ffffff",
      },
    },
}

# Custom categorical palette aligned with FormaSup colors
EXTRA_CATEGORICAL_COLOR_SCHEMES = [
    {
        "name": "FormaSup",
        "label": "FormaSup",
        "colors": [
            "#134169", "#7EB0C1", "#f3be72", "#4c8c2b", "#7851a9",
            "#d95f02", "#2ca02c", "#e15759", "#76b7b2", "#59a14f",
        ],
    }
]
DEFAULT_COLOR_SCHEME = "FormaSup"
DEFAULT_CATEGORICAL_COLOR_SCHEME = "FormaSup"

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
# FEATURE FLAGS - Security-focused configuration
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

    # Export features - DISABLED for security (data exfiltration prevention)
    "ALLOW_FULL_CSV_EXPORT": False,

    # SQL Lab - controlled via role permissions
    "SQLLAB_BACKEND_PERSISTENCE": True,

    # UI preferences
    "LISTVIEWS_DEFAULT_CARD_VIEW": True,
    "DATAPANEL_CLOSED_BY_DEFAULT": False,
    "FILTERBAR_CLOSED_BY_DEFAULT": False,

    # Security - DISABLED (prevent embedding/XSS vectors)
    "EMBEDDABLE_CHARTS": False,
    "EMBEDDED_SUPERSET": False,

    # Advanced features - DISABLED for security (code injection prevention)
    "ENABLE_TEMPLATE_PROCESSING": False,  # Prevent Jinja template injection
    "ENABLE_JAVASCRIPT_CONTROLS": False,  # Prevent XSS via custom JS
    "TAGGING_SYSTEM": False,
    "THUMBNAILS": False,
    "ALERT_REPORTS": False,

    # Row Level Security - ENABLED for data isolation
    "ROW_LEVEL_SECURITY": True,

    # Escape HTML in markdown - ENABLED for XSS prevention
    "ESCAPE_MARKDOWN_HTML": True,
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
        from superset.translations.utils import get_language_pack  # type: ignore[import]

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

    - Custom French login page
    - Adds language pack permission to Public/Gamma roles
    - Configures cache headers for translation endpoints
    - Redirects non-admin users to dashboard list after login

    Args:
        app: The Flask application instance
    """
    # Override Flask-WTF's CSRF protection for /login/ POST requests
    from flask_wtf.csrf import CSRFProtect  # type: ignore[import]
    original_protect = CSRFProtect.protect

    def protect_override(self):
        from flask import request # type: ignore
        # Skip CSRF check for our custom login form
        if request.path in ['/login/', '/login'] and request.method == 'POST':
            return  # Skip protection, we validate manually
        return original_protect(self)

    CSRFProtect.protect = protect_override

    # Mark /login/ requests to bypass Flask-WTF CSRF check
    @app.before_request
    def mark_login_bypass():
        from flask import request  # type: ignore[import]
        if request.path in ['/login/', '/login'] and request.method == 'POST':
            from flask import g  # type: ignore[import]
            g.csrf_bypass = True

    # Serve custom French login page before Superset handles it
    @app.before_request
    def serve_french_login():
        from flask import request, make_response  # type: ignore[import]
        from flask_login import current_user, login_user  # type: ignore[import]
        from flask_wtf.csrf import generate_csrf, validate_csrf  # type: ignore[import]
        from wtforms.validators import ValidationError  # type: ignore[import]

        if request.path != '/login/' and request.path != '/login':
            return None

        if current_user.is_authenticated:
            return None

        # Get CSRF token for the form
        csrf_token = generate_csrf()

        if request.method == 'POST':
            from superset import security_manager  # type: ignore[import]
            from flask import redirect  # type: ignore[import]

            # Validate CSRF token
            try:
                validate_csrf(request.form.get('csrf_token'))
            except ValidationError:
                error_msg = 'Erreur de sécurité (token invalide). Veuillez réessayer.'
                return make_response(_get_login_html(error_msg, csrf_token), 200)

            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not username or not password:
                error_msg = 'Veuillez remplir tous les champs'
                return make_response(_get_login_html(error_msg, csrf_token), 200)

            # Use Flask-AppBuilder's authentication to ensure proper session handling
            user = security_manager.find_user(username=username)
            if user and user.is_active:
                # Use security_manager's auth method for proper session setup
                if security_manager.auth_user_db(username, password):
                    login_user(user, remember=True)
                    # Mark session as permanent for proper cookie handling
                    from flask import session  # type: ignore[import]
                    session.permanent = True
                    # Log successful login for audit trail
                    logger.info(f"SECURITY: Successful login for user '{username}' from IP {request.remote_addr}")
                    # Redirect to dashboard list after successful login
                    return redirect('/dashboard/list/')

            # Log failed login attempt for security monitoring
            logger.warning(f"SECURITY: Failed login attempt for user '{username}' from IP {request.remote_addr}")

            # Password check failed or user not found
            error_msg = 'Identifiant ou mot de passe incorrect'
            return make_response(_get_login_html(error_msg, csrf_token), 200)

        return make_response(_get_login_html(csrf_token=csrf_token), 200)

    @app.after_request
    def add_security_headers(response):
        """Apply security headers to all responses."""
        # Core security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Cache control for sensitive pages
        if not response.headers.get("Cache-Control"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        # Translation endpoints need fresh data
        request_path = response.headers.get("Location", "")
        if "/language_pack/" in request_path or "/api/v1/common/" in request_path:
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"

        return response

    # Force login for unauthenticated users and set French locale
    @app.before_request
    def require_login():
        from flask import request, redirect, session, g  # type: ignore[import]
        from flask_login import current_user  # type: ignore[import]

        # Force French locale for all requests
        try:
            from flask_babel import refresh  # type: ignore[import]
            session['locale'] = 'fr'
            g.locale = 'fr'
            refresh()
        except Exception:
            pass

        # Allow access to login page, static files, API endpoints, and health check
        allowed_paths = ["/login/", "/login", "/static/", "/api/", "/health", "/language_pack/"]

        if any(request.path.startswith(path) for path in allowed_paths):
            return None

        # Redirect to login if not authenticated
        if not current_user.is_authenticated:
            return redirect("/login/")

        return None

    # Hide navbar on login page only
    @app.after_request
    def hide_navbar_on_login(response):
        from flask import request  # type: ignore[import]
        from flask_login import current_user  # type: ignore[import]

        try:
            # Only inject CSS on login page
            if request.path != "/login/" or current_user.is_authenticated:
                return response

            if response.status_code != 200:
                return response

            if not (response.content_type or "").startswith("text/html"):
                return response

            content = response.get_data(as_text=True)
            css = (
                "<style>"
                ".ant-layout-header,.navbar,header{display:none!important;}"
                ".ant-layout,.ant-layout-content{padding-top:0!important;margin-top:0!important;}"
                "</style>"
            )

            if "</head>" in content and css not in content:
                content = content.replace("</head>", f"{css}</head>", 1)
                response.set_data(content)
        except Exception:
            pass

        return response

    # Inject custom theme CSS into all HTML pages
    @app.after_request
    def inject_custom_theme(response):
        """Inject FormaSup premium theme CSS into all HTML responses."""
        from flask import request  # type: ignore[import]

        try:
            # Skip non-HTML responses
            if response.status_code != 200:
                return response

            if not (response.content_type or "").startswith("text/html"):
                return response

            # Skip login page (has its own styling)
            if request.path in ["/login/", "/login"]:
                return response

            content = response.get_data(as_text=True)

            # Inject custom CSS link before </head>
            css_link = '<link rel="stylesheet" href="/static/assets/css/formasup-theme.css" type="text/css">'

            if "</head>" in content and css_link not in content:
                content = content.replace("</head>", f"{css_link}</head>", 1)
                response.set_data(content)
        except Exception:
            pass

        return response

    # Force French language on login page
    @app.after_request
    def set_french_locale(response):
        from flask import request  # type: ignore[import]

        # Set locale cookie for French language on login page
        if request.path == "/login/" and response.status_code == 200:
            response.set_cookie("SUPERSET_LOCALE", "fr", max_age=31536000, samesite="Lax")

        return response

    # Redirect non-admin users to dashboard list after login
    @app.after_request
    def redirect_non_admin_to_dashboards(response):
        """Redirect non-admin users to dashboard list instead of welcome page."""
        from flask import redirect  # type: ignore[import]
        from flask_login import current_user  # type: ignore[import]

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
            from superset import security_manager  # type: ignore[import]
            from superset.extensions import db  # type: ignore[import]

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
# CUSTOM CSS & FONTS
# =============================================================================

# Custom font configuration
# Load external fonts at runtime without rebuilding the application
CUSTOM_FONT_URLS = [
    "/static/assets/fonts/booster-next-fy.css",
]

# Custom CSS file for premium theme styling
CUSTOM_CSS = "/static/assets/css/formasup-theme.css"


# =============================================================================
# STARTUP LOG
# =============================================================================

logger.info("FormaSup BI configuration loaded successfully")
logger.info(f"  - Language: {BABEL_DEFAULT_LOCALE}")
logger.info(f"  - App Name: {APP_NAME}")
logger.info(f"  - CSRF Enabled: {WTF_CSRF_ENABLED}")

