# Orchestration Engine Tests

Comprehensive test suite for the Project Bootstrap Web App orchestration engine.

## Test Coverage

### 1. Workflow Initialization Tests
- Discovery mode initialization
- Direct mode initialization
- Timestamp validation
- Async task creation
- Domain expert detection during initialization

### 2. Phase Execution Order Tests
- Discovery mode phase sequence (8 phases)
- Direct mode phase sequence (4 phases)
- Phase skipping for completed phases
- Resume workflow validation

### 3. Parallel Agent Execution Tests
- Concurrent agent execution
- Partial failure handling
- Agent activation matrix (by project type)
- Architecture agent selection
- Code generation agent selection

### 4. Approval Gate Tests
- Workflow pause at approval gates
- Workflow resume after approval
- Approval gate creation with artifacts
- Approval rejection handling
- WebSocket notification (when available)

### 5. Error Handling and Recovery Tests
- Phase execution error handling
- Agent timeout handling
- Missing agent handling
- Workflow not found errors
- State persistence on errors
- Circular dependency detection

### 6. Progress Tracking Tests
- Running workflow progress
- Non-existent workflow handling
- Completed phases tracking
- Current phase tracking

### 7. Domain Expert Detection Tests
- Healthcare domain detection
- Multiple domain detection
- Finance and ecommerce detection
- No domain experts in Direct mode

### 8. Dependency Graph Execution Tests
- Scaffolding phase dependency order
- Dependency resolver batch grouping
- Parallel batch execution

### 9. Workflow Completion Tests
- Completion status setting
- All phases completed scenario
- Completion timestamp validation

## Running Tests

### Prerequisites

Install required dependencies:

```bash
pip install pytest pytest-asyncio structlog
```

### Run All Tests

```bash
# From project root
pytest src/orchestrator/tests/

# With verbose output
pytest -v src/orchestrator/tests/

# With coverage report
pytest --cov=src/orchestrator --cov-report=html src/orchestrator/tests/
```

### Run Specific Test Classes

```bash
# Test workflow initialization only
pytest src/orchestrator/tests/test_engine.py::TestWorkflowInitialization -v

# Test parallel execution only
pytest src/orchestrator/tests/test_engine.py::TestParallelAgentExecution -v

# Test approval gates only
pytest src/orchestrator/tests/test_engine.py::TestApprovalGateHandling -v

# Test error handling only
pytest src/orchestrator/tests/test_engine.py::TestErrorHandlingAndRecovery -v
```

### Run Specific Tests

```bash
# Run single test
pytest src/orchestrator/tests/test_engine.py::TestWorkflowInitialization::test_discovery_mode_initialization -v

# Run tests matching pattern
pytest -k "approval" src/orchestrator/tests/
pytest -k "error" src/orchestrator/tests/
```

### Run with Markers

```bash
# Run only async tests
pytest -m asyncio src/orchestrator/tests/

# Skip slow tests (if marked)
pytest -m "not slow" src/orchestrator/tests/
```

### Debug Mode

```bash
# Show print statements and verbose output
pytest -v -s src/orchestrator/tests/

# Stop on first failure
pytest -x src/orchestrator/tests/

# Drop into debugger on failure
pytest --pdb src/orchestrator/tests/
```

## Test Structure

```
src/orchestrator/tests/
├── __init__.py                 # Package marker
├── conftest.py                 # Shared fixtures and configuration
├── test_engine.py              # Main engine tests (this file)
└── README.md                   # This file
```

## Test Fixtures

### Mock Fixtures (from test_engine.py)
- `mock_agent_registry` - Mocked agent registry
- `mock_parallel_executor` - Parallel execution coordinator
- `mock_dependency_resolver` - Dependency resolution
- `mock_phase_executor` - Phase execution handler
- `mock_state_manager` - State persistence
- `mock_approval_manager` - Approval gate management
- `mock_domain_detector` - Domain expert detection
- `orchestration_engine` - Fully configured engine instance

### Data Fixtures (from conftest.py)
- `sample_discovery_input` - Sample Discovery mode input
- `sample_direct_input` - Sample Direct mode input
- `sample_healthcare_input` - Healthcare domain input
- `sample_ecommerce_input` - E-commerce domain input
- `sample_ml_project_input` - ML project input

## Coverage Goals

| Component | Target Coverage |
|-----------|----------------|
| engine.py | 90%+ |
| phase_executor.py | 85%+ |
| workflow.py | 95%+ |
| state_manager.py | 80%+ |
| approval_manager.py | 80%+ |

## Test Data

Tests use realistic project scenarios:
- Healthcare management system (HIPAA compliance)
- E-commerce platform (PCI-DSS compliance)
- Task management web app
- REST API services
- ML/AI projects

## Common Issues

### Async Tests Not Running
Ensure `pytest-asyncio` is installed:
```bash
pip install pytest-asyncio
```

### Import Errors
Run tests from project root, not from tests directory:
```bash
# Correct
pytest src/orchestrator/tests/

# Wrong
cd src/orchestrator/tests && pytest
```

### Timing Issues
Some tests use `asyncio.sleep()` for async task coordination. If tests are flaky, increase sleep durations.

## Contributing

When adding new tests:
1. Follow AAA pattern (Arrange, Act, Assert)
2. Use descriptive test names: `test_<scenario>_<expected_behavior>`
3. Add docstrings explaining what is being tested
4. Group related tests in test classes
5. Use appropriate fixtures from conftest.py
6. Mark async tests with `@pytest.mark.asyncio`

## Continuous Integration

Tests run automatically on:
- Pull request creation
- Commits to main branch
- Pre-commit hooks (if configured)

CI configuration: `.github/workflows/test.yml`
