# AI Rules and Constraints

> Strict rules for AI assistants working with this repository.

---

## Scope Definition

This repository is a **production Business Intelligence system** operating under:

- **ISO 27001:2022** Information Security Management System compliance
- **RGPD/GDPR** General Data Protection Regulation compliance
- **Regular security audits** (internal and external)

All AI interactions must respect the following constraints and security requirements.

---

## CRITICAL RULES

### 1. Language

- **ALL content must be in English**
- Comments, documentation, variable names, commit messages
- No exceptions

### 2. Security (ISO 27001 / RGPD Compliance)

- **NEVER expose credentials** (ISO 27001 A.9)
- **NEVER disable security features** (ISO 27001 A.12)
- **NEVER log sensitive data** (RGPD Art. 32)
- **ALWAYS use environment variables** (ISO 27001 A.9)
- **CONSIDER retention periods** when handling data (RGPD Art. 5)
- **PRESERVE audit trails** for compliance (ISO 27001 A.12.4)

### 3. Architecture

- **DO NOT change Docker service definitions**
- **DO NOT modify database schemas**
- **DO NOT add new services without explicit request**
- **DO NOT remove existing functionality**
- **DO NOT modify** `docker-compose.yml` or `superset/config/superset_config.py` without explicit approval

### 4. Dependencies

- **DO NOT add new dependencies without explicit request**
- **DO NOT upgrade major versions without explicit request**
- **MAY upgrade patch versions for security fixes**

### 5. Testing

- **MUST run tests before suggesting changes**
- **MUST maintain or improve test coverage**
- **MUST NOT skip or disable tests**
- Run test suite: `./run-tests.sh` (bash) or `./run-tests.ps1` (PowerShell)
- Coverage minima: migration ≥ 80%, superset ≥ 85%

### 6. Sensitive Outputs

- Never commit migration reports: `siret_corrections.txt`, `siret_invalid.txt`, `siret_errors_api.txt`
- Keep backups and dumps out of version control except explicitly whitelisted items

---

## Coding Standards

### Python

| Rule                    | Requirement                      |
|-------------------------|----------------------------------|
| Style                   | PEP 8                            |
| Type hints              | Required for public functions    |
| Docstrings              | Required for modules and classes |
| Line length             | 100 characters maximum           |
| Imports                 | Sorted, grouped by type          |

### PowerShell

| Rule                    | Requirement                      |
|-------------------------|----------------------------------|
| Comment headers         | Required for scripts             |
| Error handling          | Use try/catch blocks             |
| Parameter validation    | Use [CmdletBinding()]            |

### Markdown

| Rule                    | Requirement                      |
|-------------------------|----------------------------------|
| Headings                | ATX style (#)                    |
| Code blocks             | With language specifier          |
| Links                   | Relative paths when possible     |

---

## Prohibited Patterns

### Code

```python
# FORBIDDEN: Hardcoded credentials
password = "secret123"

# FORBIDDEN: Disabled security
WTF_CSRF_ENABLED = False

# FORBIDDEN: Logging secrets
logger.info(f"Password: {password}")
```

### Documentation

```markdown
<!-- FORBIDDEN: Non-English content -->
## Configuration (Configuración)

<!-- FORBIDDEN: Emojis -->
## 🚀 Getting Started
```

---

## Allowed Modifications

| Category      | Allowed Without Request          | Requires Explicit Request       |
|---------------|----------------------------------|---------------------------------|
| Tests         | Add new tests                    | Remove or skip tests            |
| Documentation | Fix typos, improve clarity       | Change structure                |
| Comments      | Add explanatory comments         | Remove existing comments        |
| Formatting    | Apply style guidelines           | Change code logic               |
| Security      | Add validation, improve safety   | Remove security checks          |

---

## Review Checklist

Before submitting any change:

- [ ] All tests pass
- [ ] No new dependencies added
- [ ] No security features disabled
- [ ] All content is in English
- [ ] No emojis in any file
- [ ] No hardcoded credentials
- [ ] Documentation updated if needed
- [ ] Code follows style guidelines

---

## Escalation

If a requested change would violate these rules:

1. **Explain** why the change is problematic
2. **Suggest** a safe alternative
3. **Document** the constraint
4. **Request** explicit confirmation before proceeding

---

## Enforcement

These rules are:

- **Mandatory**: No exceptions without explicit override
- **Auditable**: Changes will be reviewed against these rules
- **Version-controlled**: Changes to rules require approval

---

## Version

- **Version**: 1.2.0
- **Date**: January 2026
- **Author**: Marie Challet
- **Compliance**: ISO 27001:2022, RGPD
