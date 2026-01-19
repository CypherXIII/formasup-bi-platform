# FormaSup BI Platform

> A production-ready Business Intelligence platform based on Apache Superset 6.0.0, with complete French translation and MariaDB to PostgreSQL migration tools.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue)](https://www.postgresql.org/)
[![Superset](https://img.shields.io/badge/Superset-6.0.0-orange)](https://superset.apache.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Security](#security)
- [Backup and Recovery](#backup-and-recovery)
- [VPS Deployment](#vps-deployment)
- [Testing](#testing)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

A production-ready Business Intelligence platform based on Apache Superset 6.0.0, with complete French translation and MariaDB to PostgreSQL migration tools. Designed for educational data analysis at FormaSup Auvergne.

**FormaSup BI Platform** is a custom deployment of Apache Superset designed for FormaSup Auvergne and its academic partners (UCA, Clermont School of Business, ISRP). It provides:

- **Business Intelligence dashboards** for educational data analysis
- **100% French interface** with complete translation (fixing Superset bug #35569)
- **Data migration tools** for transferring data from MariaDB to PostgreSQL
- **Production-ready Docker deployment** with security best practices
  
## Features

### Core Features

- **Apache Superset 6.0.0**: Full-featured BI platform with SQL Lab, dashboards, and charts
- **French translation**: Complete French interface with backend and frontend translations
- **PostgreSQL Backend**: Two databases (business data + Superset metadata)
- **Docker Orchestration**: Multi-service deployment with health checks

### Data Migration

- **MariaDB to PostgreSQL migration** with intelligent deduplication
- **API enrichment** for company data via French government APIs (INSEE, Recherche Entreprises)
- **OPCO enrichment** for apprenticeship data (optional)
- **SIRET validation and correction** with detailed reporting
- **Batch processing** with rate limiting and performance optimization
- **Comprehensive logging** and error handling

### Backup and Recovery

- **Automated daily backups** at 3 AM (configurable via cron expression)
- **Smart scheduling**: runs missed backups on next startup
- **Compressed tar.gz archives** for efficient storage (50%+ space savings)
- **Per-schema backups** for granular restore options
- **Multi-database support** (business data + Superset metadata)
- **Configurable retention** (default: 7 days)
- **Duplicate prevention**: one backup per day maximum
- **One-command restore** from backup files

### Security Features

- Environment-based configuration (no hardcoded secrets)
- CSRF protection enabled by default
- Network isolation via Docker networks
- Health checks and automatic restarts

## Architecture

```text
formasup-bi-platform/
├── docker-compose.yml          # Service orchestration (development)
├── docker-compose.prod.yml     # Production configuration
├── .env.example                # Environment template
├── README.md                   # This documentation
├── docs/
│   └── DEV_RULES.md            # Development guidelines and rules
├── scripts/
│   ├── run-tests.ps1           # PowerShell test runner
│   └── run-tests.sh            # Bash test runner
├── config/
│   └── .markdownlint.json      # Markdown lint configuration
│
├── deploy/                     # VPS deployment resources
│   ├── nginx.conf              # Reverse proxy configuration
│   ├── superset.service        # systemd service file
│   └── README.md               # Deployment documentation
│
├── backup/                     # Automated backup service
│   ├── Dockerfile              # Backup container
│   ├── backup.sh               # Backup script
│   ├── entrypoint.sh           # Container entrypoint
│   └── README.md               # Backup documentation
│
├── backups-files/              # Backup storage directory (git-ignored)
│   └── backup_*.tar.gz         # Compressed PostgreSQL backup archives
│
├── init/                       # PostgreSQL initialization scripts
│   └── restore_backup.sh       # Database restore script
│
├── migration/                  # Data migration tools
│   ├── migrate.py              # Main entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connections
│   ├── migration_core.py       # Migration logic
│   ├── api_enrichment.py       # API data enrichment
│   ├── api_client.py           # Rate-limited API client
│   ├── cleanup.py              # Data cleaning functions
│   ├── sync.py                 # Table synchronization
│   ├── temp_tables.py          # Temporary table management
│   ├── siret_correction.py     # SIRET validation/correction
│   ├── logger.py               # Logging configuration
│   ├── Dockerfile              # Migration container
│   ├── requirements.txt        # Python dependencies
│   ├── README.md               # Migration documentation
│   └── tests/                  # Test suite
│       ├── conftest.py         # Test fixtures
│       ├── test_database.py    # Database tests
│       ├── test_integration.py # Integration tests
│       ├── test_migration.py   # Migration tests
│       ├── test_opco_tabular.py # OPCO enrichment tests
│       ├── test_siret_correction.py # SIRET tests
│       └── test_utils.py       # Utility tests
│
└── superset/                   # Superset configuration
    ├── apache-superset-src/    # Superset 6.0.0 source (DO NOT MODIFY)
    ├── config/                 # Custom configuration
    │   └── superset_config.py  # Superset settings
    ├── docker/                 # Docker files
    │   └── Dockerfile          # Custom Superset image
    ├── locales/                # French translations
    │   └── backup-messages.po  # Translation backup
    ├── scripts/                # Build and setup scripts
    │   ├── build-superset-fr.ps1  # French build script
    │   ├── check_themes.py     # Theme verification
    │   └── setup_viewer_role.py # Role setup
    ├── assets/                 # Logos and branding
    │   ├── images/             # Logo, favicon
    │   └── fonts/              # Custom fonts
    ├── tests/                  # Test suite
    │   ├── test_config.py      # Configuration tests
    │   └── test_build.py       # Build tests
    └── README.md               # Superset documentation
```

### Services

| Service       | Container       | Port  | Description                          |
|---------------|-----------------|-------|--------------------------------------|
| Superset      | superset-fsa    | 8088  | BI dashboards and SQL Lab            |
| PostgreSQL    | postgres-fsa    | 5432  | Business data database (PostgreSQL 17) |
| Superset DB   | superset-db     | 5442  | Superset metadata database (PostgreSQL 15) |
| Migration     | migration-fsa   | -     | Data migration service (scheduled)   |
| Backup        | backup-fsa      | -     | Daily automated backups              |

## Prerequisites

### System Requirements

- **RAM**: 8 GB minimum (16 GB recommended for production)
- **Storage**: 20 GB minimum for Docker images and data
- **OS**: Linux (recommended), Windows 10/11, macOS

### Software Requirements

- Docker Desktop 24.0+ or Docker Engine 24.0+
- Docker Compose v2.20+
- Git 2.30+
- PowerShell 7+ (Windows) or Bash (Linux/macOS)

### For Development

- Python 3.10+
- pytest 7.0+
- Node.js 18+ (for building Superset French translations)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/CypherXIII/formasup-bi-platform.git
cd formasup-bi-platform
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your values (REQUIRED for production)
nano .env
```

### 3. Start Services

```bash
# Development mode
docker compose up -d

# Production mode (recommended)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# View logs
docker compose logs -f superset
```

### 4. Access the Application

- **URL**: <http://localhost:8088>
- **Username**: admin
- **Password**: admin

> **WARNING**: Change default credentials immediately in production!

## Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# =============================================================================
# SUPERSET CONFIGURATION
# =============================================================================

# REQUIRED: Generate with: openssl rand -base64 42
SUPERSET_SECRET_KEY=your-secure-secret-key-here

# Admin credentials (change in production!)
SUPERSET_ADMIN_USER=admin
SUPERSET_ADMIN_PASSWORD=admin
SUPERSET_ADMIN_EMAIL=admin@example.com

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Business database (postgres-fsa)
POSTGRES_DB=FSA
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password

# Superset metadata database (superset-db)
SUPERSET_DB_USER=superset
SUPERSET_DB_PASSWORD=superset

# =============================================================================
# MIGRATION CONFIGURATION (optional)
# =============================================================================

# MariaDB source
MARIA_HOST=localhost
MARIA_USER=root
MARIA_PASSWORD=your-mariadb-password
MARIA_DB=source_database

# PostgreSQL target
PG_HOST=localhost
PG_USER=postgres
PG_PASSWORD=your-postgres-password
PG_DB=FSA
PG_SCHEMA=staging

# Performance
BATCH_SIZE=500
ENABLE_API_ENRICHMENT=false
API_REQUESTS_PER_SECOND=7

# OPCO enrichment (optional)
ENABLE_OPCO_ENRICHMENT=false
OPCO_RESOURCE_ID=59533036-3c0b-45e6-972c-e967c0a1be17

# Scheduler (hour 0-23 when migration runs daily)
MIGRATION_RUN_HOUR=1

# =============================================================================
# BACKUP CONFIGURATION (optional)
# =============================================================================

BACKUP_CRON_SCHEDULE=0 3 * * *
BACKUP_RETENTION_DAYS=7
RUN_BACKUP_ON_START=false
```

### Configuration Files

| File                                 | Purpose                       |
|--------------------------------------|-------------------------------|
| `docker-compose.yml`                 | Service definitions           |
| `docker-compose.prod.yml`            | Production overrides          |
| `.env`                               | Environment variables         |
| `superset/config/superset_config.py` | Superset configuration        |
| `migration/config.py`                | Migration settings            |

## Security

### Security Principles

This project follows **secure-by-default** principles:

1. **No hardcoded secrets**: All sensitive data via environment variables
2. **Input validation**: All user inputs validated before processing
3. **Network isolation**: Services communicate via internal Docker network
4. **CSRF protection**: Enabled by default in Superset
5. **Health checks**: Automatic service recovery
6. **Parameterized queries**: SQL injection prevention in migration tools

### Security Warnings

> **CRITICAL**: Before deploying to production:
>
> 1. Generate new `SUPERSET_SECRET_KEY`: `openssl rand -base64 42`
> 2. Change all default passwords in `.env`
> 3. Configure reverse proxy with HTTPS
> 4. Restrict database ports (remove public port mappings)
> 5. Review `superset_config.py` security settings

### Known Limitations

- Default admin credentials are `admin/admin`
- Database ports are exposed by default (for development)
- No built-in rate limiting (use reverse proxy)
- No built-in authentication integration (LDAP/OAuth configurable)

## Backup & Recovery

### Automated Backups

The backup service runs daily at 3 AM by default (configurable via `BACKUP_CRON_SCHEDULE`). Each run produces:

- `backups-files/fsa_<schema>_YYYYMMDD_HHMMSS.dump` for every non-system schema of the FSA database
- `backups-files/fsa_full_YYYYMMDD_HHMMSS.dump` for a full FSA database snapshot
- `backups-files/superset_YYYYMMDD_HHMMSS.dump` for Superset metadata

```bash
# Manual backup
docker exec backup-fsa /usr/local/bin/backup.sh

# List available backups
ls -la backups-files/
```

### Restore from Backup

```bash
# Restore one FSA schema (replace <schema>)
docker exec -i postgres-fsa pg_restore -U postgres -d FSA -c backups-files/fsa_<schema>_YYYYMMDD_HHMMSS.dump

# Restore full FSA database
docker exec -i postgres-fsa pg_restore -U postgres -d FSA -c backups-files/fsa_full_YYYYMMDD_HHMMSS.dump

# Restore Superset metadata
docker exec -i superset-db pg_restore -U superset -d superset -c backups-files/superset_YYYYMMDD_HHMMSS.dump

# Or use the helper script (targets FSA)
./init/restore_backup.sh backups-files/fsa_full_YYYYMMDD_HHMMSS.dump
```

### Backup Configuration

| Variable                | Default       | Description                    |
|-------------------------|---------------|--------------------------------|
| `BACKUP_CRON_SCHEDULE`  | `0 3 * * *`   | Cron expression for backup time|
| `BACKUP_RETENTION_DAYS` | `7`           | Days to keep backup files      |
| `RUN_BACKUP_ON_START`   | `false`       | Run backup on container start  |

## VPS Deployment

### Server Requirements

- Ubuntu 22.04 LTS or Debian 12 (recommended)
- Docker Engine and Docker Compose installed
- Domain name with DNS configured
- SSL certificate (Let's Encrypt recommended)

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Logout and login for group changes
exit
```

### Step 2: Clone and Configure

```bash
# Clone repository
cd /opt
sudo git clone https://github.com/CypherXIII/formasup-bi-platform.git
sudo chown -R $USER:$USER formasup-bi-platform
cd formasup-bi-platform

# Configure environment
cp .env.example .env
nano .env  # Set production values
```

### Step 3: Configure Nginx Reverse Proxy

```bash
# Install Nginx
sudo apt install nginx certbot python3-certbot-nginx

# Copy configuration
sudo cp deploy/nginx.conf /etc/nginx/sites-available/superset
sudo ln -s /etc/nginx/sites-available/superset /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Edit domain name
sudo nano /etc/nginx/sites-available/superset

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

### Step 4: SSL Certificate

```bash
# Obtain certificate
sudo certbot --nginx -d bi.yourdomain.com

# Auto-renewal is configured automatically
```

### Step 5: Start Services

```bash
# Start containers (production mode)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify services
docker compose ps
curl http://localhost:8088/health
```

### Step 6: Configure systemd (Optional)

```bash
# Copy service file
sudo cp deploy/superset.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable superset
sudo systemctl start superset
```

### Production Checklist

- [ ] Generate new `SUPERSET_SECRET_KEY`
- [ ] Change all default passwords
- [ ] Configure SSL/TLS with valid certificate
- [ ] Remove public database port mappings
- [ ] Configure firewall (ufw or iptables)
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Review security settings in `superset_config.py`

## Testing

### Test Suites

| Module     | Tests | Coverage | Description                          |
|------------|-------|----------|--------------------------------------|
| Migration  | 6     | 80%+     | Database, API, SIRET, OPCO tests     |
| Superset   | 2     | 85%+     | Configuration and build tests        |

### Running Tests

```bash
# All tests (recommended)
./scripts/run-tests.sh          # Linux/macOS
.\scripts\run-tests.ps1         # Windows PowerShell

# Migration tests only
cd migration
python -m pytest tests/ -v

# Superset tests only
cd superset
python -m pytest tests/ -v

# With coverage report
pytest --cov=migration --cov-report=html
```

### Test Requirements

```bash
pip install pytest pytest-cov pytest-mock
```

## Development

### Repository Structure

This is a monorepo containing all components:

- **Root**: Docker orchestration and main configuration
- **migration/**: Data migration tools (MariaDB to PostgreSQL)
- **superset/**: Superset configuration and French translation
- **deploy/**: VPS deployment resources
- **backup/**: Automated backup service

### Building Custom Images

```bash
# Build Superset French image (required first time)
cd superset/scripts
./build-superset-fr.ps1  # Windows PowerShell
cd ../..

# Build and start all services
docker compose build
docker compose up -d

# Rebuild a specific service
docker compose build superset
docker compose up -d superset
```

### Migration Commands

```bash
# Run full migration
docker exec migration-fsa python migrate.py --step migrate

# Dry run (no changes)
docker exec migration-fsa python migrate.py --step migrate --dry-run

# Run specific step
docker exec migration-fsa python migrate.py --step enrich
docker exec migration-fsa python migrate.py --step sync
```

### Code Style

- **Python**: PEP 8, type hints required, docstrings required
- **PowerShell**: Microsoft conventions
- **Markdown**: ATX headings, English only, no emojis

## Troubleshooting

### Common Issues

#### Interface Shows English Instead of French

1. Clear browser cache and cookies
2. Rebuild image: `docker compose build superset`
3. Verify `superset_config.py` has correct locale settings

```bash
docker compose up -d --build superset
```

#### Database Connection Failed

1. Verify containers are running: `docker compose ps`
2. Check health status: `docker compose logs postgres`
3. Verify environment variables in `.env`
4. Check network connectivity: `docker network inspect fsa-net`

#### Container Keeps Restarting

```bash
# Check logs
docker compose logs superset

# Check health
docker exec superset-fsa curl http://localhost:8088/health

# Check container status
docker inspect superset-fsa --format='{{.State.Health.Status}}'
```

#### Migration Fails

```bash
# Check migration logs
docker compose logs migration

# Run in dry-run mode to diagnose
docker exec migration-fsa python migrate.py --step migrate --dry-run

# Check database connectivity
docker exec migration-fsa python -c "from database import get_pg_connection; print(get_pg_connection())"
```

### Getting Help

1. Check the [Troubleshooting](#troubleshooting) section
2. Review container logs: `docker compose logs <service>`
3. Check [DEV_RULES.md](DEV_RULES.md) for development guidelines
4. Open an issue on GitHub with logs and configuration

## Contributing

### Guidelines

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `./run-tests.sh`
5. Commit with clear messages: `git commit -m 'Add: your feature'`
6. Push and create a Pull Request

### Commit Message Format

```text
<type>: <description>

Types: Add, Fix, Update, Refactor, Test, Docs, Chore
```

## License

- **Apache Superset**: Apache License 2.0
- **This project**: Apache License 2.0

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 2.0.0  
**Last Updated**: January 2026  
**Base**: Apache Superset 6.0.0
