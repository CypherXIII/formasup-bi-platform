# FormaSup BI - Superset Docker

Business Intelligence platform based on Apache Superset 6.0.0, configured for FormaSup Auvergne.

## 🚀 Quick Start

```bash
# Go to superset folder
cd superset

# Build the French image
.\build-superset-fr.ps1

# Go back to root
cd ..

# Start services
docker compose up -d

# Access the application
# URL: http://localhost:8088
# Login: admin / admin
```

## 📁 Project Structure

- `superset/` - Superset configuration and sources
- `init/` - PostgreSQL initialization scripts
- `migration/` - Data migration scripts
- `docker-compose.yml` - Service orchestration
- `Dockerfile` - Custom image (moved to superset/ folder)

## 📖 Complete Documentation

See [`superset/README.md`](superset/README.md) for detailed documentation.

## 🐛 Issues?

Check the troubleshooting section in [`superset/README.md`](superset/README.md).