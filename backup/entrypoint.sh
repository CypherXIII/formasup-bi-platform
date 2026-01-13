#!/bin/bash
# Entrypoint for backup container
# Author: Marie Challet
# Organization: Formasup Auvergne

set -e

# Configure cron schedule from environment variable
CRON_SCHEDULE="${BACKUP_CRON_SCHEDULE:-0 3 * * *}"
echo "${CRON_SCHEDULE} /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1" > /etc/crontabs/root

# Create log file
touch /var/log/backup.log

echo "[$(date)] Backup service started"
echo "[$(date)] Schedule: ${CRON_SCHEDULE}"
echo "[$(date)] Retention: ${BACKUP_RETENTION_DAYS:-7} days"

# Run initial backup if requested
if [ "${RUN_BACKUP_ON_START:-false}" = "true" ]; then
    echo "[$(date)] Running initial backup..."
    /usr/local/bin/backup.sh
fi

# Start cron in foreground
echo "[$(date)] Starting cron daemon..."
crond -f -l 2
