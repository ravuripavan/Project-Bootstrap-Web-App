"""
State manager - persists workflow state.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json


@dataclass
class ExecutionContext:
    """Execution context for a workflow."""
    project_id: str
    mode: Any  # WorkflowMode
    workflow: Any  # WorkflowDefinition
    input_data: Dict[str, Any]
    activated_experts: List[Tuple[str, float]] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    status: str = "running"
    current_phase: str = ""
    completed_phases: List[str] = field(default_factory=list)
    phase_results: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class StateManager:
    """
    Manages workflow state persistence.
    Uses Redis for fast access, PostgreSQL for durability.
    """

    def __init__(self, redis_client=None, db_session=None):
        self.redis = redis_client
        self.db = db_session
        self._memory_store: Dict[str, ExecutionContext] = {}

    async def save_state(self, context: ExecutionContext) -> None:
        """Save execution context."""
        # For now, use in-memory storage
        # TODO: Implement Redis + PostgreSQL persistence
        self._memory_store[context.project_id] = context

    async def load_state(self, project_id: str) -> Optional[ExecutionContext]:
        """Load execution context."""
        return self._memory_store.get(project_id)

    async def delete_state(self, project_id: str) -> None:
        """Delete execution context."""
        if project_id in self._memory_store:
            del self._memory_store[project_id]
