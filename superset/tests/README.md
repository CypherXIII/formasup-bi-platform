# Superset Module Tests

> Test suite for the Superset configuration and build scripts.

[![Tests](https://img.shields.io/badge/Tests-11%20Passed-brightgreen)](#running-tests)
[![Coverage](https://img.shields.io/badge/Coverage-85%25+-yellowgreen)](#running-tests)

---

## Test Structure

```text
tests/
├── test_config.py    # Configuration validation tests
├── test_build.py     # Build script tests
├── __init__.py       # Test module init
└── README.md         # This documentation
```

---

## Test Categories

### Configuration Tests (`test_config.py`)

- **Environment Variables**: SECRET_KEY, DATABASE_URL
- **Branding**: APP_NAME, APP_ICON, LOGO_*
- **French Locale**: LANGUAGES, BABEL_DEFAULT_LOCALE
- **Validation**: Data types, formats, default values

### Build Tests (`test_build.py`)

- **PowerShell Script**: Existence, parameters, content
- **Artifacts**: Dockerfile, docker-compose.yml
- **Source Code**: Presence of apache-superset-src
- **Translations**: backup-messages.po file

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
pytest --cov=config --cov-report=html
```

### Specific Test Categories

```bash
# Configuration tests only
pytest -m config

# Build tests only
pytest -m build

# Specific test
pytest tests/test_config.py::TestSupersetConfig::test_language_configuration -v
```

---

## Test Configuration

Configuration is defined in `pytest.ini`:

- **Minimum coverage**: 85% (stricter than migration)
- **HTML reports**: Generated in `htmlcov/`
- **Markers**: Filter tests by domain

---

## Environment Variables

Tests use mocked environment variables:

| Variable              | Purpose                    |
|-----------------------|----------------------------|
| `SUPERSET_SECRET_KEY` | Custom secret key          |
| `DATABASE_URL`        | Custom database URI        |

---

## Test Metrics

After running tests, verify:

- **Coverage**: At least 85% of `config/` lines
- **Pass Rate**: All tests pass
- **Performance**: Tests complete in < 10 seconds

---

## Tested Configuration

The Superset configuration is validated for:

| Category     | Validated Items                           |
|--------------|-------------------------------------------|
| **Security** | SECRET_KEY, WTF_CSRF_ENABLED              |
| **Database** | SQLALCHEMY_DATABASE_URI                   |
| **Branding** | APP_NAME, icons, logos                    |
| **Language** | 100% French interface                     |
| **Timezone** | Europe/Paris                              |

---

## Tested Build Scripts

The `build-superset-fr.ps1` script is validated for:

- **Parameters**: SupersetVersion, ImageName, NoBuildCache
- **Content**: BUILD_TRANSLATIONS=true instruction
- **Compliance**: Official Superset build procedure

---

## Adding New Tests

### Guidelines

1. **Config tests**: Add to `test_config.py`
2. **Build tests**: Add to `test_build.py`
3. **Markers**: Use `@pytest.mark.config`, `@pytest.mark.build`
4. **Isolation**: Mock environment variables

### Example

```python
class TestNewFeature:
    """Tests for new configuration feature."""

    def test_feature_exists(self):
        """Test that feature is configured."""
        assert hasattr(config, 'NEW_FEATURE')

    def test_feature_type(self):
        """Test that feature has correct type."""
        assert isinstance(config.NEW_FEATURE, expected_type)
```

---

## CI/CD Integration

Tests are designed for CI/CD pipelines:

```yaml
# Example GitHub Actions step
- name: Run Superset Tests
  run: |
    cd superset
    pip install pytest pytest-cov
    pytest --cov=config --cov-fail-under=85
```

---

## Credits

**Author**: Marie Challet  
**Organization**: FormaSup Auvergne  
**Version**: 1.0.0  
**Last Updated**: January 2026
