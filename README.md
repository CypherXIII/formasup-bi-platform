# FormaSup BI Platform

> A production-ready Business Intelligence platform based on Apache Superset 6.0.0, with complete French translation and MariaDB to PostgreSQL migration tools.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)
[![Superset](https://img.shields.io/badge/Superset-6.0.0-orange)](https://superset.apache.org/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-79%20Passed-brightgreen)](#testing)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Security](#security)
- [VPS Deployment](#vps-deployment)
- [Testing](#testing)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

A production-ready Business Intelligence platform based on Apache Superset 6.0.0, with complete French translation and MariaDB to PostgreSQL migration tools. Designed for educational data analysis at FormaSup Auvergne.

**FormaSup BI Platform** is a custom deployment of Apache Superset designed for FormaSup Auvergne and its academic partners (UCA, Clermont School of Business, ISRP). It provides:

- **Business Intelligence dashboards** for educational data analysis
- **100% French interface** with complete translation (fixing Superset bug #35569)
- **Data migration tools** for transferring data from MariaDB to PostgreSQL
- **Production-ready Docker deployment** with security best practices

### Intended Users

- Data analysts at FormaSup Auvergne
- Academic partners requiring BI dashboards
- IT administrators managing educational data infrastructure
- DevOps engineers deploying Superset in production

---

## Features

### Core Features

- **Apache Superset 6.0.0**: Full-featured BI platform with SQL Lab, dashboards, and charts
- **French translation**: Complete French interface with backend and frontend translations
- **PostgreSQL Backend**: Two databases (business data + Superset metadata)
- **Docker Orchestration**: Multi-service deployment with health checks

### Data Migration

- **MariaDB to PostgreSQL migration** with intelligent deduplication
- **API enrichment** for company data via French government APIs
- **Unified company table** (staging and enriched data merged)
- **Batch processing** with rate limiting and performance optimization
- **Comprehensive logging** and error handling

### Backup & Recovery

- **Automated daily backups** at 3 AM (configurable)
- **Multi-schema support** (staging + dwh)
- **Configurable retention** (default: 7 days)
- **One-command restore** from backup files

### Security Features

- Environment-based configuration (no hardcoded secrets)
- CSRF protection enabled by default
- Network isolation via Docker networks
- Health checks and automatic restarts

---

## Architecture

```text
formasup-bi-platform/
├── docker-compose.yml          # Service orchestration
├── docker-compose.prod.yml     # Production configuration
├── .env.example                # Environment template
├── README.md                   # This documentation
├── run-tests.ps1               # PowerShell test runner
├── run-tests.sh                # Bash test runner
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
├── backups-files/              # Backup storage directory
│   └── .gitkeep                # Keep directory in git
│
├── init/                       # PostgreSQL initialization scripts
│   ├── backup.dump             # Latest database backup
│   ├── merge_company_tables.sql # Company table migration
│   └── sync_sequences.sql      # Sequence synchronization
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
│   ├── db_monitor.py           # Database monitoring
│   ├── logger.py               # Logging configuration
│   ├── Dockerfile              # Migration container
│   ├── requirements.txt        # Python dependencies
│   ├── README.md               # Migration documentation
│   └── tests/                  # Test suite
│       ├── conftest.py
│       ├── test_database.py
│       ├── test_integration.py
│       ├── test_migration.py
│       └── test_utils.py
│
└── superset/                   # Superset configuration
    ├── apache-superset-src/    # Superset 6.0.0 source
    ├── config/                 # Custom configuration
    │   └── superset_config.py  # Superset settings
    ├── docker/                 # Docker files
    │   └── Dockerfile          # Custom Superset image
    ├── locales/                # French translations
    │   └── backup-messages.po  # Translation backup
    ├── scripts/                # Build scripts
    │   └── build-superset-fr.ps1
    ├── assets/                 # Logos and branding
    │   └── images/
    │       ├── favicon.ico
    │       └── logo.png
    ├── tests/                  # Test suite
    │   ├── test_config.py
    │   └── test_build.py
    └── README.md               # Superset documentation
```

### Services

| Service       | Container       | Port  | Description                    |
|---------------|-----------------|-------|--------------------------------|
| Superset      | superset-fsa    | 8088  | BI dashboards and SQL Lab      |
| PostgreSQL    | postgres-fsa    | 5432  | Business data database         |
| Superset DB   | superset-db     | 5442  | Superset metadata database     |
| Migration     | migration-fsa   | -     | Data migration service         |
| Backup        | backup-fsa      | -     | Daily automated backups        |

---

## Prerequisites

### System Requirements

- **RAM**: 16 GB minimum (8 GB for smaller deployments)
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
- Node.js 18+ (if modifying Superset frontend)

---

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

---

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
```

### Configuration Files

| File                                 | Purpose                     |
|--------------------------------------|-----------------------------|
| `docker-compose.yml`                 | Service definitions         |
| `.env`                               | Environment variables       |
| `superset/config/superset_config.py` | Superset configuration      |
| `migration/.env`                     | Migration-specific settings |

---

## Security

### Security Principles

This project follows **secure-by-default** principles:

1. **No hardcoded secrets**: All sensitive data via environment variables
2. **Input validation**: All user inputs validated before processing
3. **Network isolation**: Services communicate via internal Docker network
4. **CSRF protection**: Enabled by default in Superset
5. **Health checks**: Automatic service recovery

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

---

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

---

## Testing

### Test Suites

| Module     | Tests | Coverage | Description                   |
|------------|-------|----------|-------------------------------|
| Migration  | 54    | 80%+     | Database operations, API, etc.|
| Superset   | 25    | 85%+     | Configuration, build scripts  |
| **Total**  | 79    | 80%+     | All tests passing             |

### Running Tests

```bash
# All tests
./run-tests.sh          # Linux/macOS
.\run-tests.ps1         # Windows PowerShell

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

---

## Development

### Repository Structure

This is a monorepo containing all components:

- **Root**: Docker orchestration and main configuration
- **migration/**: Data migration tools (MariaDB to PostgreSQL)
- **superset/**: Superset configuration and French translation
- **deploy/**: VPS deployment resources

### Building Custom Images

```bash
# Rebuild Superset French image
cd superset
./scripts/build-superset-fr.ps1  # Windows
cd ..

# Rebuild all services
docker compose build --no-cache
docker compose up -d
```

### Code Style

- **Python**: PEP 8, type hints, docstrings
- **PowerShell**: Microsoft conventions
- **Markdown**: ATX headings, consistent formatting

---

## Troubleshooting

### Common Issues

#### Interface Shows English Instead of French

1. Clear browser cache and cookies
2. Rebuild image with `BUILD_TRANSLATIONS=true`
3. Verify `superset_config.py` has correct locale settings

```bash
cd superset && ./scripts/build-superset-fr.ps1
docker compose up -d --build
```

#### Database Connection Failed

1. Verify containers are running: `docker compose ps`
2. Check health status: `docker compose logs postgres`
3. Verify environment variables in `.env`

#### Container Keeps Restarting

```bash
# Check logs
docker compose logs superset

# Check health
docker exec superset-fsa curl http://localhost:8088/health
```

### Getting Help

1. Check the [Troubleshooting](#troubleshooting) section
2. Review container logs: `docker compose logs <service>`
3. Open an issue on GitHub with logs and configuration

---

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

---

## License

- **Apache Superset**: Apache License 2.0
- **This project**: Apache License 2.0

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Date**: January 2026  
**Base**: Apache Superset 6.0.0
