## Description

<!-- Briefly describe the changes in this PR -->

## Type of Change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Test additions or modifications

## Related Issues

<!-- Link any related issues using #issue_number -->

Fixes #

## Checklist

### Code Quality

- [ ] All code and comments are in English
- [ ] No emojis in code or documentation
- [ ] Docstrings added for all public functions
- [ ] Type hints for all function parameters

### Security (ISO 27001 / RGPD)

- [ ] No hardcoded secrets or credentials
- [ ] Environment variables used for sensitive data
- [ ] Parameterized queries for database operations
- [ ] User inputs are validated

### Testing

- [ ] Tests pass locally: `.\run-tests.ps1`
- [ ] New tests added for new functionality
- [ ] Coverage requirements met (80% migration, 85% superset)

### Architecture

- [ ] No new dependencies added (or explicitly approved)
- [ ] No modifications to docker-compose.yml (or explicitly requested)
- [ ] No modifications to superset_config.py (or explicitly requested)
- [ ] Database schema changes include migration scripts

## Screenshots (if applicable)

<!-- Add screenshots for UI changes -->

## Additional Notes

<!-- Any additional information for reviewers -->
