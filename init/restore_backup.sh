#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"; do
  sleep 1
done

# Check if backup file exists
BACKUP_FILE="/docker-entrypoint-initdb.d/backup.dump"
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE"
  exit 0
fi

# Check if database is already populated (check staging schema, not public)
SCHEMA_EXISTS=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = 'staging';")
if [ "$SCHEMA_EXISTS" -gt 0 ]; then
  TABLE_COUNT=$(psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'staging';")
  if [ "$TABLE_COUNT" -gt 0 ]; then
    echo "Database already populated (staging schema has $TABLE_COUNT tables), skipping restore"
    exit 0
  fi
fi

# Pre-create schemas and install required extensions BEFORE restore
echo "Creating schemas and installing extensions..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
  -- Create schemas
  CREATE SCHEMA IF NOT EXISTS staging;
  CREATE SCHEMA IF NOT EXISTS dwh;

  -- Install unaccent extension in staging schema (required for normalize_name function)
  CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA staging;

  -- Also install in public for compatibility
  CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA public;
EOSQL

echo "Restoring backup from $BACKUP_FILE..."
# Use --disable-triggers to avoid FK constraint errors during restore
# Use --single-transaction for atomicity
pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
  --no-owner \
  --no-acl \
  --disable-triggers \
  --if-exists \
  --clean \
  -v "$BACKUP_FILE" 2>&1 || {
  echo "Warning: pg_restore completed with some errors, but continuing..."
}

echo "Synchronizing sequences..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
  DO \$\$
  DECLARE
    r RECORD;
    max_id INTEGER;
    seq_name TEXT;
  BEGIN
    FOR r IN
      SELECT
        table_schema,
        table_name,
        column_name,
        pg_get_serial_sequence(table_schema || '.' || table_name, column_name) as sequence_name
      FROM information_schema.columns
      WHERE
        table_schema NOT IN ('pg_catalog', 'information_schema')
        AND pg_get_serial_sequence(table_schema || '.' || table_name, column_name) IS NOT NULL
    LOOP
      EXECUTE format('SELECT COALESCE(MAX(%I), 0) FROM %I.%I', r.column_name, r.table_schema, r.table_name) INTO max_id;
      IF max_id > 0 THEN
        EXECUTE format('SELECT setval(%L, %s)', r.sequence_name, max_id);
        RAISE NOTICE 'Set sequence % to %', r.sequence_name, max_id;
      END IF;
    END LOOP;
  END \$\$;
EOSQL

echo "Backup restore completed"
