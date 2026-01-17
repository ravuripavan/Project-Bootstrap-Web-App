"""
Parallel executor - runs agents concurrently.
"""
from typing import Dict, Any, List
import asyncio
import structlog

logger = structlog.get_logger()


class ParallelExecutor:
    """Executes multiple agents concurrently using asyncio."""

    def __init__(self, agent_registry, timeout: int = 300):
        self.agent_registry = agent_registry
        self.timeout = timeout

    async def execute_parallel(
        self,
        agent_ids: List[str],
        context,
    ) -> Dict[str, Any]:
        """
        Run multiple agents in parallel.

        Args:
            agent_ids: List of agent IDs to execute
            context: Execution context

        Returns:
            Combined results from all agents
        """
        logger.info(
            "Starting parallel execution",
            agents=agent_ids,
            project_id=context.project_id,
        )

        tasks = []
        for agent_id in agent_ids:
            agent = self.agent_registry.get_agent(agent_id)
            if agent:
                tasks.append(self._execute_with_timeout(agent, context, agent_id))

        if not tasks:
            return {"status": "completed", "agent_results": {}}

        results = await asyncio.gather(*tasks, return_exceptions=True)

        agent_results = {}
        errors = []

        for i, result in enumerate(results):
            agent_id = agent_ids[i]
            if isinstance(result, Exception):
                errors.append(f"{agent_id}: {str(result)}")
                agent_results[agent_id] = {
                    "status": "failed",
                    "error": str(result),
                }
            else:
                agent_results[agent_id] = result

        status = "completed" if not errors else "partial_failure"

        return {
            "status": status,
            "agent_results": agent_results,
            "errors": errors if errors else None,
        }

    async def _execute_with_timeout(
        self,
        agent,
        context,
        agent_id: str,
    ) -> Dict[str, Any]:
        """Execute agent with timeout."""
        try:
            return await asyncio.wait_for(
                agent.execute(context),
                timeout=self.timeout,
            )
        except asyncio.TimeoutError:
            logger.error(
                "Agent timed out",
                agent_id=agent_id,
                timeout=self.timeout,
            )
            return {
                "status": "failed",
                "error": f"Agent {agent_id} timed out after {self.timeout}s",
            }
