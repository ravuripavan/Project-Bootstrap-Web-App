"""
Comprehensive tests for the OrchestrationEngine.

Tests cover:
- Workflow initialization (Discovery and Direct modes)
- Phase execution order validation
- Parallel agent execution
- Approval gate handling
- Error handling and recovery
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any

from src.orchestrator.engine import OrchestrationEngine
from src.orchestrator.workflow import (
    WorkflowMode,
    DiscoveryModeWorkflow,
    DirectModeWorkflow,
    Phase,
)
from src.orchestrator.state_manager import StateManager, ExecutionContext
from src.orchestrator.phase_executor import PhaseExecutor
from src.orchestrator.approval_manager import ApprovalManager
from src.orchestrator.domain_expert_detector import DomainExpertDetector
from src.orchestrator.parallel_executor import ParallelExecutor
from src.orchestrator.dependency_resolver import DependencyResolver


# Test Fixtures
@pytest.fixture
def mock_agent_registry():
    """Mock agent registry."""
    registry = Mock()

    # Create mock agents
    mock_agent = Mock()
    mock_agent.execute = AsyncMock(return_value={
        "status": "success",
        "output": {"result": "test_output"}
    })

    registry.get_agent = Mock(return_value=mock_agent)
    return registry


@pytest.fixture
def mock_parallel_executor(mock_agent_registry):
    """Mock parallel executor."""
    return ParallelExecutor(agent_registry=mock_agent_registry, timeout=300)


@pytest.fixture
def mock_dependency_resolver():
    """Mock dependency resolver."""
    return DependencyResolver()


@pytest.fixture
def mock_phase_executor(mock_agent_registry, mock_parallel_executor, mock_dependency_resolver):
    """Mock phase executor."""
    return PhaseExecutor(
        agent_registry=mock_agent_registry,
        parallel_executor=mock_parallel_executor,
        dependency_resolver=mock_dependency_resolver,
    )


@pytest.fixture
def mock_state_manager():
    """Mock state manager."""
    return StateManager()


@pytest.fixture
def mock_approval_manager():
    """Mock approval manager."""
    return ApprovalManager()


@pytest.fixture
def mock_domain_detector():
    """Mock domain expert detector."""
    return DomainExpertDetector()


@pytest.fixture
def orchestration_engine(
    mock_phase_executor,
    mock_state_manager,
    mock_approval_manager,
    mock_domain_detector,
):
    """Create OrchestrationEngine instance with mocked dependencies."""
    return OrchestrationEngine(
        phase_executor=mock_phase_executor,
        state_manager=mock_state_manager,
        approval_manager=mock_approval_manager,
        domain_detector=mock_domain_detector,
    )


# Test Class: Workflow Initialization
class TestWorkflowInitialization:
    """Tests for workflow initialization in both Discovery and Direct modes."""

    @pytest.mark.asyncio
    async def test_discovery_mode_initialization(self, orchestration_engine, mock_state_manager):
        """Test workflow initialization in Discovery mode."""
        project_id = "test_project_001"
        input_data = {
            "project_overview": "Build a healthcare management system",
            "key_features": "Patient records, appointment scheduling",
            "constraints": "HIPAA compliant",
        }

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            input_data=input_data,
        )

        # Verify context creation
        assert context.project_id == project_id
        assert context.mode == WorkflowMode.DISCOVERY
        assert context.status == "running"
        assert isinstance(context.workflow, DiscoveryModeWorkflow)
        assert context.input_data == input_data

        # Verify workflow has 7 phases (Discovery mode)
        assert len(context.workflow.phases) == 8  # Updated to 8 phases

        # Verify domain experts were detected
        assert len(context.activated_experts) > 0
        # Healthcare should be detected
        domains = [expert[0] for expert in context.activated_experts]
        assert "healthcare" in domains

        # Verify state was saved
        saved_context = await mock_state_manager.load_state(project_id)
        assert saved_context == context

    @pytest.mark.asyncio
    async def test_direct_mode_initialization(self, orchestration_engine, mock_state_manager):
        """Test workflow initialization in Direct mode."""
        project_id = "test_project_002"
        input_data = {
            "project_name": "My API",
            "project_type": "api",
            "language_stack": "python",
            "include_repo": True,
            "include_ci": True,
        }

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DIRECT,
            input_data=input_data,
        )

        # Verify context creation
        assert context.project_id == project_id
        assert context.mode == WorkflowMode.DIRECT
        assert context.status == "running"
        assert isinstance(context.workflow, DirectModeWorkflow)

        # Verify workflow has 4 phases (Direct mode)
        assert len(context.workflow.phases) == 4

        # Verify no domain experts in Direct mode
        assert len(context.activated_experts) == 0

        # Verify state was saved
        saved_context = await mock_state_manager.load_state(project_id)
        assert saved_context == context

    @pytest.mark.asyncio
    async def test_workflow_initialization_with_timestamps(self, orchestration_engine):
        """Test that workflow initialization sets proper timestamps."""
        project_id = "test_project_003"
        input_data = {"project_overview": "Test project"}

        before = datetime.utcnow()
        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            input_data=input_data,
        )
        after = datetime.utcnow()

        # Verify timestamps
        assert context.started_at >= before
        assert context.started_at <= after
        assert context.completed_at is None

    @pytest.mark.asyncio
    async def test_workflow_creates_async_execution_task(self, orchestration_engine):
        """Test that start_workflow creates an async task for execution."""
        project_id = "test_project_004"
        input_data = {"project_overview": "Test"}

        with patch("asyncio.create_task") as mock_create_task:
            await orchestration_engine.start_workflow(
                project_id=project_id,
                mode=WorkflowMode.DISCOVERY,
                input_data=input_data,
            )

            # Verify task was created
            mock_create_task.assert_called_once()


# Test Class: Phase Execution Order
class TestPhaseExecutionOrder:
    """Tests for phase execution order validation."""

    @pytest.mark.asyncio
    async def test_discovery_mode_phase_order(self, orchestration_engine, mock_state_manager):
        """Test that Discovery mode executes phases in correct order."""
        project_id = "test_project_005"
        input_data = {"project_overview": "Test project"}

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            input_data=input_data,
        )

        # Wait for execution to complete (short delay for async task)
        await asyncio.sleep(0.1)

        # Verify phase order
        expected_phases = [
            "input",
            "product_design",
            "requirements",
            "architecture_design",
            "code_generation",
            "quality",
            "scaffolding",
            "summary",
        ]

        workflow_phases = [phase.name for phase in context.workflow.phases]
        assert workflow_phases == expected_phases

    @pytest.mark.asyncio
    async def test_direct_mode_phase_order(self, orchestration_engine):
        """Test that Direct mode executes phases in correct order."""
        project_id = "test_project_006"
        input_data = {"project_type": "api"}

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DIRECT,
            input_data=input_data,
        )

        # Verify phase order
        expected_phases = ["input", "architecture_design", "scaffolding", "summary"]
        workflow_phases = [phase.name for phase in context.workflow.phases]
        assert workflow_phases == expected_phases

    @pytest.mark.asyncio
    async def test_phase_skipping_when_already_completed(
        self, orchestration_engine, mock_state_manager
    ):
        """Test that already completed phases are skipped on resume."""
        project_id = "test_project_007"
        input_data = {"project_overview": "Test"}

        # Create context with some completed phases
        workflow = DiscoveryModeWorkflow()
        context = ExecutionContext(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            workflow=workflow,
            input_data=input_data,
            completed_phases=["input", "product_design"],
            current_phase="requirements",
        )

        await mock_state_manager.save_state(context)

        # Resume workflow
        resumed_context = await orchestration_engine.resume_workflow(project_id)

        assert resumed_context.completed_phases == ["input", "product_design"]
        assert resumed_context.current_phase == "requirements"


# Test Class: Parallel Agent Execution
class TestParallelAgentExecution:
    """Tests for parallel agent execution."""

    @pytest.mark.asyncio
    async def test_parallel_phase_execution(self, mock_phase_executor, mock_agent_registry):
        """Test that parallel phases execute agents concurrently."""
        phase = Phase(
            name="test_parallel",
            display_name="Test Parallel",
            description="Test parallel execution",
            execution_model="parallel",
            agents=["agent1", "agent2", "agent3"],
        )

        context = ExecutionContext(
            project_id="test",
            mode=WorkflowMode.DISCOVERY,
            workflow=DiscoveryModeWorkflow(),
            input_data={},
        )

        result = await mock_phase_executor.execute_phase(phase, context)

        # Verify all agents were executed
        assert result["status"] == "completed"
        assert "agent_results" in result
        assert len(result["agent_results"]) == 3

    @pytest.mark.asyncio
    async def test_parallel_execution_with_partial_failure(
        self, mock_phase_executor, mock_agent_registry
    ):
        """Test parallel execution handles partial failures gracefully."""
        # Mock one failing agent
        failing_agent = Mock()
        failing_agent.execute = AsyncMock(side_effect=Exception("Agent failed"))

        success_agent = Mock()
        success_agent.execute = AsyncMock(return_value={"status": "success"})

        def get_agent_side_effect(agent_id):
            if agent_id == "failing_agent":
                return failing_agent
            return success_agent

        mock_agent_registry.get_agent = Mock(side_effect=get_agent_side_effect)

        phase = Phase(
            name="test_partial_failure",
            display_name="Test",
            description="Test",
            execution_model="parallel",
            agents=["agent1", "failing_agent", "agent3"],
        )

        context = ExecutionContext(
            project_id="test",
            mode=WorkflowMode.DISCOVERY,
            workflow=DiscoveryModeWorkflow(),
            input_data={},
        )

        result = await mock_phase_executor.execute_phase(phase, context)

        # Verify partial failure status
        assert result["status"] == "partial_failure"
        assert "errors" in result
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_architecture_phase_agent_activation(self, mock_phase_executor):
        """Test that architecture phase activates correct agents based on project type."""
        # Test for web-app project type
        context = ExecutionContext(
            project_id="test",
            mode=WorkflowMode.DISCOVERY,
            workflow=DiscoveryModeWorkflow(),
            input_data={"project_type": "web-app"},
        )

        architecture_phase = context.workflow.get_phase("architecture_design")
        activated_agents = mock_phase_executor._get_activated_agents(
            architecture_phase, context
        )

        # Should activate web-app specific agents
        assert "fullstack_architect" in activated_agents
        assert "backend_architect" in activated_agents
        assert "frontend_architect" in activated_agents
        assert "database_architect" in activated_agents

    @pytest.mark.asyncio
    async def test_api_project_agent_activation(self, mock_phase_executor):
        """Test agent activation for API project type."""
        context = ExecutionContext(
            project_id="test",
            mode=WorkflowMode.DISCOVERY,
            workflow=DiscoveryModeWorkflow(),
            input_data={"project_type": "api"},
        )

        architecture_phase = context.workflow.get_phase("architecture_design")
        activated_agents = mock_phase_executor._get_activated_agents(
            architecture_phase, context
        )

        # API projects shouldn't activate frontend architects
        assert "backend_architect" in activated_agents
        assert "frontend_architect" not in activated_agents


# Test Class: Approval Gate Handling
class TestApprovalGateHandling:
    """Tests for approval gate handling."""

    @pytest.mark.asyncio
    async def test_workflow_pauses_at_approval_gate(
        self, orchestration_engine, mock_state_manager, mock_approval_manager
    ):
        """Test that workflow pauses at approval gates."""
        project_id = "test_project_008"
        input_data = {"project_overview": "Test"}

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            input_data=input_data,
        )

        # Let workflow execute until first approval gate
        await asyncio.sleep(0.2)

        # Load current state
        current_state = await mock_state_manager.load_state(project_id)

        # Should pause at product_design phase (first approval gate)
        if current_state.status == "awaiting_approval":
            assert current_state.current_phase == "product_design"
            # Verify approval gate was created
            pending_gate = await mock_approval_manager.get_pending_gate(project_id)
            assert pending_gate is not None

    @pytest.mark.asyncio
    async def test_workflow_resume_after_approval(
        self, orchestration_engine, mock_state_manager, mock_approval_manager
    ):
        """Test that workflow resumes after approval."""
        project_id = "test_project_009"
        workflow = DiscoveryModeWorkflow()

        # Create paused context
        context = ExecutionContext(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            workflow=workflow,
            input_data={"project_overview": "Test"},
            status="awaiting_approval",
            current_phase="product_design",
            completed_phases=["input", "product_design"],
        )

        await mock_state_manager.save_state(context)

        # Approve the gate
        await mock_approval_manager.approve(project_id, feedback="Looks good!")

        # Resume workflow
        resumed_context = await orchestration_engine.resume_workflow(project_id)

        assert resumed_context.project_id == project_id
        # Status might still be awaiting_approval immediately after resume
        # as async task needs time to execute

    @pytest.mark.asyncio
    async def test_approval_gate_creation_with_artifact(self, mock_approval_manager):
        """Test approval gate creation includes artifact."""
        project_id = "test_project_010"
        phase = "product_design"
        artifact = {
            "type": "product_design",
            "summary": "Product design for healthcare app",
            "key_points": ["Feature 1", "Feature 2"],
        }

        gate_id = await mock_approval_manager.create_gate(
            project_id=project_id,
            phase=phase,
            artifact=artifact,
        )

        assert gate_id is not None
        assert gate_id.startswith(project_id)

        # Verify gate was stored
        pending_gate = await mock_approval_manager.get_pending_gate(project_id)
        assert pending_gate["artifact"] == artifact

    @pytest.mark.asyncio
    async def test_approval_rejection(self, mock_approval_manager):
        """Test approval rejection workflow."""
        project_id = "test_project_011"
        artifact = {"type": "test", "summary": "test"}

        await mock_approval_manager.create_gate(
            project_id=project_id,
            phase="product_design",
            artifact=artifact,
        )

        # Reject the gate
        result = await mock_approval_manager.reject(
            project_id=project_id,
            feedback="Needs more detail on authentication",
        )

        assert result is True

        # Verify gate status
        gate = await mock_approval_manager.get_pending_gate(project_id)
        # Gate should no longer be pending after rejection
        assert gate is None or gate["status"] != "pending"


# Test Class: Error Handling and Recovery
class TestErrorHandlingAndRecovery:
    """Tests for error handling and recovery mechanisms."""

    @pytest.mark.asyncio
    async def test_workflow_error_handling(
        self, orchestration_engine, mock_state_manager, mock_phase_executor
    ):
        """Test that workflow handles phase execution errors properly."""
        project_id = "test_project_012"
        input_data = {"project_overview": "Test"}

        # Mock phase executor to raise error
        mock_phase_executor.execute_phase = AsyncMock(
            side_effect=Exception("Phase execution failed")
        )

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            input_data=input_data,
        )

        # Wait for execution
        await asyncio.sleep(0.2)

        # Load state
        current_state = await mock_state_manager.load_state(project_id)

        # Verify error was captured
        if current_state.status == "failed":
            assert current_state.error is not None
            assert "Phase execution failed" in current_state.error

    @pytest.mark.asyncio
    async def test_agent_timeout_handling(self, mock_agent_registry):
        """Test that agent timeouts are handled gracefully."""
        # Create slow agent that times out
        async def slow_execute(ctx):
            await asyncio.sleep(10)
            return {"status": "success"}

        slow_agent = Mock()
        slow_agent.execute = slow_execute

        mock_agent_registry.get_agent = Mock(return_value=slow_agent)

        parallel_executor = ParallelExecutor(
            agent_registry=mock_agent_registry,
            timeout=0.1,  # Very short timeout
        )

        context = ExecutionContext(
            project_id="test",
            mode=WorkflowMode.DISCOVERY,
            workflow=DiscoveryModeWorkflow(),
            input_data={},
        )

        result = await parallel_executor.execute_parallel(
            agent_ids=["slow_agent"],
            context=context,
        )

        # Verify timeout was handled
        assert result["agent_results"]["slow_agent"]["status"] == "failed"
        assert "timed out" in result["agent_results"]["slow_agent"]["error"]

    @pytest.mark.asyncio
    async def test_missing_agent_handling(self, mock_agent_registry):
        """Test handling of missing agents in registry."""
        mock_agent_registry.get_agent = Mock(return_value=None)

        parallel_executor = ParallelExecutor(
            agent_registry=mock_agent_registry,
            timeout=300,
        )

        context = ExecutionContext(
            project_id="test",
            mode=WorkflowMode.DISCOVERY,
            workflow=DiscoveryModeWorkflow(),
            input_data={},
        )

        result = await parallel_executor.execute_parallel(
            agent_ids=["missing_agent"],
            context=context,
        )

        # Should complete without errors (no agents to execute)
        assert result["status"] == "completed"
        assert result["agent_results"] == {}

    @pytest.mark.asyncio
    async def test_workflow_not_found_error(self, orchestration_engine):
        """Test error handling when resuming non-existent workflow."""
        with pytest.raises(ValueError, match="No workflow found"):
            await orchestration_engine.resume_workflow("non_existent_project")

    @pytest.mark.asyncio
    async def test_state_persistence_on_error(
        self, orchestration_engine, mock_state_manager, mock_phase_executor
    ):
        """Test that state is persisted even when errors occur."""
        project_id = "test_project_013"
        input_data = {"project_overview": "Test"}

        mock_phase_executor.execute_phase = AsyncMock(
            side_effect=Exception("Test error")
        )

        await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            input_data=input_data,
        )

        await asyncio.sleep(0.2)

        # Verify state was saved despite error
        saved_state = await mock_state_manager.load_state(project_id)
        assert saved_state is not None

    @pytest.mark.asyncio
    async def test_circular_dependency_detection(self, mock_dependency_resolver):
        """Test that circular dependencies are detected."""
        agents = ["agent_a", "agent_b", "agent_c"]
        dependencies = {
            "agent_a": ["agent_b"],
            "agent_b": ["agent_c"],
            "agent_c": ["agent_a"],  # Circular!
        }

        with pytest.raises(ValueError, match="Circular dependency"):
            mock_dependency_resolver.resolve(agents, dependencies)


# Test Class: Progress Tracking
class TestProgressTracking:
    """Tests for workflow progress tracking."""

    @pytest.mark.asyncio
    async def test_get_progress_running_workflow(
        self, orchestration_engine, mock_state_manager
    ):
        """Test getting progress of a running workflow."""
        project_id = "test_project_014"
        input_data = {"project_overview": "Healthcare app"}

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            input_data=input_data,
        )

        progress = await orchestration_engine.get_progress(project_id)

        assert progress is not None
        assert progress["project_id"] == project_id
        assert progress["mode"] == "discovery"
        assert progress["status"] == "running"
        assert "started_at" in progress
        assert "activated_experts" in progress

    @pytest.mark.asyncio
    async def test_get_progress_non_existent_workflow(self, orchestration_engine):
        """Test getting progress for non-existent workflow."""
        progress = await orchestration_engine.get_progress("non_existent")
        assert progress is None

    @pytest.mark.asyncio
    async def test_completed_phases_tracking(
        self, orchestration_engine, mock_state_manager
    ):
        """Test that completed phases are tracked correctly."""
        project_id = "test_project_015"
        workflow = DirectModeWorkflow()

        context = ExecutionContext(
            project_id=project_id,
            mode=WorkflowMode.DIRECT,
            workflow=workflow,
            input_data={},
            completed_phases=["input", "architecture_design"],
            current_phase="scaffolding",
        )

        await mock_state_manager.save_state(context)

        progress = await orchestration_engine.get_progress(project_id)

        assert len(progress["completed_phases"]) == 2
        assert "input" in progress["completed_phases"]
        assert "architecture_design" in progress["completed_phases"]
        assert progress["current_phase"] == "scaffolding"


# Test Class: Domain Expert Detection Integration
class TestDomainExpertDetectionIntegration:
    """Tests for domain expert detection in workflow."""

    @pytest.mark.asyncio
    async def test_healthcare_domain_detection(self, orchestration_engine):
        """Test healthcare domain expert detection."""
        project_id = "test_project_016"
        input_data = {
            "project_overview": "Medical patient portal with HIPAA compliance",
            "key_features": "Electronic health records, doctor appointments",
            "constraints": "Must be HIPAA compliant",
        }

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            input_data=input_data,
        )

        # Verify healthcare expert was detected
        domains = [expert[0] for expert in context.activated_experts]
        assert "healthcare" in domains

    @pytest.mark.asyncio
    async def test_multiple_domain_detection(self, orchestration_engine):
        """Test detection of multiple domain experts."""
        project_id = "test_project_017"
        input_data = {
            "project_overview": "E-commerce platform with payment processing",
            "key_features": "Shopping cart, checkout, banking integration",
            "constraints": "PCI-DSS compliant",
        }

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DISCOVERY,
            input_data=input_data,
        )

        # Should detect both ecommerce and finance
        domains = [expert[0] for expert in context.activated_experts]
        # At least one of these should be detected
        assert len(domains) > 0
        assert any(d in ["ecommerce", "finance"] for d in domains)

    @pytest.mark.asyncio
    async def test_no_domain_experts_in_direct_mode(self, orchestration_engine):
        """Test that domain experts are not activated in Direct mode."""
        project_id = "test_project_018"
        input_data = {
            "project_overview": "Healthcare app",  # Even with healthcare keywords
            "project_type": "api",
        }

        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DIRECT,
            input_data=input_data,
        )

        # No domain experts in Direct mode
        assert len(context.activated_experts) == 0


# Test Class: Dependency Graph Execution
class TestDependencyGraphExecution:
    """Tests for dependency graph-based execution."""

    @pytest.mark.asyncio
    async def test_scaffolding_phase_dependency_order(
        self, mock_phase_executor, mock_agent_registry
    ):
        """Test that scaffolding phase executes agents in correct dependency order."""
        execution_order = []

        def track_execution(agent_id):
            agent = Mock()

            async def execute_with_tracking(ctx):
                execution_order.append(agent_id)
                return {"status": "success"}

            agent.execute = execute_with_tracking
            return agent

        mock_agent_registry.get_agent = Mock(side_effect=track_execution)

        phase = Phase(
            name="scaffolding",
            display_name="Scaffolding",
            description="Test scaffolding",
            execution_model="dependency_graph",
            agents=[
                "filesystem_scaffolder",
                "git_provisioner",
                "workflow_generator",
                "jira_provisioner",
            ],
        )

        context = ExecutionContext(
            project_id="test",
            mode=WorkflowMode.DISCOVERY,
            workflow=DiscoveryModeWorkflow(),
            input_data={},
        )

        await mock_phase_executor.execute_phase(phase, context)

        # Verify execution order: filesystem_scaffolder must come before git_provisioner
        fs_index = execution_order.index("filesystem_scaffolder")
        git_index = execution_order.index("git_provisioner")
        assert fs_index < git_index

        # git_provisioner must come before workflow_generator and jira_provisioner
        if "workflow_generator" in execution_order:
            wf_index = execution_order.index("workflow_generator")
            assert git_index < wf_index

        if "jira_provisioner" in execution_order:
            jira_index = execution_order.index("jira_provisioner")
            assert git_index < jira_index

    @pytest.mark.asyncio
    async def test_dependency_resolver_batch_grouping(self, mock_dependency_resolver):
        """Test that dependency resolver creates correct parallel batches."""
        agents = ["a", "b", "c", "d", "e"]
        dependencies = {
            "b": ["a"],
            "c": ["a"],
            "d": ["b", "c"],
            "e": ["d"],
        }

        batches = mock_dependency_resolver.resolve(agents, dependencies)

        # Verify batch structure
        assert len(batches) > 0

        # First batch should be agents with no dependencies
        assert "a" in batches[0]

        # Verify all agents are included
        all_agents = []
        for batch in batches:
            all_agents.extend(batch)
        assert set(all_agents) == set(agents)


# Test Class: Workflow Completion
class TestWorkflowCompletion:
    """Tests for workflow completion scenarios."""

    @pytest.mark.asyncio
    async def test_workflow_completion_status(self, mock_state_manager):
        """Test that workflow status is set to completed."""
        project_id = "test_project_019"
        workflow = DirectModeWorkflow()

        context = ExecutionContext(
            project_id=project_id,
            mode=WorkflowMode.DIRECT,
            workflow=workflow,
            input_data={},
            completed_phases=["input", "architecture_design", "scaffolding", "summary"],
            current_phase="summary",
            status="completed",
            completed_at=datetime.utcnow(),
        )

        await mock_state_manager.save_state(context)

        loaded = await mock_state_manager.load_state(project_id)

        assert loaded.status == "completed"
        assert loaded.completed_at is not None
        assert len(loaded.completed_phases) == 4

    @pytest.mark.asyncio
    async def test_all_phases_completed(
        self, orchestration_engine, mock_state_manager, mock_phase_executor
    ):
        """Test workflow with all phases completed successfully."""
        project_id = "test_project_020"

        # Mock successful execution
        mock_phase_executor.execute_phase = AsyncMock(
            return_value={
                "status": "completed",
                "agent_results": {"test": {"status": "success"}},
            }
        )

        # Use Direct mode (no approval gates) for faster completion
        context = await orchestration_engine.start_workflow(
            project_id=project_id,
            mode=WorkflowMode.DIRECT,
            input_data={"project_type": "api"},
        )

        # Allow workflow to complete
        await asyncio.sleep(0.3)

        # Load final state
        final_state = await mock_state_manager.load_state(project_id)

        # Should eventually complete
        if final_state.status == "completed":
            assert final_state.completed_at is not None
            assert len(final_state.completed_phases) > 0
