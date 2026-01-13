#!/bin/bash
# Daily backup script for PostgreSQL databases
# Author: Marie Challet
# Organization: Formasup Auvergne

set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting daily backup..."

# Backup FSA database (staging schema)
echo "[$(date)] Backing up FSA database..."
pg_dump -h "${PG_HOST}" -U "${PG_USER}" -d "${PG_DB}" \
    -n staging -F c -f "${BACKUP_DIR}/fsa_staging_${TIMESTAMP}.dump"

echo "[$(date)] FSA backup completed: fsa_staging_${TIMESTAMP}.dump"

# Backup Superset database
echo "[$(date)] Backing up Superset database..."
pg_dump -h superset-db -U "${SUPERSET_DB_USER}" -d superset \
    -F c -f "${BACKUP_DIR}/superset_${TIMESTAMP}.dump"

echo "[$(date)] Superset backup completed: superset_${TIMESTAMP}.dump"

# Cleanup old backups
echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "*.dump" -type f -mtime +${RETENTION_DAYS} -delete

# List current backups
echo "[$(date)] Current backups:"
ls -lh "${BACKUP_DIR}"/*.dump 2>/dev/null || echo "No backups found"

echo "[$(date)] Backup completed successfully"
