# Testing Guide

## Quick Start

```bash
# Just run tests - production databases are automatically protected
task test
```

## How It Works

The test suite automatically:
- Detects if production database variables (`MONGODB_DB=ebl` or `ebldev`) are set
- Unsets them automatically with a clear warning
- Sets up an isolated in-memory MongoDB instance
- Creates a unique test database for each test session
- Cleans up after tests complete

**No manual setup required** - just run `poetry run pytest`.

## Common Commands

```bash
# Run using task commands
task test
task test-cov

# Run all tests
poetry run pytest

# Run specific test directory
poetry run pytest ebl/tests/atf_importer/

# Run specific test with verbose output
poetry run pytest ebl/tests/atf_importer/test_atf_importer_workflow.py::test_logger_writes_files -xvs

# Run with coverage
poetry run pytest --cov=ebl --cov-report=html
```

## Safety Mechanisms

**Automatic Protection Layers:**

1. **Root conftest.py** - Detects and unsets production database variables at import time
2. **pytest_configure hook** - Sets up in-memory MongoDB with unique database name (`ebltest_*`)
3. **Database fixtures** - Runtime validation of database names
4. **Test data setup** - Validates database names before populating

## What Happens with Production Variables Set

If you run tests with production database variables set:

```bash
$ MONGODB_DB=ebl poetry run pytest
```

You'll see this warning:
```
⚠️  PRODUCTION DATABASE DETECTED: MONGODB_DB='ebl'
For safety, automatically unsetting production environment variables.
Tests will use an isolated in-memory database instead.
```

Then tests run normally with in-memory database. **No action needed.**

## Performance Notes

**First test run may take 30-40 seconds** due to:
- Lark parser initialization (~30 seconds) - one-time cost per session
- In-memory MongoDB startup (~5-10 seconds)

**Optimize test speed:**
- Run specific test files instead of entire suite
- Use `pytest -n auto` for parallel execution
- Use `--lf` (last failed) or `--ff` (failed first) flags

## Troubleshooting

**Production database warning**: Automatic protection working correctly - no action needed

**Tests timeout during collection**: Normal for first run (Lark parser initialization ~30s)

**Missing dependencies**: Run `poetry install --no-root`

**In-memory MongoDB download issues**: Check network or set `CI=true` to use external MongoDB

## CI/CD

Set `CI=true` to use CI-provided MongoDB instead of in-memory:
```yaml
env:
  CI: true
  MONGODB_URI: mongodb://localhost:27017
  MONGODB_DB: ebltest_ci
```

## Best Practices

**DO:**
- Use `poetry run pytest` for running tests
- Trust the automatic production database protection
- Use existing fixtures (`database`, `fragment_repository`, etc.)
- Follow test database naming convention (`ebltest_*`)

**DON'T:**
- Never commit production credentials
- Never manually override safety mechanisms
- Never use real MongoDB URIs in test code

## Security

⚠️ **Production databases are automatically protected** - multiple safety layers ensure tests never connect to production, even if environment variables are set.
