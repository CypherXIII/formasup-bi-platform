# LLM Instructions - FormaSup BI Platform

> This file provides guidance for AI assistants (Claude, Copilot, ChatGPT, etc.) working with this repository.

---

## Project Overview

**FormaSup BI Platform** is a production Business Intelligence system based on Apache Superset 6.0.0. It is deployed for FormaSup Auvergne and academic partners for educational data analysis.

### Key Characteristics

- **Production system**: Real users depend on this
- **French localization**: Complete French interface
- **Security-sensitive**: Contains database credentials configuration
- **Docker-based**: Multi-container orchestration
- **Submodule architecture**: Main repo + migration tools + superset config

---

## Allowed Actions

AI assistants MAY:

1. **Fix bugs** in existing code with clear justification
2. **Add tests** for existing functionality
3. **Improve documentation** while maintaining English language
4. **Refactor** small sections with equivalent functionality
5. **Add comments** explaining complex logic
6. **Update dependencies** for security patches only
7. **Optimize performance** without changing behavior

---

## Forbidden Actions

AI assistants MUST NOT:

1. **Add new dependencies** without explicit user request
2. **Change architecture** (Docker services, database structure)
3. **Modify security settings** (SECRET_KEY, passwords, CSRF)
4. **Remove functionality** without explicit request
5. **Change database schemas** or migration logic
6. **Modify production configurations** in docker-compose.yml
7. **Write non-English content** in code, comments, or documentation
8. **Add emojis** to any files (code, scripts, documentation)
9. **Expose secrets** or hardcode credentials
10. **Bypass tests** or reduce test coverage

---

## Code Standards

### Python

```python
# Use type hints
def migrate_table(source: Connection, target: Connection, table: str) -> int:
    """
    Migrate a single table from source to target.

    Args:
        source: Source database connection
        target: Target database connection
        table: Table name to migrate

    Returns:
        Number of rows migrated

    Raises:
        MigrationError: If migration fails
    """
    pass
```

### PowerShell

```powershell
<#
.SYNOPSIS
    Brief description of the script

.DESCRIPTION
    Detailed description

.PARAMETER Name
    Parameter description

.EXAMPLE
    Example usage
#>
```

### Documentation

- All content in **English**
- Use **Markdown** formatting
- Include **code examples** where appropriate
- Add **warnings** for security-sensitive operations

---

## Security Rules

### Never Do

- Hardcode passwords, API keys, or secrets
- Disable CSRF protection
- Expose database ports publicly
- Log sensitive information
- Skip input validation

### Always Do

- Use environment variables for secrets
- Validate all user inputs
- Use parameterized queries
- Log actions without sensitive data
- Follow least privilege principle

---

## Testing Requirements

### Before Any Change

1. Run existing tests: `./run-tests.sh`
2. Verify all tests pass
3. Check coverage meets minimums

### After Any Change

1. Add tests for new functionality
2. Update existing tests if behavior changed
3. Verify coverage did not decrease

### Coverage Minimums

- Migration module: 80%
- Superset module: 85%

---

## File Organization

### Do Not Modify

- `docker-compose.yml` (production config)
- `superset/config/superset_config.py` (security settings)
- `.env` files (user credentials)
- `apache-superset-src/` (external source)

### Safe to Modify

- Test files (`tests/`)
- Documentation (`*.md`)
- Build scripts (`scripts/`)
- Development utilities

---

## Commit Guidelines

### Message Format

```
<type>: <description>

Types:
- Add: New feature
- Fix: Bug fix
- Update: Feature modification
- Refactor: Code restructure
- Test: Test addition/modification
- Docs: Documentation only
- Chore: Maintenance
```

### Examples

```
Add: Rate limiting for API client
Fix: Connection timeout handling
Docs: Update deployment instructions
Test: Add coverage for database module
```

---

## Questions to Ask

Before making changes, consider:

1. **Is this production-safe?** Could this break deployed systems?
2. **Is this tested?** Are there tests covering this change?
3. **Is this documented?** Will other developers understand?
4. **Is this secure?** Could this expose sensitive data?
5. **Is this in English?** All content must be English.

---

## Getting Help

If unclear about requirements:

1. Document your assumptions
2. Proceed conservatively
3. Add TODO comments for review
4. Request clarification from maintainer

---

## Version

- **Document version**: 1.0.0
- **Last updated**: January 2026
- **Author**: Marie Challet
- **Organization**: FormaSup Auvergne
