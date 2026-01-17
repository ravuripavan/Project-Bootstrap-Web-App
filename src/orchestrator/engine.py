"""
Core Orchestration Engine - Coordinates multi-agent workflows.
Supports Discovery Mode (7 phases with approvals) and Direct Mode (5 phases).
"""
from typing import Dict, Any, Optional
from datetime import datetime
import structlog
import asyncio

from src.orchestrator.workflow import (
    WorkflowDefinition,
    DiscoveryModeWorkflow,
    DirectModeWorkflow,
    WorkflowMode,
    Phase,
)
from src.orchestrator.phase_executor import PhaseExecutor
from src.orchestrator.state_manager import StateManager, ExecutionContext
from src.orchestrator.approval_manager import ApprovalManager
from src.orchestrator.domain_expert_detector import DomainExpertDetector

logger = structlog.get_logger()


class OrchestrationEngine:
    """
    Master coordinator that manages the entire workflow.

    Responsibilities:
    - Determines workflow mode (Discovery vs Direct)
    - Selects appropriate agents based on project type
    - Manages agent execution order and dependencies
    - Handles user approval gates
    - Coordinates parallel agent execution
    - Aggregates and consolidates agent outputs
    """

    def __init__(
        self,
        phase_executor: PhaseExecutor,
        state_manager: StateManager,
        approval_manager: ApprovalManager,
        domain_detector: DomainExpertDetector,
    ):
        self.phase_executor = phase_executor
        self.state_manager = state_manager
        self.approval_manager = approval_manager
        self.domain_detector = domain_detector

    async def start_workflow(
        self,
        project_id: str,
        mode: WorkflowMode,
        input_data: Dict[str, Any],
    ) -> ExecutionContext:
        """
        Initialize and start a new workflow.

        Args:
            project_id: Unique project identifier
            mode: WorkflowMode.DISCOVERY or WorkflowMode.DIRECT
            input_data: Project overview (discovery) or spec (direct)

        Returns:
            ExecutionContext with initial state
        """
        logger.info(
            "Starting workflow",
            project_id=project_id,
            mode=mode.value,
        )

        # Select workflow based on mode
        workflow = self._get_workflow(mode)

        # Detect domain experts if in discovery mode
        activated_experts = []
        if mode == WorkflowMode.DISCOVERY:
            activated_experts = self.domain_detector.detect_domains(
                project_overview=input_data.get("project_overview", ""),
                key_features=input_data.get("key_features", ""),
                constraints=input_data.get("constraints", ""),
            )
            logger.info(
                "Domain experts detected",
                project_id=project_id,
                experts=[e[0] for e in activated_experts],
            )

        # Create execution context
        context = ExecutionContext(
            project_id=project_id,
            mode=mode,
            workflow=workflow,
            input_data=input_data,
            activated_experts=activated_experts,
            started_at=datetime.utcnow(),
        )

        # Persist initial state
        await self.state_manager.save_state(context)

        # Begin execution (async - will pause at approval gates)
        asyncio.create_task(self._execute_workflow(context))

        return context

    async def resume_workflow(self, project_id: str) -> ExecutionContext:
        """
        Resume a paused workflow after approval.

        Args:
            project_id: Project to resume

        Returns:
            Updated ExecutionContext
        """
        context = await self.state_manager.load_state(project_id)
        if not context:
            raise ValueError(f"No workflow found for project {project_id}")

        logger.info(
            "Resuming workflow",
            project_id=project_id,
            current_phase=context.current_phase,
        )

        # Continue execution
        asyncio.create_task(self._execute_workflow(context))

        return context

    async def _execute_workflow(self, context: ExecutionContext) -> None:
        """Execute workflow phases sequentially."""
        try:
            for phase in context.workflow.phases:
                # Skip already completed phases
                if phase.name in context.completed_phases:
                    continue

                context.current_phase = phase.name
                await self.state_manager.save_state(context)

                logger.info(
                    "Executing phase",
                    project_id=context.project_id,
                    phase=phase.name,
                )

                # Execute the phase
                result = await self.phase_executor.execute_phase(
                    phase=phase,
                    context=context,
                )

                # Update context with results
                context.phase_results[phase.name] = result
                context.completed_phases.append(phase.name)
                await self.state_manager.save_state(context)

                # Check for approval gate after phase
                if phase.requires_approval:
                    logger.info(
                        "Approval required",
                        project_id=context.project_id,
                        phase=phase.name,
                    )

                    # Create approval gate
                    await self.approval_manager.create_gate(
                        project_id=context.project_id,
                        phase=phase.name,
                        artifact=result,
                    )

                    # Pause workflow
                    context.status = "awaiting_approval"
                    await self.state_manager.save_state(context)
                    return  # Exit and wait for approval

            # All phases complete
            context.status = "completed"
            context.completed_at = datetime.utcnow()
            await self.state_manager.save_state(context)

            logger.info(
                "Workflow completed",
                project_id=context.project_id,
                duration_seconds=(context.completed_at - context.started_at).total_seconds(),
            )

        except Exception as e:
            logger.error(
                "Workflow failed",
                project_id=context.project_id,
                error=str(e),
            )
            context.status = "failed"
            context.error = str(e)
            await self.state_manager.save_state(context)
            raise

    def _get_workflow(self, mode: WorkflowMode) -> WorkflowDefinition:
        """Get workflow definition for mode."""
        if mode == WorkflowMode.DISCOVERY:
            return DiscoveryModeWorkflow()
        return DirectModeWorkflow()

    async def get_progress(self, project_id: str) -> Dict[str, Any]:
        """Get current workflow progress."""
        context = await self.state_manager.load_state(project_id)
        if not context:
            return None

        return {
            "project_id": context.project_id,
            "mode": context.mode.value,
            "status": context.status,
            "current_phase": context.current_phase,
            "completed_phases": context.completed_phases,
            "started_at": context.started_at.isoformat(),
            "activated_experts": [e[0] for e in context.activated_experts],
        }
