# Backup Service

Daily automated backup service for PostgreSQL databases.

## Features

- Automated daily backups at 3 AM (configurable)
- Backs up both FSA (staging) and Superset databases
- Configurable retention period (default: 7 days)
- Automatic cleanup of old backups

## Configuration

Environment variables in `.env`:

```bash
# Cron schedule (default: 3 AM daily)
BACKUP_CRON_SCHEDULE="0 3 * * *"

# Number of days to keep backups (default: 7)
BACKUP_RETENTION_DAYS=7

# Run backup immediately on container start (default: false)
RUN_BACKUP_ON_START=false
```

## Manual Backup

To run a manual backup:

```bash
docker exec backup-fsa /usr/local/bin/backup.sh
```

## Backup Location

Backups are stored in `./backups/` directory:

- `fsa_staging_YYYYMMDD_HHMMSS.dump` - FSA staging schema
- `fsa_dwh_YYYYMMDD_HHMMSS.dump` - FSA data warehouse schema
- `superset_YYYYMMDD_HHMMSS.dump` - Superset database

## Restore

To restore a backup:

```bash
# Restore FSA staging schema
docker exec -i postgres-fsa pg_restore -U postgres -d FSA -c ./backups/fsa_staging_XXXXXXXX_XXXXXX.dump

# Restore FSA dwh schema
docker exec -i postgres-fsa pg_restore -U postgres -d FSA -c ./backups/fsa_dwh_XXXXXXXX_XXXXXX.dump

# Restore Superset database
docker exec -i superset-db pg_restore -U superset -d superset -c ./backups/superset_XXXXXXXX_XXXXXX.dump
```

## Logs

View backup logs:

```bash
docker logs backup-fsa
```
