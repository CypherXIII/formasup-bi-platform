#!/bin/bash
# Daily backup script for PostgreSQL databases
# Author: Marie Challet
# Organization: Formasup Auvergne

set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# System schemas to exclude when dumping per schema
EXCLUDED_SCHEMAS="pg_catalog,information_schema,pg_toast"

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting daily backup..."

# Discover non-system schemas and dump each separately for granular restore
echo "[$(date)] Discovering schemas in ${PG_DB}..."
SCHEMA_LIST=$(psql -h "${PG_HOST}" -U "${PG_USER}" -d "${PG_DB}" -Atc \
    "SELECT nspname FROM pg_namespace WHERE nspname NOT IN (${EXCLUDED_SCHEMAS}) AND nspname NOT LIKE 'pg_temp_%' AND nspname NOT LIKE 'pg_toast_temp_%'")

if [ -z "${SCHEMA_LIST}" ]; then
    echo "[$(date)] No schemas found to back up; aborting." >&2
    exit 1
fi

for schema in ${SCHEMA_LIST}; do
    echo "[$(date)] Backing up schema '${schema}'..."
    pg_dump -h "${PG_HOST}" -U "${PG_USER}" -d "${PG_DB}" \
            -n "${schema}" -F c -f "${BACKUP_DIR}/fsa_${schema}_${TIMESTAMP}.dump"
    echo "[$(date)] Schema '${schema}' backup completed: fsa_${schema}_${TIMESTAMP}.dump"
done

# Full database backup for disaster recovery
echo "[$(date)] Backing up full database ${PG_DB}..."
pg_dump -h "${PG_HOST}" -U "${PG_USER}" -d "${PG_DB}" \
        -F c -f "${BACKUP_DIR}/fsa_full_${TIMESTAMP}.dump"

echo "[$(date)] Full database backup completed: fsa_full_${TIMESTAMP}.dump"

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
