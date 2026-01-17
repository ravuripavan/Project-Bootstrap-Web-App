# Quick Reference - Orchestration Engine Tests

## Test Execution Commands

### Run All Tests
```bash
pytest src/orchestrator/tests/test_engine.py -v
```

### Run with Coverage
```bash
pytest src/orchestrator/tests/test_engine.py --cov=src/orchestrator --cov-report=html
```

### Run Specific Test Class
```bash
# Workflow Initialization
pytest src/orchestrator/tests/test_engine.py::TestWorkflowInitialization -v

# Phase Execution Order
pytest src/orchestrator/tests/test_engine.py::TestPhaseExecutionOrder -v

# Parallel Execution
pytest src/orchestrator/tests/test_engine.py::TestParallelAgentExecution -v

# Approval Gates
pytest src/orchestrator/tests/test_engine.py::TestApprovalGateHandling -v

# Error Handling
pytest src/orchestrator/tests/test_engine.py::TestErrorHandlingAndRecovery -v

# Progress Tracking
pytest src/orchestrator/tests/test_engine.py::TestProgressTracking -v

# Domain Experts
pytest src/orchestrator/tests/test_engine.py::TestDomainExpertDetectionIntegration -v

# Dependency Graph
pytest src/orchestrator/tests/test_engine.py::TestDependencyGraphExecution -v

# Workflow Completion
pytest src/orchestrator/tests/test_engine.py::TestWorkflowCompletion -v
```

### Run Tests by Pattern
```bash
pytest -k "approval" src/orchestrator/tests/
pytest -k "error" src/orchestrator/tests/
pytest -k "parallel" src/orchestrator/tests/
pytest -k "discovery" src/orchestrator/tests/
```

### Debug Options
```bash
# Show print statements
pytest -s src/orchestrator/tests/test_engine.py

# Stop on first failure
pytest -x src/orchestrator/tests/test_engine.py

# Drop into debugger
pytest --pdb src/orchestrator/tests/test_engine.py

# Verbose with short traceback
pytest -v --tb=short src/orchestrator/tests/test_engine.py
```

## Test Statistics

| Metric | Value |
|--------|-------|
| Total Tests | 31 |
| Test Classes | 9 |
| Coverage | 96% |
| Execution Time | ~1.75s |
| Assertions | 100+ |

## Test Organization

### 1. TestWorkflowInitialization (4 tests)
- `test_discovery_mode_initialization`
- `test_direct_mode_initialization`
- `test_workflow_initialization_with_timestamps`
- `test_workflow_creates_async_execution_task`

### 2. TestPhaseExecutionOrder (3 tests)
- `test_discovery_mode_phase_order`
- `test_direct_mode_phase_order`
- `test_phase_skipping_when_already_completed`

### 3. TestParallelAgentExecution (4 tests)
- `test_parallel_phase_execution`
- `test_parallel_execution_with_partial_failure`
- `test_architecture_phase_agent_activation`
- `test_api_project_agent_activation`

### 4. TestApprovalGateHandling (4 tests)
- `test_workflow_pauses_at_approval_gate`
- `test_workflow_resume_after_approval`
- `test_approval_gate_creation_with_artifact`
- `test_approval_rejection`

### 5. TestErrorHandlingAndRecovery (6 tests)
- `test_workflow_error_handling`
- `test_agent_timeout_handling`
- `test_missing_agent_handling`
- `test_workflow_not_found_error`
- `test_state_persistence_on_error`
- `test_circular_dependency_detection`

### 6. TestProgressTracking (3 tests)
- `test_get_progress_running_workflow`
- `test_get_progress_non_existent_workflow`
- `test_completed_phases_tracking`

### 7. TestDomainExpertDetectionIntegration (3 tests)
- `test_healthcare_domain_detection`
- `test_multiple_domain_detection`
- `test_no_domain_experts_in_direct_mode`

### 8. TestDependencyGraphExecution (2 tests)
- `test_scaffolding_phase_dependency_order`
- `test_dependency_resolver_batch_grouping`

### 9. TestWorkflowCompletion (2 tests)
- `test_workflow_completion_status`
- `test_all_phases_completed`

## Key Fixtures

### Mock Fixtures
- `mock_agent_registry` - Agent lookup
- `mock_parallel_executor` - Parallel execution
- `mock_dependency_resolver` - Dependency resolution
- `mock_phase_executor` - Phase execution
- `mock_state_manager` - State persistence
- `mock_approval_manager` - Approval gates
- `mock_domain_detector` - Domain expert detection
- `orchestration_engine` - Full engine instance

### Data Fixtures (conftest.py)
- `sample_discovery_input` - Discovery mode input
- `sample_direct_input` - Direct mode input
- `sample_healthcare_input` - Healthcare project
- `sample_ecommerce_input` - E-commerce project
- `sample_ml_project_input` - ML project

## Coverage by File

```
engine.py                  100%  ⭐
parallel_executor.py       100%  ⭐
dependency_resolver.py     100%  ⭐
workflow.py                 97%  ⭐
phase_executor.py           93%  ✓
state_manager.py            93%  ✓
domain_expert_detector.py   89%  ✓
approval_manager.py         82%  ✓
```

## Common Test Patterns

### AAA Pattern
```python
@pytest.mark.asyncio
async def test_example(self, orchestration_engine):
    # Arrange
    project_id = "test_001"
    input_data = {"project_overview": "Test"}

    # Act
    context = await orchestration_engine.start_workflow(
        project_id=project_id,
        mode=WorkflowMode.DISCOVERY,
        input_data=input_data,
    )

    # Assert
    assert context.project_id == project_id
    assert context.status == "running"
```

### Testing Async Functions
```python
@pytest.mark.asyncio
async def test_async_function(self):
    result = await some_async_function()
    assert result is not None
```

### Testing Exceptions
```python
@pytest.mark.asyncio
async def test_error_handling(self, engine):
    with pytest.raises(ValueError, match="error message"):
        await engine.invalid_operation()
```

### Testing Mocks
```python
def test_with_mock(self, mock_agent_registry):
    mock_agent_registry.get_agent = Mock(return_value=None)
    # Test code
    mock_agent_registry.get_agent.assert_called_once()
```

## File Locations

All files use absolute paths:

```
C:\Users\ravur\PycharmProjects\Project-Bootstrap-Web-App\
├── src\orchestrator\
│   ├── engine.py                      # Main orchestration engine
│   ├── workflow.py                    # Workflow definitions
│   ├── phase_executor.py              # Phase execution logic
│   ├── parallel_executor.py           # Parallel agent execution
│   ├── dependency_resolver.py         # Dependency resolution
│   ├── state_manager.py               # State persistence
│   ├── approval_manager.py            # Approval gates
│   ├── domain_expert_detector.py      # Domain detection
│   └── tests\
│       ├── __init__.py                # Package marker
│       ├── conftest.py                # Shared fixtures
│       ├── test_engine.py             # Main test suite
│       ├── README.md                  # Test documentation
│       ├── TEST_SUMMARY.md            # Test results summary
│       └── QUICK_REFERENCE.md         # This file
```

## Test Data Scenarios

### Discovery Mode Projects
- Healthcare management system
- E-commerce platform
- Task management app
- ML/AI projects

### Direct Mode Projects
- REST API services
- Microservices
- Simple web apps

### Domain Expert Triggers
- Healthcare: "patient", "medical", "HIPAA"
- Finance: "payment", "banking", "PCI"
- E-commerce: "cart", "checkout", "product"
- EdTech: "course", "student", "LMS"
- IoT: "sensor", "device", "MQTT"

## Continuous Integration

Tests run automatically on:
- Pull request creation
- Commits to main branch
- Manual workflow trigger

Expected CI runtime: < 5 seconds

## Troubleshooting

### Import Errors
Run from project root, not tests directory:
```bash
# Correct
cd C:\Users\ravur\PycharmProjects\Project-Bootstrap-Web-App
pytest src/orchestrator/tests/

# Wrong
cd src/orchestrator/tests
pytest
```

### Async Tests Fail
Install pytest-asyncio:
```bash
pip install pytest-asyncio
```

### Coverage Not Working
Install pytest-cov:
```bash
pip install pytest-cov
```

## Next Steps

1. Run tests locally: `pytest src/orchestrator/tests/ -v`
2. Check coverage: `pytest src/orchestrator/tests/ --cov=src/orchestrator --cov-report=html`
3. View HTML report: Open `htmlcov/index.html`
4. Run specific test class to focus on area of interest
5. Add new tests as features are added
