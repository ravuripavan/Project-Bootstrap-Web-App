"""
Agent executor - executes agents with Claude API integration.
"""
from typing import Dict, Any, Optional
import structlog
import asyncio

from src.agents.base import BaseAgent, AgentInput, AgentOutput
from src.agents.registry import AgentRegistry

logger = structlog.get_logger()


class AgentExecutor:
    """
    Executes agents with timeout, retry logic, and Claude API integration.
    """

    def __init__(
        self,
        registry: AgentRegistry,
        claude_client=None,  # Anthropic client
        default_timeout: int = 300,
        max_retries: int = 3,
    ):
        self.registry = registry
        self.claude_client = claude_client
        self.default_timeout = default_timeout
        self.max_retries = max_retries

    async def execute(
        self,
        agent_id: str,
        input_data: AgentInput,
        timeout: Optional[int] = None,
    ) -> AgentOutput:
        """
        Execute an agent with error handling and retries.

        Args:
            agent_id: Agent to execute
            input_data: Input data for agent
            timeout: Optional timeout override

        Returns:
            AgentOutput with results
        """
        agent = self.registry.get_agent(agent_id)

        if not agent:
            # Try to execute via Claude API using definition
            definition = self.registry.get_definition(agent_id)
            if definition and self.claude_client:
                return await self._execute_via_claude(definition, input_data)

            return AgentOutput.failure(
                errors=[f"Agent not found: {agent_id}"]
            )

        timeout = timeout or self.default_timeout

        # Execute with retries
        for attempt in range(self.max_retries):
            try:
                output = await asyncio.wait_for(
                    agent.run(input_data),
                    timeout=timeout,
                )

                if output.status == "success":
                    return output

                # Retry on failure (except last attempt)
                if attempt < self.max_retries - 1:
                    logger.warning(
                        "Agent failed, retrying",
                        agent_id=agent_id,
                        attempt=attempt + 1,
                        errors=output.errors,
                    )
                    await asyncio.sleep(1 * (attempt + 1))  # Backoff
                    continue

                return output

            except asyncio.TimeoutError:
                logger.error(
                    "Agent timed out",
                    agent_id=agent_id,
                    timeout=timeout,
                )
                if attempt < self.max_retries - 1:
                    continue

                return AgentOutput.failure(
                    errors=[f"Agent timed out after {timeout}s"]
                )

            except Exception as e:
                logger.error(
                    "Agent execution error",
                    agent_id=agent_id,
                    error=str(e),
                )
                if attempt < self.max_retries - 1:
                    continue

                return AgentOutput.failure(errors=[str(e)])

        return AgentOutput.failure(errors=["Max retries exceeded"])

    async def _execute_via_claude(
        self,
        definition,  # AgentDefinition
        input_data: AgentInput,
    ) -> AgentOutput:
        """
        Execute agent via Claude API using definition instructions.

        This allows agents defined only in .claude/agents/*.md to run
        without a Python implementation.
        """
        if not self.claude_client:
            return AgentOutput.failure(
                errors=["Claude client not configured"]
            )

        try:
            # Build prompt from definition
            system_prompt = definition.instructions

            # Build user message from input
            user_message = self._build_user_message(input_data)

            # Call Claude API
            response = await self.claude_client.messages.create(
                model=self._get_model_id(definition.model),
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )

            # Parse response
            output = self._parse_claude_response(response)

            return AgentOutput.success(
                output=output,
                token_usage={
                    "input": response.usage.input_tokens,
                    "output": response.usage.output_tokens,
                },
            )

        except Exception as e:
            logger.error(
                "Claude API error",
                agent=definition.name,
                error=str(e),
            )
            return AgentOutput.failure(errors=[str(e)])

    def _get_model_id(self, model_name: str) -> str:
        """Map model name to Claude model ID."""
        MODEL_MAP = {
            "opus": "claude-opus-4-5-20251101",
            "sonnet": "claude-sonnet-4-20250514",
            "haiku": "claude-haiku-3-5-20241022",
        }
        return MODEL_MAP.get(model_name, MODEL_MAP["sonnet"])

    def _build_user_message(self, input_data: AgentInput) -> str:
        """Build user message from input data."""
        parts = [f"Project ID: {input_data.project_id}"]

        if input_data.context:
            parts.append(f"\nContext:\n{self._format_dict(input_data.context)}")

        if input_data.dependencies:
            parts.append(f"\nDependencies:\n{self._format_dict(input_data.dependencies)}")

        return "\n".join(parts)

    def _format_dict(self, d: Dict[str, Any], indent: int = 0) -> str:
        """Format dictionary for display."""
        import json
        return json.dumps(d, indent=2)

    def _parse_claude_response(self, response) -> Dict[str, Any]:
        """Parse Claude API response into output dict."""
        content = response.content[0].text

        # Try to parse as JSON if it looks like JSON
        if content.strip().startswith("{"):
            try:
                import json
                return json.loads(content)
            except json.JSONDecodeError:
                pass

        # Return as text output
        return {"response": content}
