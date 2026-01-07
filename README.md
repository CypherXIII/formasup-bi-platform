# FormaSup BI - Reporting Platform

## Overview

FormaSup BI is a custom instance of Apache Superset 6.0.0 configured for FormaSup Auvergne and its academic partners (UCA, Clermont School of Business, ISRP).

**100% French interface by default** thanks to technical fixes for Superset 6.0.0 bug #35569.

## Architecture

```txt
postgres_docker/
├── init/                        # PostgreSQL init scripts
├── migration/                   # Data migration scripts (Git submodule)
├── superset/                    # Superset configuration (Git submodule)
│   ├── assets/
│   │   ├── images/
│   │       ├── favicon.ico
│   │       └── logo.png
│   ├── backup-messages.po       # Complete FR translations (backup)
│   ├── build-superset-fr.ps1    # Automated build script
│   ├── config/
│   │   └── superset_config.py   # Custom configuration
│   └── Dockerfile               # Custom image extension
├── docker-compose.yml           # Service orchestration
├── .gitmodules                  # Git submodules configuration
└── README.md                    # This documentation
```

### Git Submodules

This project uses Git submodules for better organization:

- **`superset/`**: Independent repository containing Superset-specific configurations, assets, and build scripts
- **`migration/`**: Independent repository containing data migration tools and scripts

To clone with submodules:
```bash
git clone --recursive https://github.com/CypherXIII/superset_formasup.git
```

To update submodules:
```bash
git submodule update --remote
```

### Services

| Service | Port | Description |
| --------- | ------ | ------------- |
| superset-fsa | 8088 | Superset interface |
| postgres-fsa | 5432 | Business database |
| superset-db | 5442 | Superset metadata database |

## Installation

### Prerequisites

- Docker Desktop
- PowerShell 7+
- 16 GB RAM minimum

### Steps

1. **Clone Superset repository**

```powershell
git clone https://github.com/apache/superset.git superset/apache-superset-src
cd superset/apache-superset-src
git checkout 6.0.0
cd ../..
```

2. **Build the French image**

```powershell
cd superset
.\build-superset-fr.ps1
cd ..
```

3. **Start services**

```powershell
docker compose up -d
```

4. **Access the application**

- URL: <http://localhost:8088>
- Login: admin
- Password: admin

## French Translations

### Problem Solved

Superset 6.0.0 has a known bug (#35569) that causes a **race condition** in French translation loading. This bug prevents translation display despite file presence.

### Applied Solutions

#### 1. Source code fixes
- **Backend** (`superset/views/base.py`): Use `BABEL_DEFAULT_LOCALE` instead of "en" fallback
- **Frontend** (`superset-frontend/src/preamble.ts`): Wait for language pack loading before React rendering

#### 2. Custom configuration
- `BABEL_DEFAULT_LOCALE = "fr"`
- `LANGUAGES = {"fr": {"flag": "fr", "name": "Français"}}`
- Workaround to bypass race condition

#### 3. Translation architecture
- **Backend**: `.po` files → `.mo` (Flask-Babel)
- **Frontend**: `.po` files → `.json` (jed1.x format)

### Applied Modifications

The `build-superset-fr.ps1` script performs 5 modifications to force French:

| File | Modification |
| --------- | -------------- |
| messages.po | Complete translations (0 empty strings) |
| superset/config.py | BABEL_DEFAULT_LOCALE = "fr" |
| superset-frontend/src/constants.ts | locale: 'fr', lang: 'fr' |
| plugin-chart-echarts/src/constants.ts | DEFAULT_LOCALE = 'fr' |
| CurrencyFormatter.ts | locale = 'fr-FR' |

## Useful Commands

### Restart Superset

```powershell
docker compose restart superset
```

### View logs

```powershell
docker logs superset-fsa --tail 100 -f
```

### Backup databases

```powershell
docker exec postgres-fsa pg_dump -U postgres FSA > backup_fsa.sql
docker exec superset-db pg_dump -U superset superset > backup_superset.sql
```

### Rebuild image

```powershell
cd superset
.\build-superset-fr.ps1
cd ..
docker compose up -d
```

### Check translations

```bash
# Check present files
docker exec superset-fsa ls -la /app/superset/translations/fr/LC_MESSAGES/

# Functional endpoint
docker exec superset-fsa curl -s 'http://localhost:8088/superset/language_pack/fr/' | head -20

# Initialization logs
docker logs superset-fsa | grep -i "language\|traduction\|fr"
```

## Troubleshooting

### English interface

1. Clear browser cache (Ctrl+Shift+Del)
2. Check image: `docker images superset-fr-formasup`
3. Rebuild: `cd superset && .\build-superset-fr.ps1 && cd ..`

### Connection error

```powershell
docker compose ps
```

All services should be "healthy" or "running".

### Advanced debugging

```bash
# Inspect bootstrap data
docker exec superset-fsa curl -s 'http://localhost:8088/superset/bootstrap_data/' | jq '.locale'

# Check permissions
docker exec superset-fsa python -c "
from superset import app
from superset.app import create_app
app = create_app()
with app.app_context():
    from superset import security_manager
    print('Public role permissions:', [p.name for p in security_manager.get_public_role().permissions])
"
```

## Advanced Configuration

Edit `superset/config/superset_config.py` to:

- Modify branding
- Configure caches
- Enable/disable features
- Configure Row Level Security

## License

Apache Superset: Apache 2.0 License

---

**Version**: 1.0.0 (January 2026)
**Base**: Apache Superset 6.0.0
