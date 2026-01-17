# Test Suite Quick Start Guide

## Setup (One-time)

### 1. Install Dependencies
```bash
cd src/web/backend
pip install -e ".[dev]"
```

### 2. Create Test Database
```bash
# Using psql
psql -U postgres -c "CREATE DATABASE bootstrap_test;"

# Or using createdb
createdb -U postgres bootstrap_test
```

### 3. Verify Setup
```bash
pytest --version
pytest --collect-only tests/
```

## Running Tests

### Windows
```bash
# All tests
run_tests.bat all

# Project API tests only
run_tests.bat projects

# With coverage report
run_tests.bat coverage

# Fast tests only (skip slow tests)
run_tests.bat fast
```

### Linux/Mac
```bash
# Make script executable (first time only)
chmod +x run_tests.sh

# All tests
./run_tests.sh all

# Project API tests only
./run_tests.sh projects

# With coverage report
./run_tests.sh coverage

# Fast tests only
./run_tests.sh fast
```

### Direct pytest Commands
```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_api_projects.py

# Specific class
pytest tests/test_api_projects.py::TestProjectCreation

# Specific test
pytest tests/test_api_projects.py::TestProjectCreation::test_create_project_discovery_mode

# With verbose output
pytest tests/ -v

# With output capture disabled (see print statements)
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Run last failed tests
pytest tests/ --lf

# Show coverage
pytest tests/ --cov=app

# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
```

## Test Structure Overview

```
tests/
├── conftest.py                 # Fixtures and test configuration
├── test_api_projects.py        # 38+ test cases for project API
├── __init__.py                # Package marker
├── README.md                  # Detailed documentation
├── QUICKSTART.md              # This file
└── TEST_SUMMARY.md            # Test coverage summary
```

## Test Categories

| Category | Tests | Description |
|----------|-------|-------------|
| Project Creation | 5 | Discovery & direct mode creation |
| Project Listing | 4 | List, filter, paginate projects |
| Project Detail | 4 | Get details, progress, artifacts |
| Project Approval | 8 | Approve/reject workflow phases |
| Project Cancellation | 4 | Cancel projects, validation |
| Spec Validation | 4 | Validate project specifications |
| WebSocket | 4 | Real-time updates, connections |
| Edge Cases | 5 | Concurrency, performance, edge cases |

**Total: 38+ test cases**

## Common Testing Scenarios

### 1. Test Single Endpoint
```bash
pytest tests/test_api_projects.py::TestProjectCreation::test_create_project_discovery_mode -v
```

### 2. Test All Creation Endpoints
```bash
pytest tests/test_api_projects.py::TestProjectCreation -v
```

### 3. Test with Coverage for Specific Module
```bash
pytest tests/test_api_projects.py --cov=app.api.v1.projects --cov-report=term-missing
```

### 4. Run Tests Matching Pattern
```bash
pytest tests/ -k "creation" -v
pytest tests/ -k "websocket" -v
pytest tests/ -k "approval" -v
```

### 5. Debug Failing Test
```bash
# Run with full output
pytest tests/test_api_projects.py::TestProjectCreation::test_create_project_discovery_mode -vv -s

# Run with Python debugger on failure
pytest tests/ --pdb
```

## Expected Output

### Successful Test Run
```
================================ test session starts ================================
platform win32 -- Python 3.11.0, pytest-7.4.0, pluggy-1.3.0
rootdir: C:\Users\ravur\PycharmProjects\Project-Bootstrap-Web-App\src\web\backend
configfile: pytest.ini
plugins: asyncio-0.23.0, cov-4.1.0
collected 38 items

tests/test_api_projects.py::TestProjectCreation::test_create_project_discovery_mode PASSED [  2%]
tests/test_api_projects.py::TestProjectCreation::test_create_project_direct_mode PASSED [  5%]
...
tests/test_api_projects.py::TestEdgeCases::test_approve_already_approved_project PASSED [100%]

================================ 38 passed in 12.34s ================================
```

### Coverage Report
```
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
app/__init__.py                          0      0   100%
app/api/__init__.py                      0      0   100%
app/api/v1/__init__.py                   0      0   100%
app/api/v1/projects.py                 142      5    96%   45-47, 89, 156
app/models/project.py                   45      2    95%   72-73
app/schemas/project.py                  87      3    96%   24, 56, 89
------------------------------------------------------------------
TOTAL                                  274     10    96%
```

## Troubleshooting

### Test Database Not Found
```bash
# Create the database
psql -U postgres -c "CREATE DATABASE bootstrap_test;"
```

### Import Errors
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Or reinstall
pip install --force-reinstall -e ".[dev]"
```

### Connection Errors
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Update DATABASE_URL if needed
export DATABASE_URL="postgresql+asyncpg://user:pass@host:port/bootstrap_test"
```

### Fixture Errors
```bash
# Clear pytest cache
pytest --cache-clear

# Or delete cache directory
rm -rf .pytest_cache
```

### Async Errors
Make sure `pytest-asyncio` is installed and `pytest.ini` has:
```ini
[pytest]
asyncio_mode = auto
```

## Writing New Tests

### 1. Add Test to Existing Class
```python
# In tests/test_api_projects.py
class TestProjectCreation:
    @pytest.mark.asyncio
    async def test_my_new_feature(self, client: AsyncClient):
        response = await client.post("/api/v1/projects", json={...})
        assert response.status_code == 201
```

### 2. Create New Test Class
```python
class TestMyNewFeature:
    """Test my new feature."""

    @pytest.mark.asyncio
    async def test_basic_functionality(self, client: AsyncClient):
        # Test implementation
        pass
```

### 3. Add New Fixture
```python
# In tests/conftest.py
@pytest.fixture
async def my_custom_fixture(test_session):
    # Setup
    data = create_test_data()
    yield data
    # Teardown (optional)
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd src/web/backend
          pip install -e ".[dev]"

      - name: Create test database
        run: |
          PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE bootstrap_test;"

      - name: Run tests
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/bootstrap_test
        run: |
          cd src/web/backend
          pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Best Practices

1. **Run tests before committing**
   ```bash
   pytest tests/ -v
   ```

2. **Check coverage regularly**
   ```bash
   pytest tests/ --cov=app --cov-report=term-missing
   ```

3. **Keep tests fast** - Mock external dependencies

4. **Write descriptive test names** - Test name should explain what is tested

5. **One assertion per test** - Or closely related assertions

6. **Use fixtures** - Don't repeat setup code

7. **Test edge cases** - Not just happy paths

## Resources

- **README.md** - Detailed test documentation
- **TEST_SUMMARY.md** - Coverage summary
- **conftest.py** - Available fixtures
- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio documentation](https://pytest-asyncio.readthedocs.io/)
