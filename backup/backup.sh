#!/bin/bash
# Daily backup script for PostgreSQL databases
# Author: Marie Challet
# Organization: Formasup Auvergne

set -e

# Ensure pgpass file is used
export PGPASSFILE=/root/.pgpass

# Function to wait for database to be ready
wait_for_database() {
    local host=$1
    local user=$2
    local db=$3
    local max_attempts=30
    local attempt=0

    while [ ${attempt} -lt ${max_attempts} ]; do
        if PGPASSWORD="${PGPASSWORD}" psql -h "${host}" -U "${user}" -d "${db}" -c "SELECT 1" > /dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    echo "[$(date)] Failed to connect to database ${db} at ${host}" >&2
    return 1
}

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
DATE_ONLY=$(date +%Y%m%d)

# Create backup directory if not exists
mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting daily backup..."

# Remove any existing backups from today to ensure only one backup per day
echo "[$(date)] Removing existing backups from today if any..."
rm -f "${BACKUP_DIR}"/backup_${DATE_ONLY}.tar.gz
rm -f "${BACKUP_DIR}"/*_${DATE_ONLY}.dump

# Wait for databases to be available
if ! wait_for_database "${PG_HOST}" "${PG_USER}" "${PG_DB}"; then
    echo "[$(date)] FSA database not available, backup aborted" >&2
    exit 1
fi

if ! PGPASSWORD="${SUPERSET_DB_PASSWORD}" wait_for_database "superset-db" "${SUPERSET_DB_USER}" "superset"; then
    echo "[$(date)] Superset database not available, backup aborted" >&2
    exit 1
fi

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
            -n "${schema}" -F c -f "${BACKUP_DIR}/fsa_${schema}_${DATE_ONLY}.dump"
    echo "[$(date)] Schema '${schema}' backup completed: fsa_${schema}_${DATE_ONLY}.dump"
done

# Full database backup for disaster recovery
echo "[$(date)] Backing up full database ${PG_DB}..."
pg_dump -h "${PG_HOST}" -U "${PG_USER}" -d "${PG_DB}" \
        -F c -f "${BACKUP_DIR}/fsa_full_${DATE_ONLY}.dump"

echo "[$(date)] Full database backup completed: fsa_full_${DATE_ONLY}.dump"

# Backup Superset database (uses PGPASSWORD for authentication)
echo "[$(date)] Backing up Superset database..."
PGPASSWORD="${SUPERSET_DB_PASSWORD}" pg_dump -h superset-db -U "${SUPERSET_DB_USER}" -d superset \
    -F c -f "${BACKUP_DIR}/superset_${DATE_ONLY}.dump"

echo "[$(date)] Superset backup completed: superset_${DATE_ONLY}.dump"

# Compress all dumps into a single tar.gz archive
echo "[$(date)] Compressing backups into archive..."
cd "${BACKUP_DIR}"
tar -czf "backup_${DATE_ONLY}.tar.gz" *_${DATE_ONLY}.dump 2>/dev/null
TAR_EXIT_CODE=$?
cd - > /dev/null

if [ ${TAR_EXIT_CODE} -eq 0 ]; then
    echo "[$(date)] Compression completed: backup_${DATE_ONLY}.tar.gz"

    # Display archive size
    ARCHIVE_SIZE=$(du -h "${BACKUP_DIR}/backup_${DATE_ONLY}.tar.gz" | cut -f1)
    echo "[$(date)] Archive size: ${ARCHIVE_SIZE}"

    # Remove individual dump files after successful compression
    rm -f "${BACKUP_DIR}"/*_${DATE_ONLY}.dump
    echo "[$(date)] Individual dump files removed after compression"
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
