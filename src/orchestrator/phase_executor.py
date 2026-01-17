"""
Phase executor - handles execution of workflow phases.
"""
from typing import Dict, Any, List
import structlog
import asyncio

from src.orchestrator.workflow import Phase
from src.orchestrator.parallel_executor import ParallelExecutor
from src.orchestrator.dependency_resolver import DependencyResolver

logger = structlog.get_logger()


class PhaseExecutor:
    """
    Executes individual workflow phases.
    Supports sequential, parallel, and dependency graph execution models.
    """

    def __init__(
        self,
        agent_registry,  # Will be injected
        parallel_executor: ParallelExecutor,
        dependency_resolver: DependencyResolver,
    ):
        self.agent_registry = agent_registry
        self.parallel_executor = parallel_executor
        self.dependency_resolver = dependency_resolver

    async def execute_phase(
        self,
        phase: Phase,
        context,  # ExecutionContext
    ) -> Dict[str, Any]:
        """
        Execute a workflow phase.

        Args:
            phase: Phase definition
            context: Current execution context

        Returns:
            Phase execution results
        """
        logger.info(
            "Executing phase",
            phase=phase.name,
            execution_model=phase.execution_model,
            agents=phase.agents,
        )

        # Get activated agents for this phase
        agents = self._get_activated_agents(phase, context)

        if not agents:
            logger.info("No agents activated for phase", phase=phase.name)
            return {"status": "skipped", "reason": "no_activated_agents"}

        # Execute based on execution model
        if phase.execution_model == "sequential":
            result = await self._execute_sequential(agents, context)
        elif phase.execution_model == "parallel":
            result = await self._execute_parallel(agents, context)
        elif phase.execution_model == "dependency_graph":
            result = await self._execute_dependency_graph(agents, context, phase)
        else:
            raise ValueError(f"Unknown execution model: {phase.execution_model}")

        return result

    def _get_activated_agents(self, phase: Phase, context) -> List[str]:
        """Get agents that should be activated for this phase."""
        if not phase.activation_rules:
            return phase.agents

        # Use activation matrix based on project type
        if phase.activation_rules.get("use_activation_matrix"):
            project_type = context.input_data.get("project_type") or \
                          context.input_data.get("project_type_hint") or \
                          "web-app"
            return self._filter_by_activation_matrix(phase.agents, project_type, phase.name)

        return phase.agents

    def _filter_by_activation_matrix(
        self,
        agents: List[str],
        project_type: str,
        phase_name: str,
    ) -> List[str]:
        """Filter agents based on activation matrix."""
        # Activation matrix from agent-orchestration-v2.yml
        ACTIVATION_MATRIX = {
            "web-app": {
                "architecture_design": ["fullstack_architect", "backend_architect", "frontend_architect", "database_architect", "infrastructure_architect", "security_architect"],
                "code_generation": ["fullstack_developer", "backend_developer", "frontend_developer"],
            },
            "api": {
                "architecture_design": ["backend_architect", "database_architect", "infrastructure_architect", "security_architect"],
                "code_generation": ["backend_developer"],
            },
            "ml-project": {
                "architecture_design": ["fullstack_architect", "backend_architect", "database_architect", "infrastructure_architect", "ml_architect"],
                "code_generation": ["backend_developer", "aiml_developer"],
            },
            "ai-app": {
                "architecture_design": ["fullstack_architect", "backend_architect", "frontend_architect", "database_architect", "infrastructure_architect", "security_architect", "ai_architect"],
                "code_generation": ["fullstack_developer", "aiml_developer"],
            },
            "full-platform": {
                "architecture_design": ["fullstack_architect", "backend_architect", "frontend_architect", "database_architect", "infrastructure_architect", "security_architect", "ml_architect", "ai_architect"],
                "code_generation": ["fullstack_developer", "backend_developer", "frontend_developer", "aiml_developer"],
            },
        }

        matrix = ACTIVATION_MATRIX.get(project_type, ACTIVATION_MATRIX["web-app"])
        activated = matrix.get(phase_name, [])

        return [a for a in agents if a in activated]

    async def _execute_sequential(
        self,
        agents: List[str],
        context,
    ) -> Dict[str, Any]:
        """Execute agents sequentially."""
        results = {}
        for agent_id in agents:
            agent = self.agent_registry.get_agent(agent_id)
            if agent:
                result = await agent.execute(context)
                results[agent_id] = result
        return {"status": "completed", "agent_results": results}

    async def _execute_parallel(
        self,
        agents: List[str],
        context,
    ) -> Dict[str, Any]:
        """Execute agents in parallel."""
        return await self.parallel_executor.execute_parallel(
            agent_ids=agents,
            context=context,
        )

    async def _execute_dependency_graph(
        self,
        agents: List[str],
        context,
        phase: Phase,
    ) -> Dict[str, Any]:
        """Execute agents based on dependency graph."""
        # Define dependencies for scaffolding phase
        DEPENDENCIES = {
            "git_provisioner": ["filesystem_scaffolder"],
            "workflow_generator": ["git_provisioner"],
            "jira_provisioner": ["git_provisioner"],
        }

        # Resolve execution order
        execution_order = self.dependency_resolver.resolve(agents, DEPENDENCIES)

        results = {}
        for batch in execution_order:
            # Execute batch in parallel
            batch_agents = [a for a in batch if a in agents]
            if batch_agents:
                batch_result = await self.parallel_executor.execute_parallel(
                    agent_ids=batch_agents,
                    context=context,
                )
                results.update(batch_result.get("agent_results", {}))

        return {"status": "completed", "agent_results": results}
