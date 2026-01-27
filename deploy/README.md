# FormaSup BI Platform Deployment Guide

This document provides instructions for deploying the FormaSup BI Platform to a production VPS server.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Server Preparation](#server-preparation)
- [Deployment Steps](#deployment-steps)
- [SSL Configuration](#ssl-configuration)
- [Service Management](#service-management)
- [Monitoring](#monitoring)
- [Backup Procedures](#backup-procedures)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Server Requirements

- **OS**: Ubuntu 22.04 LTS or Debian 12
- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 50GB SSD minimum
- **Network**: Public IP address, ports 80/443 open

### Software Requirements

- Docker Engine 24.0+
- Docker Compose 2.20+
- Nginx 1.18+
- Certbot (for SSL)

## Server Preparation

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl git htop ufw
```

### 2. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add current user to docker group
sudo usermod -aG docker $USER

# Enable and start Docker
sudo systemctl enable docker
sudo systemctl start docker
```

### 3. Install Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
```

### 4. Configure Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw enable
```

## Deployment Steps

### 1. Clone Repository

```bash
sudo mkdir -p /opt/formasup-bi
sudo chown $USER:$USER /opt/formasup-bi
cd /opt/formasup-bi
git clone https://github.com/CypherXIII/formasup-bi-platform.git .
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment variables (MANDATORY)
nano .env
```

**Critical environment variables to set:**

```bash
# Generate a secure secret key
SUPERSET_SECRET_KEY=$(openssl rand -base64 42)

# Set database credentials
POSTGRES_PASSWORD=<strong_password>
SUPERSET_DB_PASSWORD=<strong_password>

# Set admin credentials
SUPERSET_ADMIN_PASSWORD=<strong_password>
```

### 3. Install systemd Service

```bash
sudo cp deploy/superset.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable superset
```

### 4. Configure Nginx

```bash
# Copy nginx configuration
sudo cp deploy/nginx.conf /etc/nginx/sites-available/superset

# Update server_name in configuration
sudo nano /etc/nginx/sites-available/superset

# Enable site
sudo ln -s /etc/nginx/sites-available/superset /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### 5. Start Services

```bash
# Start the application
sudo systemctl start superset

# Verify status
sudo systemctl status superset

# Check logs
sudo journalctl -u superset -f
```

## SSL Configuration

### Using Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d bi.formasup-auvergne.fr

# Verify auto-renewal
sudo certbot renew --dry-run
```

### Certificate Renewal Cron

```bash
# Add to crontab
echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'" | sudo tee -a /etc/crontab
```

## Service Management

### Start/Stop Commands

```bash
# Start all services
sudo systemctl start superset

# Stop all services
sudo systemctl stop superset

# Restart services
sudo systemctl restart superset

# Check status
sudo systemctl status superset
```

### Docker Management

```bash
# View running containers
docker compose ps

# View logs
docker compose logs -f

# Restart specific service
docker compose restart superset

# Access container shell
docker compose exec superset bash
```

## Monitoring

### Log Files

| Log | Location |
| ----- | ---------- |
| Superset | `docker compose logs superset` |
| PostgreSQL | `docker compose logs postgres` |
| Nginx Access | `/var/log/nginx/superset_access.log` |
| Nginx Error | `/var/log/nginx/superset_error.log` |
| systemd | `journalctl -u superset` |

### Health Checks

```bash
# Check Superset health
curl -s http://localhost:8088/health

# Check database connectivity
docker compose exec postgres pg_isready -U superset

# Check disk usage
df -h
```

### Resource Monitoring

```bash
# Real-time container stats
docker stats

# System resources
htop
```

## Backup Procedures

### Database Backup

```bash
# Create backup directory
mkdir -p /opt/formasup-bi/backups

# Backup PostgreSQL databases
docker compose exec postgres pg_dumpall -U postgres > /opt/formasup-bi/backups/backup_$(date +%Y%m%d).sql

# Compress backup
gzip /opt/formasup-bi/backups/backup_$(date +%Y%m%d).sql
```

### Automated Backup Script

```bash
#!/bin/bash
# /opt/formasup-bi/scripts/backup.sh

BACKUP_DIR="/opt/formasup-bi/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup
docker compose exec -T postgres pg_dumpall -U postgres | gzip > "$BACKUP_DIR/backup_$DATE.sql.gz"

# Remove old backups
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: backup_$DATE.sql.gz"
```

### Add to Crontab

```bash
# Daily backup at 2 AM
0 2 * * * /opt/formasup-bi/scripts/backup.sh >> /var/log/formasup-backup.log 2>&1
```

## Troubleshooting

### Common Issues

#### Container Won't Start

```bash
# Check logs
docker compose logs superset

# Verify environment
docker compose config

# Check disk space
df -h
```

#### Database Connection Failed

```bash
# Check PostgreSQL status
docker compose ps postgres

# Test connection
docker compose exec postgres psql -U superset -d superset -c "SELECT 1"
```

#### Nginx 502 Bad Gateway

```bash
# Check if Superset is running
curl http://localhost:8088/health

# Check nginx configuration
sudo nginx -t

# Check upstream connectivity
sudo netstat -tlnp | grep 8088
```

#### High Memory Usage

```bash
# Check container memory
docker stats --no-stream

# Restart services if needed
sudo systemctl restart superset
```

### Recovery Procedures

#### Restore from Backup

```bash
# Stop services
sudo systemctl stop superset

# Restore database
gunzip -c /opt/formasup-bi/backups/backup_YYYYMMDD.sql.gz | docker compose exec -T postgres psql -U postgres

# Restart services
sudo systemctl start superset
```

## Security Checklist

Before going to production:

- [ ] Changed all default passwords
- [ ] Generated unique SUPERSET_SECRET_KEY
- [ ] Enabled HTTPS with valid SSL certificate
- [ ] Configured firewall rules
- [ ] Set up automated backups
- [ ] Enabled HSTS header in nginx
- [ ] Reviewed security/SECURITY.md

## Contact

For deployment support:

- **Author**: Marie Challet
- **Organization**: FormaSup Auvergne
