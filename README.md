# FormaSup BI - Reporting Platform

## Overview

FormaSup BI is a custom instance of Apache Superset 6.0.0 configured for FormaSup Auvergne and its academic partners (UCA, Clermont School of Business, ISRP).

**100% French interface by default** thanks to technical fixes for Superset 6.0.0 bug #35569.

## Getting Started

### Quick Setup (Recommended)

```bash
# Clone the project with submodules
git clone --recursive https://github.com/CypherXIII/formasup-bi-platform.git
cd formasup-bi-platform

# Start all services
docker compose up -d

# Access Superset at http://localhost:8088
# Login: admin / Password: admin
```

### Prerequisites

- Docker Desktop
- PowerShell 7+
- 16 GB RAM minimum

### Advanced Setup

For development or custom configuration:

1. **Clone Superset source code** (if not using submodules)

```powershell
git clone https://github.com/apache/superset.git superset/apache-superset-src
cd superset/apache-superset-src
git checkout 6.0.0
cd ../..
```

2. **Build the French image**

```powershell
cd superset
.\scripts\build-superset-fr.ps1
cd ..
```

3. **Start services**

```powershell
docker compose up -d
```

### Updated File Paths

**Important**: File paths have been reorganized for better maintainability:

- **Build script**: `superset/build-superset-fr.ps1` → `superset/scripts/build-superset-fr.ps1`
- **Translations**: `superset/backup-messages.po` → `superset/locales/backup-messages.po`
- **Dockerfile**: `superset/Dockerfile` → `superset/docker/Dockerfile`

The `docker-compose.yml` has been updated to reference the new Dockerfile path.

## French Localization

This project includes **complete French localization** for Superset 6.0.0, resolving bug #35569.

**Key features:**
- 100% French interface by default
- Custom build script with 5 targeted modifications
- Complete translation files backup

**Detailed documentation**: See `superset/README-superset-french-fix.md` for technical implementation details.

## Useful Commands

### Basic Operations
```bash
# Restart services
docker compose restart

# View logs
docker logs superset-fsa --tail 50 -f

# Access containers
docker exec -it superset-fsa bash
```

### Database Operations
```bash
# Backup databases
docker exec postgres-fsa pg_dump -U postgres FSA > backup_fsa.sql
docker exec superset-db pg_dump -U superset superset > backup_superset.sql
```

### Troubleshooting
```bash
# Check service health
docker compose ps

# Rebuild French image
cd superset && .\scripts\build-superset-fr.ps1 && cd ..
docker compose up -d

# Clear browser cache if interface appears in English
# Then refresh http://localhost:8088
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
- **`formasup-migration-tools`**: Data migration tools and scripts
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
