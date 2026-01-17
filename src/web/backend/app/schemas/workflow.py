from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

from app.schemas.enums import PhaseStatus, WorkflowMode

class PhaseDefinition(BaseModel):
    """Workflow phase definition"""
    name: str
    display_name: str
    description: str
    requires_approval: bool = False
    execution_model: str = "sequential"  # sequential, parallel, dependency_graph
    agents: list[str] = []

class PhaseProgress(BaseModel):
    """Progress of a workflow phase"""
    name: str
    display_name: str
    status: PhaseStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agents_total: int = 0
    agents_completed: int = 0
    agents_running: int = 0
    current_agent: Optional[str] = None

class WorkflowProgress(BaseModel):
    """Overall workflow progress"""
    mode: WorkflowMode
    current_phase: str
    phases: list[PhaseProgress]
    started_at: datetime
    estimated_completion: Optional[datetime] = None

class ExecutionStep(BaseModel):
    """Individual execution step"""
    id: str
    phase: str
    step_order: int
    agent_id: str
    agent_name: str
    status: PhaseStatus
    depends_on: list[str] = []
    duration_ms: Optional[int] = None
    output_preview: Optional[str] = None

class ExecutionPlan(BaseModel):
    """Complete execution plan"""
    project_id: str
    mode: WorkflowMode
    phases: list[PhaseDefinition]
    steps: list[ExecutionStep]
    estimated_duration_minutes: Optional[int] = None
    activated_domain_experts: list[str] = []

class ApprovalGate(BaseModel):
    """Approval gate for user review"""
    id: str
    project_id: str
    phase: str
    artifact_type: str
    artifact_preview: dict[str, Any]
    status: str = "pending"
    created_at: datetime
    resolved_at: Optional[datetime] = None
    feedback: Optional[str] = None
