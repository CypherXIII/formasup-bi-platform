# Migration Module Tests

> Test suite for the MariaDB to PostgreSQL migration system.

[![Tests](https://img.shields.io/badge/Tests-54%20Passed-brightgreen)](#running-tests)
[![Coverage](https://img.shields.io/badge/Coverage-80%25+-yellowgreen)](#running-tests)

---

## Test Structure

```text
tests/
├── test_migration.py     # Core migration tests (config, args, metrics)
├── test_database.py      # Database operation tests
├── test_integration.py   # End-to-end workflow tests
├── test_utils.py         # Utility and API client tests
├── __init__.py           # Test module init
└── README.md             # This documentation
```

---

## Test Categories

### Unit Tests (`test_migration.py`, `test_database.py`)

- **Config**: Configuration validation and initialization
- **Arguments**: CLI argument parsing
- **Database**: Connection handling, queries, metrics
- **Migration Core**: Data migration logic

### Integration Tests (`test_integration.py`)

- **Complete Workflow**: End-to-end migration
- **Error Handling**: Connection failures, migration errors
- **Config Validation**: Complete and partial configurations

### Utility Tests (`test_utils.py`)

- **Logging**: Logger configuration and output
- **API Client**: HTTP requests, rate limiting
- **DB Operations**: Temporary schemas, cleanup

---

## Running Tests

### All Tests

```bash
pytest
```

### With Verbose Output

```bash
pytest -v
```

### With Coverage Report

```bash
pytest --cov=. --cov-report=html
```

### Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Slow tests (with real databases)
pytest -m slow
```

### Specific Test File

```bash
pytest tests/test_database.py
pytest tests/test_integration.py -v
```

---

## Test Configuration

Configuration is defined in `pytest.ini`:

- **Minimum coverage**: 80%
- **HTML reports**: Generated in `htmlcov/`
- **Markers**: Filter tests by category

---

## Mocks and Fixtures

Tests use mocks for external dependencies:

| Dependency           | Mock Method                         |
|----------------------|-------------------------------------|
| PostgreSQL           | `patch('psycopg2.connect')`         |
| MariaDB              | `patch('pymysql.connect')`          |
| Environment          | `patch.dict(os.environ, {...})`     |
| Temporary Files      | `tempfile.NamedTemporaryFile`       |
| HTTP Requests        | `patch('requests.Session')`         |

---

## Test Environment Variables

Tests use mocked environment variables:

```python
{
    'MARIADB_HOST': 'test-host',
    'MARIADB_USER': 'test-user',
    'MARIADB_PASSWORD': 'test-pass',
    'MARIADB_DB': 'test-db',
    'PG_HOST': 'test-host',
    'PG_USER': 'test-user',
    'PG_PASSWORD': 'test-pass',
    'PG_DB': 'test-db',
    'PG_SCHEMA': 'staging',
    'BATCH_SIZE': '100'
}
```

---

## Test Metrics

After running tests, verify:

- **Coverage**: At least 80% of source lines
- **Pass Rate**: All tests pass
- **Performance**: Tests complete in < 5 seconds

---

## Adding New Tests

### Guidelines

1. **Isolation**: Use mocks for all external dependencies
2. **Naming**: Use descriptive test method names
3. **Documentation**: Add docstrings explaining test purpose
4. **Markers**: Use appropriate pytest markers

### Example

```python
class TestNewFeature:
    """Tests for new feature X."""

    def test_basic_functionality(self):
        """Test that feature X works with valid input."""
        result = new_feature(valid_input)
        assert result == expected_output

    def test_error_handling(self):
        """Test that feature X raises error on invalid input."""
        with pytest.raises(ValueError):
            new_feature(invalid_input)
```

---

## CI/CD Integration

Tests are designed for CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Tests
  run: |
    pip install pytest pytest-cov
    pytest --cov=. --cov-fail-under=80
```

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Last Updated**: January 2026
