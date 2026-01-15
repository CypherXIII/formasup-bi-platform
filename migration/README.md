# Migration Tools: MariaDB to PostgreSQL

> A robust and modular migration tool for transferring data from MariaDB to PostgreSQL, featuring duplicate merging, advanced data cleaning, intelligent synchronization, and company API enrichment.

[![Python](https://img.shields.io/badge/Python-3.10+-green)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-54%20Passed-brightgreen)](#testing)
[![Coverage](https://img.shields.io/badge/Coverage-80%25+-yellowgreen)](#testing)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Migration Process](#migration-process)
- [API Enrichment](#api-enrichment)
- [Testing](#testing)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

---

## Overview

This migration tool provides a sophisticated solution for transferring data between database systems while handling common challenges:

- **Complete data migration** from MariaDB to PostgreSQL
- **Intelligent deduplication** of apprentice and company records
- **Data cleaning and normalization** during transfer
- **API enrichment** for company data via French government APIs
- **Optimized performance** with batch processing and rate limiting
- **Comprehensive logging** for monitoring and troubleshooting

### Key Features

| Feature                  | Description                                      |
|--------------------------|--------------------------------------------------|
| Batch Processing         | Configurable batch sizes for optimal performance |
| Rate Limiting            | Respects API rate limits automatically           |
| SIRET Validation         | Validates SIRET checksum via Luhn algorithm     |
| SIRET Correction         | Suggests corrections for invalid SIRETs using Hamming distance |
| Parallel API Requests    | ThreadPoolExecutor for concurrent validation (4 workers) |
| Dry Run Mode             | Test migration without modifying data            |
| Temporary Tables         | Safe migration with rollback capability          |
| Query Metrics            | Track database impact and slow queries           |
| Error Recovery           | Resume from failures with state preservation     |

---

## Architecture

The project is organized into specialized modules for improved maintainability:

```text
migration/
├── migrate.py           # Main entry point and CLI interface
├── config.py            # Centralized configuration via environment variables
├── logger.py            # Logging system configuration
├── database.py          # Connection handlers and database utilities
├── migration_core.py    # Core migration logic with optimizations
├── temp_tables.py       # Temporary table and schema management
├── cleanup.py           # Data cleaning functions
├── sync.py              # Table synchronization logic
├── api_enrichment.py    # API enrichment (companies + OPCO)
├── api_client.py        # Rate-limited API client
├── siret_correction.py  # SIRET validation and correction suggestions
├── db_monitor.py        # Database monitoring utilities
├── Dockerfile           # Container definition
├── requirements.txt     # Python dependencies
├── README.md            # This documentation
└── tests/               # Test suite
    ├── __init__.py
    ├── conftest.py      # Pytest fixtures
    ├── README.md        # Test documentation
    ├── test_database.py
    ├── test_integration.py
    ├── test_migration.py
    ├── test_siret_correction.py
    ├── test_opco_tabular.py
    └── test_utils.py
```

### Module Responsibilities

| Module              | Purpose                                          |
|---------------------|--------------------------------------------------|
| `migrate.py`        | CLI parsing, orchestration, entry point          |
| `config.py`         | Environment-based configuration management       |
| `database.py`       | Database connections, cursors, transactions      |
| `migration_core.py` | Data transfer logic, type conversion             |
| `cleanup.py`        | Name normalization, deduplication                |
| `api_enrichment.py` | SIRENE API integration, company data enrichment  |
| `api_client.py`     | HTTP client with retry and rate limiting         |
| `siret_correction.py` | SIRET validation, Hamming distance correction suggestions |

---

## Prerequisites

### System Requirements

- Python 3.10+
- Source MariaDB database with data to migrate
- Target PostgreSQL database with tables already created
- Network access between migration host and databases

### Python Dependencies

- `pymysql` - MariaDB/MySQL connector
- `psycopg2-binary` - PostgreSQL connector
- `python-dotenv` - Environment file support
- `requests` - HTTP client for API enrichment

---

## Installation

### Standard Installation

```bash
cd migration
pip install -r requirements.txt
```

### Docker Installation

```bash
# Build the image
docker build -t migration-app .

# Run migration
docker run --env-file .env migration-app
```

---

## Configuration

### Environment File

Create a `.env` file with the following variables:

```bash
# =============================================================================
# MariaDB Source Database
# =============================================================================
MARIA_HOST=localhost
MARIA_PORT=3306
MARIA_USER=root
MARIA_PASSWORD=your_password
MARIA_DB=source_database

# =============================================================================
# PostgreSQL Target Database
# =============================================================================
PG_HOST=localhost
PG_PORT=5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DB=target_database
PG_SCHEMA=staging
PG_TEMP_SCHEMA=temp_staging

# =============================================================================
# Performance Settings
# =============================================================================
BATCH_SIZE=500

# =============================================================================
# API Enrichment (Optional)
# =============================================================================
ENABLE_API_ENRICHMENT=false
API_REQUESTS_PER_SECOND=7

# OPCO enrichment
ENABLE_OPCO_ENRICHMENT=false
OPCO_RESOURCE_ID=default_resource_id

# =============================================================================
# Logging
# =============================================================================
MIGRATION_LOG=migration.log
ENABLE_DB_METRICS=true
DB_METRICS_SLOW_MS=200
DB_METRICS_LOG=db_metrics.log
```

### Configuration Parameters

| Parameter                 | Description                  | Default |
|---------------------------|------------------------------|---------|
| `BATCH_SIZE`              | Records per batch insert     | 500     |
| `API_REQUESTS_PER_SECOND` | API rate limit               | 7       |
| `DB_METRICS_SLOW_MS`      | Slow query threshold (ms)    | 200     |

---

## Usage

### Full Migration (Recommended)

```bash
python migrate.py --step full
```

### Step-by-Step Execution

```bash
# Step 1: Migrate data to temporary tables
python migrate.py --step migrate

# Step 2: Clean and deduplicate data
python migrate.py --step cleanup

# Step 3: Synchronize to main tables
python migrate.py --step sync
```

### Command-Line Options

| Option        | Description                                          |
|---------------|------------------------------------------------------|
| `--step`      | Migration step: `full`, `migrate`, `cleanup`, `sync` |
| `--dry-run`   | Simulate without modifying data                      |
| `--keep-temp` | Keep temporary tables after migration                |
| `--tables`    | Specific tables to migrate (comma-separated)         |

### Examples

```bash
# Dry run to see what would happen
python migrate.py --step full --dry-run

# Migrate specific tables only
python migrate.py --step migrate --tables apprentis,entreprises

# Keep temp tables for debugging
python migrate.py --step full --keep-temp
```

### Docker Execution

```bash
# Full migration
docker run --env-file .env migration-app

# With specific options
docker run --env-file .env migration-app python migrate.py --step migrate --dry-run

# Using host.docker.internal for local databases
docker run -e MARIA_HOST=host.docker.internal \
           -e PG_HOST=host.docker.internal \
           --env-file .env migration-app
```

---

## Migration Process

### Phase 1: Migrate (`--step migrate`)

**Preparation:**

- Validate configuration
- Create temporary schema
- Create temporary tables matching main table structure
- Disable triggers for performance

**Optimized Migration:**

- **Smart estimation**: Calculate required queries
- **Adaptive strategy**:
  - Small tables (≤ batch_size): Single query
  - Large tables: Paginated with optimized batch size (up to 10,000 rows)
- **Query monitoring**: Automatic stop if approaching limit
- **Type conversion**: Automatic MariaDB to PostgreSQL type mapping
- **Normalization**: Name/surname normalization during transfer

### Phase 2: Cleanup (`--step cleanup`)

- Normalize text fields (names, addresses)
- Identify and merge duplicates
- Validate data integrity
- Apply business rules

### Phase 3: Sync (`--step sync`)

- Compare temporary and main tables
- Apply changes with conflict resolution
- Re-enable triggers
- Drop temporary schema (unless `--keep-temp`)

---

## API Enrichment

### Company Data Enrichment

When `ENABLE_API_ENRICHMENT=true`, the tool enriches company data using French government APIs:

- **SIRENE API**: Official company registry
- **Data source**: `api.insee.fr` and `entreprise.data.gouv.fr`

### SIRET Validation and Correction

The tool validates SIRET (establishment identification number) using the Luhn algorithm and suggests corrections for invalid SIRETs:

#### SIRET Validation Process

1. **Luhn Algorithm Check**: Validates SIRET checksum
2. **API Verification**: Confirms existence via French government API
3. **Establishment Status Filter**: Excludes closed establishments (`etat_administratif: F`)
4. **Company Name Matching**: Scores match with expected company name
5. **INSEE Code Matching**: Verifies city INSEE code from MariaDB

#### SIRET Correction Algorithm

For invalid SIRETs (Luhn checksum errors), the tool uses Hamming distance to suggest corrections:

- **Distance=1 Only**: Generates only valid corrections differing by 1 digit (~126 candidates per SIRET)
- **Parallel Validation**: Uses ThreadPoolExecutor (4 workers) for concurrent API requests
- **Performance**: ~2 seconds per SIRET (vs. 100+ seconds before optimization)

**Algorithm Steps:**

1. Retrieve company name and city INSEE code from MariaDB
2. Generate all Luhn-valid candidates at distance=1 from original SIRET
3. Validate each candidate in parallel against the French government API
4. Filter by establishment status (open only)
5. Score matches by company name similarity and INSEE code match
6. Return up to 5 best candidates ranked by score

#### Output Files

- **`siret_corrections.txt`**: Suggestions for manual review (not applied to database)
  - Original SIRET with expected data from MariaDB
  - List of candidates with company name, city, and INSEE code
  - Distance (digit changes) for each candidate
  - Match scores for ranking
  
- **`siret_invalid.txt`**: SIRETs with Luhn errors (no valid correction found)
- **`siret_errors_api.txt`**: SIRETs with API retrieval errors

#### Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Candidates per SIRET | ~1,400+ | ~126 | 11x fewer |
| API calls per SIRET | ~1,400+ | ~14 | 100x fewer |
| Processing time | ~100+ seconds | ~2 seconds | 50x faster |
| Parallelization | Sequential | 4 workers | 4x concurrent |

### OPCO Enrichment

When `ENABLE_OPCO_ENRICHMENT=true`, adds OPCO (training organization) information:

- **Data source**: `data.gouv.fr` siret_opco dataset

### Rate Limiting

API calls are automatically rate-limited to respect service limits:

- Default: 7 requests per second
- Configurable via `API_REQUESTS_PER_SECOND`
- Automatic retry with exponential backoff

### Output Files Generated

After migration with API enrichment enabled, the following files are created:

| File | Purpose | Format |
|------|---------|--------|
| `migration.log` | Main migration log with all events | Text log |
| `db_metrics.log` | Database query metrics and performance | Text log |
| `siret_corrections.txt` | SIRET correction suggestions for manual review | Text report |
| `siret_invalid.txt` | List of invalid SIRETs (Luhn errors, no correction) | Text list |
| `siret_errors_api.txt` | SIRETs with API retrieval errors | Text list |

---

## Testing

### Test Structure

```text
tests/
├── test_migration.py     # Config, args, migration core tests
├── test_database.py      # Database operations tests
├── test_integration.py   # End-to-end workflow tests
├── test_utils.py         # Utility and API client tests
└── __init__.py
```

### Running Tests

```bash
# All tests
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/test_database.py -v
```

### Test Categories

| Category     | Tests | Description                    |
|--------------|-------|--------------------------------|
| Unit         | 27    | Individual function tests      |
| Integration  | 13    | Workflow and config tests      |
| Utilities    | 14    | Logger, API client tests       |
| **Total**    | 54    | All passing                    |

---

## Security

### Security Principles

1. **No hardcoded credentials**: All secrets via environment variables
2. **Secure connections**: Database connections use authentication
3. **Input validation**: All inputs validated before use
4. **Rate limiting**: Prevents API abuse
5. **Logging**: Sensitive data excluded from logs

### Security Warnings

> **WARNING**: Never commit `.env` files to version control!

- Store credentials securely
- Use strong passwords for database access
- Restrict network access to databases
- Review logs for sensitive data exposure

### Sensitive Files

Files that should NEVER be committed:

- `.env` - Environment configuration
- `*.log` - Log files
- `siret_invalid.txt` - Error reports
- `siret_errors_api.txt` - API error reports

---

## Troubleshooting

### Connection Issues

```bash
# Test MariaDB connection
python -c "import pymysql; pymysql.connect(host='localhost', user='root', password='pass', database='db')"

# Test PostgreSQL connection
python -c "import psycopg2; psycopg2.connect(host='localhost', user='postgres', password='pass', dbname='db')"
```

### Query Limit Reached

If you see "Query limit approaching" warnings:

1. Reduce `BATCH_SIZE` to make fewer, larger batches
2. Use `--tables` to migrate in smaller chunks

### Performance Issues

- Increase `BATCH_SIZE` for faster inserts
- Disable `ENABLE_DB_METRICS` if not needed
- Use `--dry-run` to estimate time

### API Errors

- Check rate limiting settings
- Verify network connectivity to APIs
- Review `siret_errors_api.txt` for details

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Date**: January 2026
