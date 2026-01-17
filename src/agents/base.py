"""
Base agent class - abstract interface for all agents.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime
import time


@dataclass
class AgentInput:
    """Input to an agent execution."""
    project_id: str
    context: Dict[str, Any]
    dependencies: Dict[str, Any] = field(default_factory=dict)

    def get_dependency(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get output from a dependency agent."""
        return self.dependencies.get(agent_id)


@dataclass
class AgentOutput:
    """Output from an agent execution."""
    status: str  # success, failure, needs_input
    output: Dict[str, Any]
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    messages: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_ms: int = 0
    token_usage: Optional[Dict[str, int]] = None

    @classmethod
    def success(
        cls,
        output: Dict[str, Any],
        artifacts: List[Dict[str, Any]] = None,
        messages: List[str] = None,
        duration_ms: int = 0,
    ) -> "AgentOutput":
        return cls(
            status="success",
            output=output,
            artifacts=artifacts or [],
            messages=messages or [],
            duration_ms=duration_ms,
        )

    @classmethod
    def failure(
        cls,
        errors: List[str],
        duration_ms: int = 0,
    ) -> "AgentOutput":
        return cls(
            status="failure",
            output={},
            errors=errors,
            duration_ms=duration_ms,
        )


class BaseAgent(ABC):
    """
    Abstract base class for all agents.

    Each agent must implement:
    - execute(): Main execution logic
    - get_activation_rules(): When should this agent be activated
    """

    agent_id: str
    agent_name: str
    category: str
    model: str = "sonnet"

    def __init__(self):
        self._start_time: Optional[float] = None

    @abstractmethod
    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """
        Execute the agent's main logic.

        Args:
            input_data: AgentInput with context and dependencies

        Returns:
            AgentOutput with results
        """
        pass

    @abstractmethod
    def get_activation_rules(self) -> Dict[str, Any]:
        """
        Return rules for when this agent should be activated.

        Returns:
            Dict with activation rules (project_types, conditions, etc.)
        """
        pass

    def validate_input(self, input_data: AgentInput) -> bool:
        """Validate input data before execution."""
        return input_data.project_id is not None

    def validate_output(self, output: AgentOutput) -> bool:
        """Validate output data after execution."""
        return output.status in ["success", "failure", "needs_input"]

    def _start_timer(self):
        """Start execution timer."""
        self._start_time = time.time()

    def _get_duration_ms(self) -> int:
        """Get execution duration in milliseconds."""
        if self._start_time is None:
            return 0
        return int((time.time() - self._start_time) * 1000)

    async def run(self, input_data: AgentInput) -> AgentOutput:
        """
        Run the agent with timing and validation.
        Wraps execute() with common functionality.
        """
        self._start_timer()

        # Validate input
        if not self.validate_input(input_data):
            return AgentOutput.failure(
                errors=["Invalid input data"],
                duration_ms=self._get_duration_ms(),
            )

        try:
            # Execute agent logic
            output = await self.execute(input_data)
            output.duration_ms = self._get_duration_ms()

            # Validate output
            if not self.validate_output(output):
                output.errors.append("Output validation failed")

            return output

        except Exception as e:
            return AgentOutput.failure(
                errors=[str(e)],
                duration_ms=self._get_duration_ms(),
            )
