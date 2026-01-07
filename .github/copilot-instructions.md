# GitHub Copilot Instructions - FormaSup BI Platform

## Project Overview

This is a production business intelligence platform for FormaSup Auvergne. The project integrates:

- **Apache Superset 6.0.0** with French translation fix
- **PostgreSQL 15** for data storage
- **Docker Compose** for orchestration
- **Python migration tools** for MariaDB to PostgreSQL migration

### Compliance Context

This project operates under strict compliance requirements:

- **ISO 27001:2022** - Information Security Management System
- **RGPD/GDPR** - General Data Protection Regulation
- **Data Classification** - C1 to C4 levels per sensitivity
- **Regular Audits** - Internal and external security audits

See `security/` folder for detailed documentation:
- `DATA_CLASSIFICATION.md` - Data sensitivity levels (ISO 27001 A.8.2)
- `ACCESS_CONTROL.md` - Access control policy (ISO 27001 A.9)
- `INCIDENT_RESPONSE.md` - Incident handling (ISO 27001 A.16, RGPD Art. 33-34)
- `DATA_RETENTION.md` - Retention periods (RGPD Art. 5)
- `THREAT_MODEL.md` - STRIDE threat analysis
- `HARDENING.md` - Production security checklist

## Critical Rules

### Language Requirements

1. **All code comments MUST be in English**
2. **All documentation MUST be in English**
3. **All commit messages MUST be in English**
4. **NO emojis anywhere in code or documentation**

### Security Requirements (ISO 27001 / RGPD)

1. **NEVER hardcode secrets or credentials** (ISO 27001 A.9)
2. **Always use environment variables for sensitive data** (ISO 27001 A.9)
3. **Maintain CSRF protection in Superset configuration** (OWASP)
4. **Validate all user inputs in migration scripts** (OWASP, RGPD Art. 32)
5. **Use parameterized queries for database operations** (SQL Injection prevention)
6. **Respect data classification levels** (C1-C4 per DATA_CLASSIFICATION.md)
7. **Log security-relevant events** for audit trail (ISO 27001 A.12)
8. **Consider data retention requirements** when handling personal data (RGPD Art. 5)

### Architecture Constraints

1. **DO NOT modify** `docker-compose.yml` without explicit request
2. **DO NOT modify** `superset/config/superset_config.py` without explicit request
3. **DO NOT add new dependencies** without explicit approval
4. **DO NOT change database schemas** without migration scripts

### Testing Requirements

1. **Run existing tests** before making changes
2. **Add tests** for any new functionality
3. **Maintain minimum coverage**: 80% for migration, 85% for superset
4. **Test commands**:
   - PowerShell: `.\run-tests.ps1`
   - Bash: `./run-tests.sh`

## Coding Standards

### Python

```python
# Required: Type hints and docstrings
def process_data(input_data: dict) -> Optional[str]:
    """
    Process input data and return result.
    
    Args:
        input_data: Dictionary containing data to process
        
    Returns:
        Processed string or None if processing fails
        
    Raises:
        ValueError: If input_data is invalid
    """
    pass
```

### SQL

```sql
-- Use parameterized queries
-- BAD:
-- cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

-- GOOD:
-- cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

### Environment Variables

```bash
# Always use environment variables for:
# - Database credentials
# - API keys
# - Secret keys
# - External service URLs
```

## File Structure Guidelines

```
postgres_docker/
├── migration/          # Migration tools (Python)
│   ├── tests/         # Migration tests
│   └── logs/          # Migration logs (gitignored)
├── superset/           # Superset configuration
│   ├── config/        # Superset Python config
│   ├── assets/        # Custom assets
│   └── tests/         # Superset tests
├── init/               # Database initialization
└── apache-superset-src/ # DO NOT MODIFY (source code)
```

## Allowed Modifications

1. **Bug fixes**: With clear justification and tests
2. **Test additions**: Always welcome
3. **Documentation improvements**: In English only
4. **Code comments**: In English only
5. **Minor refactoring**: With test coverage

## Forbidden Modifications

1. Adding new npm/pip dependencies
2. Changing Docker service configuration
3. Modifying database connection parameters
4. Disabling security features
5. Writing content in non-English languages
6. Adding emojis or decorative characters

## Commit Message Format

```
<type>: <description>

Types:
- Add: New feature or file
- Fix: Bug fix
- Update: Modification to existing feature
- Refactor: Code refactoring
- Test: Test additions or modifications
- Docs: Documentation changes
- Chore: Maintenance tasks
```

## Review Checklist

Before submitting code:

- [ ] All code and comments are in English
- [ ] No hardcoded secrets or credentials
- [ ] Tests pass: `.\run-tests.ps1`
- [ ] No new dependencies added
- [ ] No emojis in code or documentation
- [ ] Docstrings for all public functions
- [ ] Type hints for all function parameters

## Contact

For questions or clarifications, contact:

- **Author**: Marie Challet
- **Organization**: FormaSup Auvergne
