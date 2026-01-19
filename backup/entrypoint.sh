#!/bin/bash
# Entrypoint for backup container
# Author: Marie Challet
# Organization: Formasup Auvergne

set -e

# Create pgpass file for multiple database connections
cat > /root/.pgpass << EOF
${PG_HOST}:5432:${PG_DB}:${PG_USER}:${PGPASSWORD}
superset-db:5432:superset:${SUPERSET_DB_USER}:${SUPERSET_DB_PASSWORD}
*:5432:superset:${SUPERSET_DB_USER}:${SUPERSET_DB_PASSWORD}
EOF

chmod 600 /root/.pgpass

# Export PGPASSFILE to ensure pg_dump uses it
export PGPASSFILE=/root/.pgpass

# Configuration
BACKUP_HOUR=$(echo "${BACKUP_CRON_SCHEDULE:-0 3 * * *}" | awk '{print $2}')
LAST_RUN_FILE="/var/log/last_backup_date.txt"

# Function to check if backup should run today
should_run_backup() {
    local today=$(date +%Y-%m-%d)

    # Check if backup already ran today
    if [ -f "${LAST_RUN_FILE}" ]; then
        local last_run=$(cat "${LAST_RUN_FILE}")
        if [ "${last_run}" = "${today}" ]; then
            return 1  # Already ran today
        fi
    fi

    # Check if we passed the scheduled hour
    local current_hour=$(date +%H | sed 's/^0//')
    if [ ${current_hour} -ge ${BACKUP_HOUR} ]; then
        return 0  # Should run
    fi

    return 1  # Not time yet
}

# Mark backup as completed for today
mark_backup_completed() {
    date +%Y-%m-%d > "${LAST_RUN_FILE}"
}

echo "[$(date)] Backup service started"
echo "[$(date)] Schedule: ${BACKUP_CRON_SCHEDULE:-0 3 * * *} (runs at ${BACKUP_HOUR}:00)"
echo "[$(date)] Retention: ${BACKUP_RETENTION_DAYS:-7} days"

# Check if backup should run on startup (missed backup)
if should_run_backup; then
    echo "[$(date)] Scheduled backup time has passed, running backup now..."
    if /usr/local/bin/backup.sh; then
        mark_backup_completed
        echo "[$(date)] Startup backup completed successfully"
    else
        echo "[$(date)] Startup backup failed" >&2
    fi
elif [ "${RUN_BACKUP_ON_START:-false}" = "true" ]; then
    echo "[$(date)] Running initial backup (RUN_BACKUP_ON_START=true)..."
    if /usr/local/bin/backup.sh; then
        mark_backup_completed
        echo "[$(date)] Initial backup completed successfully"
    else
        echo "[$(date)] Initial backup failed" >&2
    fi
fi

# Configure cron schedule from environment variable
CRON_SCHEDULE="${BACKUP_CRON_SCHEDULE:-0 3 * * *}"

# Wrap backup script to mark completion
cat > /usr/local/bin/backup-wrapper.sh << 'WRAPPER'
#!/bin/bash
if /usr/local/bin/backup.sh >> /var/log/backup.log 2>&1; then
    date +%Y-%m-%d > /var/log/last_backup_date.txt
fi
WRAPPER

chmod +x /usr/local/bin/backup-wrapper.sh

# Update cron to use wrapper script
echo "${CRON_SCHEDULE} /usr/local/bin/backup-wrapper.sh" > /etc/crontabs/root

# Create log file
touch /var/log/backup.log

echo "[$(date)] Configured cron schedule: ${CRON_SCHEDULE}"

# Start cron in foreground
echo "[$(date)] Starting cron daemon..."
crond -f -l 2
