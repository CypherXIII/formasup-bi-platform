#!/bin/bash
# Superset initialization and startup script
# Runs database migrations, creates admin user, and starts Gunicorn WSGI server

set -e

echo "Starting Superset initialization..."

# Database migrations
echo "Running database migrations..."
superset db upgrade

# Create admin user (ignore error if already exists)
echo "Creating admin user..."
superset fab create-admin \
  --username "${SUPERSET_ADMIN_USER}" \
  --firstname Admin \
  --lastname User \
  --email "${SUPERSET_ADMIN_EMAIL}" \
  --password "${SUPERSET_ADMIN_PASSWORD}" 2>/dev/null || true

# Initialize Superset
echo "Initializing Superset..."
superset init

# Start Gunicorn WSGI server
echo "Starting Gunicorn WSGI server..."
exec gunicorn \
  --bind 0.0.0.0:8088 \
  --workers 4 \
  --worker-class gthread \
  --threads 2 \
  --timeout 120 \
  --limit-request-line 0 \
  --limit-request-field_size 0 \
  --access-logfile - \
  --error-logfile - \
  "superset.app:create_app()"
