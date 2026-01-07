# FormaSup BI - Superset Configuration

> Custom Apache Superset 6.0.0 configuration with complete French translation for FormaSup Auvergne.

[![Superset](https://img.shields.io/badge/Superset-6.0.0-orange)](https://superset.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-25%20Passed-brightgreen)](#testing)
[![Coverage](https://img.shields.io/badge/Coverage-85%25+-yellowgreen)](#testing)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [French translation](#french-translation)
- [Configuration](#configuration)
- [Building](#building)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

This submodule contains the **Superset-specific configuration** for FormaSup BI, a custom instance of Apache Superset 6.0.0.

### Key Features

- **100% French interface** by default
- Complete fix for Superset bug #35569
- Custom branding and logos
- Production-ready Docker configuration
- Comprehensive test suite

---

## Architecture

```text
superset/
├── apache-superset-src/              # Superset 6.0.0 with French localization fix
├── assets/                           # Static resources
│   └── images/
│       ├── favicon.ico
│       └── logo.png
├── config/                           # Configuration files
│   └── superset_config.py            # Main Superset configuration
├── docker/                           # Docker files
│   └── Dockerfile                    # Custom image definition
├── locales/                          # Translation files
│   └── backup-messages.po            # French translations backup
├── scripts/                          # Build scripts
│   └── build-superset-fr.ps1         # French image build script
├── tests/                            # Test suite (25 tests)
│   ├── test_config.py                # Configuration tests
│   └── test_build.py                 # Build script tests
├── README.md                         # This documentation
└── README-superset-translation-fix.md # French fix documentation
```

### Directory Purposes

| Directory              | Purpose                                              |
|------------------------|------------------------------------------------------|
| `apache-superset-src/` | Superset 6.0.0 with French localization fix applied  |
| `assets/`              | Logos, favicons, images                              |
| `config/`              | Superset configuration files                         |
| `docker/`              | Docker image definitions                             |
| `locales/`             | French translation files backup                      |
| `scripts/`             | Build automation scripts                             |
| `tests/`               | Test suite (25 tests)                                |

---

## Quick Start

### Prerequisites

- Docker Desktop 24.0+
- PowerShell 7+ (Windows) or Bash (Linux/macOS)
- 16 GB RAM minimum

### Steps

1. **Clone Superset source** (if not using submodules):

```bash
git clone https://github.com/apache/superset.git apache-superset-src
cd apache-superset-src
git checkout 6.0.0
cd ..
```

1. **Build the French image**:

```powershell
# Windows
.\scripts\build-superset-fr.ps1

# Linux/macOS
./scripts/build-superset-fr.ps1
```

1. **Start services** (from parent directory):

```bash
cd ..
docker compose up -d
```

1. **Access the application**:

- **URL**: <http://localhost:8088>
- **Username**: admin
- **Password**: admin

---

## French translation

This submodule provides **complete French translation** for Superset 6.0.0, resolving bug #35569.

### The Problem

Superset 6.0.0 has a race condition (bug #35569) that prevents French translations from loading in the frontend, even when properly configured.

### The Solution

The build script applies targeted fixes:

1. **Backend fix**: Use `BABEL_DEFAULT_LOCALE` instead of hardcoded "en"
2. **Frontend fix**: Wait for language pack before React render
3. **Configuration**: Proper French locale settings

### Technical Details

The build script in `scripts/build-superset-fr.ps1` applies the necessary patches to fix bug #35569 during the Docker image build process.

---

## Configuration

### Main Configuration File

Edit `config/superset_config.py` to customize:

```python
# Security
SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "default-key")
WTF_CSRF_ENABLED = True

# Database
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")

# Branding
APP_NAME = "FormaSup BI"
APP_ICON = "/static/assets/images/logo.png"

# French translation
BABEL_DEFAULT_LOCALE = "fr"
LANGUAGES = {
    "fr": {"flag": "fr", "name": "Francais"},
}
```

### Environment Variables

| Variable              | Description                    | Required |
|-----------------------|--------------------------------|----------|
| `SUPERSET_SECRET_KEY` | Session encryption key         | Yes      |
| `DATABASE_URL`        | Superset metadata database URI | Yes      |
| `LANG`                | System locale                  | No       |

---

## Building

### Automated Build Script

The build script handles all required steps:

```powershell
# Windows PowerShell
.\scripts\build-superset-fr.ps1

# With custom version
.\scripts\build-superset-fr.ps1 -SupersetVersion "6.0.0"

# Force rebuild without cache
.\scripts\build-superset-fr.ps1 -NoBuildCache
```

### Build Process

1. **Reset source code** to specified tag
2. **Copy French translations** from backup
3. **Build Docker image** with `BUILD_TRANSLATIONS=true`

### Build Parameters

| Parameter          | Default                | Description            |
|--------------------|------------------------|------------------------|
| `-SupersetVersion` | `6.0.0`                | Superset version tag   |
| `-ImageName`       | `superset-fr-formasup` | Docker image name      |
| `-NoBuildCache`    | `$false`               | Disable Docker cache   |

---

## Testing

### Test Structure

```text
tests/
├── test_config.py    # Configuration validation tests
├── test_build.py     # Build script tests
└── __init__.py       # Test module init
```

### Running Tests

```bash
# All tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=config --cov-report=html
```

### Test Coverage

- **Configuration tests**: SECRET_KEY, locales, branding
- **Build tests**: Script existence, parameters, artifacts

---

## Troubleshooting

### Interface Shows English

1. Clear browser cache completely
2. Rebuild with translations:

```bash
.\scripts\build-superset-fr.ps1 -NoBuildCache
docker compose up -d --build
```

1. Verify configuration:

```bash
docker exec superset-fsa cat /app/pythonpath/superset_config.py | grep BABEL
```

### Build Fails

1. Verify source code exists:

```bash
ls apache-superset-src
```

1. Check Docker is running:

```bash
docker version
```

1. Review build logs for errors

### Container Won't Start

1. Check logs:

```bash
docker compose logs superset
```

1. Verify database connectivity:

```bash
docker compose ps
```

---

## Services

| Service       | Container     | Port  | Description                |
|---------------|---------------|-------|----------------------------|
| Superset      | superset-fsa  | 8088  | BI dashboards and SQL Lab  |
| PostgreSQL    | postgres-fsa  | 5432  | Business data database     |
| Superset DB   | superset-db   | 5442  | Superset metadata database |

---

## License

Apache Superset: Apache License 2.0

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Date**: January 2026  
**Base**: Apache Superset 6.0.0
