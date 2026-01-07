# French translation Fix for Superset 6.0.0

> Technical documentation for resolving the French translation issue in Apache Superset 6.0.0 (Bug #35569).

---

## Problem Context

Superset 6.0.0 has a known bug (#35569) introduced by PR #34119 that causes a race condition in translation loading. This bug prevents French translations from displaying in the user interface, even when translation files are present.

### Symptoms

- Backend translations (.mo files) work correctly
- Frontend translations (.json files) fail to load
- Endpoint `/superset/language_pack/fr/` returns error "Language pack doesn't exist on the server"
- Interface remains in English despite French configuration

---

## Root Cause Analysis

The problem stems from a **race condition** between:

1. **Backend**: Hardcoded fallback to "en" instead of using `BABEL_DEFAULT_LOCALE`
2. **Frontend**: Asynchronous language pack loading that executes after React rendering

### Problematic Code Locations

| File                                    | Line | Issue                                    |
|-----------------------------------------|------|------------------------------------------|
| `superset/views/base.py`                | 406  | Hardcoded `"en"` fallback                |
| `superset-frontend/src/preamble.ts`     | -    | Async IIFE not awaited                   |
| `superset-frontend/src/views/index.tsx` | -    | React renders before translations load   |

---

## Applied Solutions

### 1. Backend Fix (base.py)

**File**: `superset/views/base.py`

```python
# Before (problematic)
language = locale.language if locale else "en"

# After (fixed)
language = locale.language if locale else app.config.get("BABEL_DEFAULT_LOCALE", "en")
```

This allows the `BABEL_DEFAULT_LOCALE = "fr"` configuration to work correctly.

### 2. Frontend Fix (preamble.ts)

**File**: `superset-frontend/src/preamble.ts`

```typescript
// Before: Unexported async IIFE
(async () => {
  // language pack loading...
})();

// After: Exported async function
export async function initPreamble(): Promise<void> {
  // language pack loading...
}
```

### 3. Frontend Fix (index.tsx)

**File**: `superset-frontend/src/views/index.tsx`

```typescript
// Before: Immediate render
import ReactDOM from 'react-dom';
import App from './App';
ReactDOM.render(<App />, document.getElementById('app'));

// After: Wait for language pack
import ReactDOM from 'react-dom';
import { initPreamble } from '../preamble';

(async () => {
  try {
    await initPreamble();
  } finally {
    const { default: App } = await import('./App');
    ReactDOM.render(<App />, document.getElementById('app'));
  }
})();
```

### 4. Remove Direct Import (RootContextProviders.tsx)

**File**: `superset-frontend/src/views/RootContextProviders.tsx`

```typescript
// Removed direct import (now imported in index.tsx)
// import '../preamble';
```

### 5. Configuration (superset_config.py)

**File**: `superset/config/superset_config.py`

```python
# French as default locale
BABEL_DEFAULT_LOCALE = "fr"

# Available languages (French only)
LANGUAGES = {
    "fr": {"flag": "fr", "name": "Francais"},
}

# Workaround for bug #35569
COMMON_BOOTSTRAP_OVERRIDES_FUNC = lambda app, user: {
    "locale": "fr",
    "language_pack": get_language_pack("fr")
}

# Public access to language pack
FLASK_APP_MUTATOR = lambda app: app.appbuilder.sm.add_permission_to_role(
    "can language pack Superset", "Public"
)
```

---

## Superset Translation Architecture

Superset uses two translation systems:

### Backend (Flask-Babel)

- **Files**: `.po` → `.mo` (compiled)
- **Location**: `superset/translations/fr/LC_MESSAGES/messages.mo`
- **Usage**: Server-side translations, Jinja2 templates

### Frontend (@superset-ui/translation)

- **Files**: `.po` → `.json` (jed1.x format)
- **Location**: `superset/translations/fr/LC_MESSAGES/messages.json`
- **Usage**: Client-side translations, React components

---

## Build and Deployment

### Step 1: Build Base Image

```bash
cd superset/apache-superset-src
docker build \
  --build-arg BUILD_TRANSLATIONS=true \
  -t superset-fr-formasup:latest \
  --target lean \
  .
```

### Step 2: Build Local Image

```bash
docker compose build --no-cache
```

### Step 3: Deploy

```bash
docker compose up -d
```

### Step 4: Verify

```bash
# Check translation files
docker exec superset-fsa ls -la /app/superset/translations/fr/LC_MESSAGES/

# Expected files:
# - messages.mo  (backend)
# - messages.json (frontend)
# - messages.po  (source)

# Test language pack endpoint
curl http://localhost:8088/superset/language_pack/fr/
```

---

## Verification Checklist

After deployment, verify:

- [ ] `/superset/language_pack/fr/` returns valid JSON
- [ ] Interface displays in French
- [ ] All menu items are translated
- [ ] Dashboard labels are in French
- [ ] SQL Lab interface is French
- [ ] Error messages appear in French

---

## Troubleshooting

### Language Pack Not Found

1. Verify `BUILD_TRANSLATIONS=true` was used during build
2. Check files exist inside container:

```bash
docker exec superset-fsa find /app -name "messages.json"
```

### Interface Still in English

1. Clear browser cache and cookies
2. Try incognito/private browsing mode
3. Check browser language settings
4. Verify `BABEL_DEFAULT_LOCALE = "fr"` in config

### Partial Translations

Some strings may remain in English if:

- They are hardcoded in the source
- They were added after translation file creation
- They are third-party library strings

---

## References

- **Superset Issue #35569**: [GitHub Link](https://github.com/apache/superset/issues/35569)
- **Superset PR #34119**: Original PR introducing the bug
- **Flask-Babel Documentation**: [Flask-Babel](https://flask-babel.tkte.ch/)
- **Superset Translation Guide**: [Superset Translation Guide](https://superset.apache.org/docs/contributing/translating)

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Date**: January 2026
