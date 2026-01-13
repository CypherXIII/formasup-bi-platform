#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  sleep 1
done

# Check if backup file exists
BACKUP_FILE="/docker-entrypoint-initdb.d/z_backup_2026012.dump"
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 0
fi

# Check if database is already populated
TABLE_COUNT=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")
if [ "$TABLE_COUNT" -gt 0 ]; then
  echo "Database already populated, skipping restore"
  exit 0
fi

echo "Restoring backup from $BACKUP_FILE..."
pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl -v "$BACKUP_FILE" || {
  echo "Warning: pg_restore completed with errors, but continuing..."
}

echo "Backup restore completed"
