# FormaSup BI - Reporting Platform

## Overview

FormaSup BI is a custom instance of Apache Superset 6.0.0 configured for FormaSup Auvergne and its academic partners (UCA, Clermont School of Business, ISRP).

**100% French interface by default** thanks to technical fixes for Superset 6.0.0 bug #35569.

## Quick Start

```bash
# Clone the project with submodules
git clone --recursive https://github.com/CypherXIII/formasup-bi-platform.git
cd formasup-bi-platform

# Start all services
docker compose up -d

# Access Superset at http://localhost:8088
# Login: admin / Password: admin
```

## Architecture

```txt
postgres_docker/
├── init/                        # PostgreSQL init scripts
├── migration/                   # Data migration scripts (Git submodule)
├── superset/                    # Superset configuration (Git submodule)
│   ├── apache-superset-src/     # Apache Superset 6.0.0 source code
│   ├── assets/                  # Static resources
│   │   └── images/              # Logos and favicons
│   ├── config/                  # Configuration files
│   │   └── superset_config.py   # Custom Superset configuration
│   ├── docker/                  # Docker-related files
│   │   └── Dockerfile           # Custom French Superset image
│   ├── locales/                 # Translation and localization files
│   │   └── backup-messages.po   # Complete French translations backup
│   ├── scripts/                 # Build and automation scripts
│   │   └── build-superset-fr.ps1 # Automated French build script
│   └── README.md                # Superset submodule documentation
├── docker-compose.yml           # Service orchestration
├── .gitmodules                  # Git submodules configuration
└── README.md                    # This documentation
```

### Project Organization

The project follows a **modular and organized structure** for better maintainability:

- **`apache-superset-src/`**: Complete Apache Superset 6.0.0 source code (~43MB)
- **`assets/`**: Static resources (logos, favicons, images)
- **`config/`**: Configuration files and custom settings
- **`docker/`**: Docker-related files and container definitions
- **`locales/`**: Translation files and localization resources
- **`scripts/`**: Build scripts, automation, and tooling

### Git Submodules

This project uses Git submodules for better organization:

- **`superset/`**: Independent repository containing Superset-specific configurations, assets, and build scripts
- **`migration/`**: Independent repository containing data migration tools and scripts

To clone with submodules:

```bash
git clone --recursive https://github.com/CypherXIII/formasup-bi-platform.git
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

1. **Build the French image**

```powershell
cd superset
.\scripts\build-superset-fr.ps1
cd ..
```

1. **Start services**

```powershell
docker compose up -d
```

1. **Access the application**

- URL: <http://localhost:8088>
- Login: admin
- Password: admin

### Updated File Paths

**Important**: File paths have been reorganized for better maintainability:

- **Build script**: `superset/build-superset-fr.ps1` → `superset/scripts/build-superset-fr.ps1`
- **Translations**: `superset/backup-messages.po` → `superset/locales/backup-messages.po`
- **Dockerfile**: `superset/Dockerfile` → `superset/docker/Dockerfile`

The `docker-compose.yml` has been updated to reference the new Dockerfile path.

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

## Development

### Repository Structure

- **`formasup-bi-platform`**: Main repository with Docker orchestration
- **`formasup-data-migration`**: Data migration tools and scripts
- **`superset/`**: Superset configuration and customizations

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and test them
4. Commit your changes: `git commit -m 'Add your feature'`
5. Push to the branch: `git push origin feature/your-feature`
6. Create a Pull Request

### Building Custom Images

For development, rebuild the French Superset image after configuration changes:

```bash
cd superset
.\scripts\build-superset-fr.ps1
cd ..
docker compose up -d --build
```

## License

Apache Superset: Apache 2.0 License

---

**Version**: 1.0.0 (January 2026)
**Base**: Apache Superset 6.0.0
