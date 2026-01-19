#!/bin/bash
# Daily backup script for PostgreSQL databases
# Author: Marie Challet
# Organization: Formasup Auvergne

set -e

# Ensure pgpass file is used
export PGPASSFILE=/root/.pgpass

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting daily backup..."

# Discover non-system schemas and dump each separately for granular restore
echo "[$(date)] Discovering schemas in ${PG_DB}..."
SCHEMA_LIST=$(psql -h "${PG_HOST}" -U "${PG_USER}" -d "${PG_DB}" -Atc \
    "SELECT nspname FROM pg_namespace WHERE nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast') AND nspname NOT LIKE 'pg_temp_%' AND nspname NOT LIKE 'pg_toast_temp_%'")

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

# Backup Superset database (uses PGPASSWORD for authentication)
echo "[$(date)] Backing up Superset database..."
PGPASSWORD="${SUPERSET_DB_PASSWORD}" pg_dump -h superset-db -U "${SUPERSET_DB_USER}" -d superset \
    -F c -f "${BACKUP_DIR}/superset_${TIMESTAMP}.dump"

echo "[$(date)] Superset backup completed: superset_${TIMESTAMP}.dump"

# Compress all dumps into a single tar.gz archive
echo "[$(date)] Compressing backups into archive..."
cd "${BACKUP_DIR}"
tar -czf "backup_${TIMESTAMP}.tar.gz" *_${TIMESTAMP}.dump 2>/dev/null
TAR_EXIT_CODE=$?
cd - > /dev/null

if [ ${TAR_EXIT_CODE} -eq 0 ]; then
    echo "[$(date)] Compression completed: backup_${TIMESTAMP}.tar.gz"

    # Display archive size
    ARCHIVE_SIZE=$(du -h "${BACKUP_DIR}/backup_${TIMESTAMP}.tar.gz" | cut -f1)
    echo "[$(date)] Archive size: ${ARCHIVE_SIZE}"
else
    echo "[$(date)] Compression failed, keeping individual dump files" >&2
fi

# Cleanup old backups
echo "[$(date)] Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "backup_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "*.dump" -type f -mtime +${RETENTION_DAYS} -delete

# List current backups
echo "[$(date)] Current backups:"
ls -lh "${BACKUP_DIR}"/backup_*.tar.gz 2>/dev/null || echo "No compressed backups found"
ls -lh "${BACKUP_DIR}"/*.dump 2>/dev/null && echo "Warning: Uncompressed dumps found" || true

echo "[$(date)] Backup completed successfully"
