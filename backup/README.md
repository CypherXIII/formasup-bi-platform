# Backup Service

Daily automated backup service for PostgreSQL databases.

## Features

- Automated daily backups at 3 AM (configurable)
- Smart scheduling: if backup time is missed (container stopped), runs on next startup
- Backs up both FSA (staging) and Superset databases
- Per-schema backups for granular restore options
- Compressed tar.gz archives for efficient storage
- Configurable retention period (default: 7 days)
- Automatic cleanup of old backups
- Prevents duplicate backups on the same day

## Configuration

Environment variables in `.env`:

```bash
# Cron schedule (default: 3 AM daily)
BACKUP_CRON_SCHEDULE="0 3 * * *"

# Number of days to keep backups (default: 7)
BACKUP_RETENTION_DAYS=7

# Run backup immediately on container start (default: false)
# Note: Even if false, backup will run if scheduled time was missed
RUN_BACKUP_ON_START=false
```

## Smart Scheduling

The backup service implements intelligent scheduling similar to the migration service:

- **If container starts BEFORE scheduled time** (e.g., 1 AM): waits until 3 AM to run backup
- **If container starts AFTER scheduled time** (e.g., 10 AM): runs backup immediately if not already done today
- **If backup already ran today**: skips until next scheduled time
- **Prevents duplicate backups**: tracks last run date to ensure one backup per day maximum

## Manual Backup

To run a manual backup:

```bash
docker exec backup-fsa /usr/local/bin/backup.sh
```

## Backup Location

Backups are stored in `./backups-files/` (git-ignored) as compressed archives:

- `backup_YYYYMMDD_HHMMSS.tar.gz` - Compressed archive containing:
  - `fsa_<schema>_YYYYMMDD_HHMMSS.dump` - Each non-system schema of the FSA database
  - `fsa_full_YYYYMMDD_HHMMSS.dump` - Full FSA database (all schemas)
  - `superset_YYYYMMDD_HHMMSS.dump` - Superset database

The compression significantly reduces storage space while maintaining full restore capabilities.

## Restore

To restore a backup, first extract the archive:

```bash
# Extract backup archive
tar -xzf ./backups-files/backup_YYYYMMDD_HHMMSS.tar.gz -C ./backups-files/

# Restore one FSA schema
docker exec -i postgres-fsa pg_restore -U postgres -d FSA -c -n <schema> ./backups-files/fsa_<schema>_YYYYMMDD_HHMMSS.dump

# Restore full FSA database
docker exec -i postgres-fsa pg_restore -U postgres -d FSA -c ./backups-files/fsa_full_YYYYMMDD_HHMMSS.dump

# Restore Superset database
docker exec -i superset-db pg_restore -U superset -d superset -c ./backups-files/superset_YYYYMMDD_HHMMSS.dump
```

## Logs

View backup logs:

```bash
docker logs backup-fsa
```
