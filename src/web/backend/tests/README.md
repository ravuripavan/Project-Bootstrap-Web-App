# Backend Test Suite

Comprehensive test suite for the Project Bootstrap Web App backend API.

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures and configuration
├── test_api_projects.py     # Project API endpoint tests
└── README.md               # This file
```

## Test Files

### `conftest.py`
Contains pytest fixtures for:
- `test_engine`: Test database engine with schema setup
- `test_session`: Async database session for tests
- `client`: HTTP test client with dependency overrides
- `mock_orchestration_service`: Mocked orchestration service
- `sample_project_*`: Pre-created project fixtures for various states

### `test_api_projects.py`
Comprehensive tests organized into classes:

#### TestProjectCreation
- Create project in discovery mode
- Create project in direct mode
- Input validation (name, overview length)
- Minimal configuration

#### TestProjectListing
- List all projects
- Filter by status
- Pagination
- Empty results

#### TestProjectDetail
- Get project details
- Get project with artifacts
- Get project progress
- Handle not found

#### TestProjectApproval
- Approve project phase
- Approve with feedback/modifications
- Reject project phase
- Validation and error handling

#### TestProjectCancellation
- Cancel running project
- Cancel pending project
- Cannot cancel completed project

#### TestSpecValidation
- Validate valid spec
- Detect validation warnings
- Detect validation errors
- Missing required fields

#### TestWebSocket
- Establish WebSocket connection
- Receive real-time updates
- Multiple concurrent connections
- Disconnect handling

#### TestEdgeCases
- Project name normalization
- Concurrent project creation
- Performance with many projects
- Double approval prevention

## Running Tests

### Run all tests
```bash
cd src/web/backend
pytest
```

### Run specific test file
```bash
pytest tests/test_api_projects.py
```

### Run specific test class
```bash
pytest tests/test_api_projects.py::TestProjectCreation
```

### Run specific test
```bash
pytest tests/test_api_projects.py::TestProjectCreation::test_create_project_discovery_mode
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html
```

### Run with verbose output
```bash
pytest -v
```

### Run and stop on first failure
```bash
pytest -x
```

## Test Database Setup

The tests use a separate test database to avoid interfering with development data:

**Database URL**: `postgresql+asyncpg://postgres:postgres@localhost:5432/bootstrap_test`

### Setup Test Database

```bash
# Create test database
createdb bootstrap_test

# Or using psql
psql -U postgres -c "CREATE DATABASE bootstrap_test;"
```

The test suite automatically creates and drops tables before/after test runs.

## Fixtures

### Database Fixtures
- `test_engine`: Database engine (session-scoped)
- `test_session`: Database session (function-scoped, auto-rollback)

### HTTP Client Fixtures
- `client`: AsyncClient configured with dependency overrides

### Mock Fixtures
- `mock_orchestration_service`: Mock for background workflow orchestration

### Sample Data Fixtures
- `sample_project_discovery`: Project in discovery mode (pending)
- `sample_project_direct`: Project in direct mode (executing)
- `sample_project_awaiting_approval`: Project awaiting approval with gate
- `sample_completed_project`: Completed project

## Writing New Tests

### Basic Test Structure

```python
import pytest
from httpx import AsyncClient

class TestMyFeature:
    """Test description."""

    @pytest.mark.asyncio
    async def test_my_feature(self, client: AsyncClient):
        """Test a specific behavior."""
        response = await client.post("/api/v1/endpoint", json={...})

        assert response.status_code == 200
        data = response.json()
        assert data["field"] == "expected_value"
```

### Using Fixtures

```python
@pytest.mark.asyncio
async def test_with_sample_project(
    client: AsyncClient,
    sample_project_discovery
):
    """Use pre-created project fixture."""
    project_id = sample_project_discovery.id
    response = await client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
```

### Mocking Services

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_with_mock(client: AsyncClient, mock_orchestration_service):
    """Test with mocked background service."""
    with patch(
        "app.api.v1.projects.get_orchestration_service",
        return_value=mock_orchestration_service
    ):
        response = await client.post("/api/v1/projects", json={...})

        # Verify mock was called
        mock_orchestration_service.start_workflow.assert_called_once()
```

## Test Coverage

Aim for >80% coverage on:
- API endpoints (routes)
- Service layer
- Database operations
- Input validation

Use `pytest-cov` to generate coverage reports:

```bash
pytest --cov=app --cov-report=term-missing
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Use fixtures with proper teardown or database rollback
3. **Naming**: Use descriptive test names that explain what is being tested
4. **Organization**: Group related tests in classes
5. **Assertions**: Use specific assertions with clear error messages
6. **Mocking**: Mock external dependencies (APIs, file system, background tasks)
7. **Edge Cases**: Test both happy paths and error conditions

## CI/CD Integration

These tests are designed to run in CI/CD pipelines. Ensure:
- Test database is available
- Environment variables are set
- Dependencies are installed (`pip install -r requirements.txt`)

Example GitHub Actions workflow:

```yaml
- name: Run tests
  env:
    DATABASE_URL: postgresql+asyncpg://postgres:postgres@localhost/bootstrap_test
  run: |
    pytest --cov=app --cov-report=xml
```
