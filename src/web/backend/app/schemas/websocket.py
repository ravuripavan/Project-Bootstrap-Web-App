from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

from app.schemas.enums import PhaseStatus, AgentStatus

class WSMessage(BaseModel):
    """Base WebSocket message"""
    type: str
    timestamp: datetime
    project_id: str

class WSConnected(WSMessage):
    """Connection established"""
    type: str = "connected"
    message: str = "Connected to project updates"

class WSPhaseStarted(WSMessage):
    """Phase started"""
    type: str = "phase_started"
    phase: str
    phase_display_name: str

class WSPhaseCompleted(WSMessage):
    """Phase completed"""
    type: str = "phase_completed"
    phase: str
    status: PhaseStatus
    duration_ms: int

class WSAgentStarted(WSMessage):
    """Agent execution started"""
    type: str = "agent_started"
    agent_id: str
    agent_name: str
    phase: str

class WSAgentProgress(WSMessage):
    """Agent execution progress"""
    type: str = "agent_progress"
    agent_id: str
    agent_name: str
    progress_percent: int
    message: Optional[str] = None

class WSAgentCompleted(WSMessage):
    """Agent execution completed"""
    type: str = "agent_completed"
    agent_id: str
    agent_name: str
    status: AgentStatus
    duration_ms: int
    output_preview: Optional[str] = None

class WSApprovalRequired(WSMessage):
    """User approval required"""
    type: str = "approval_required"
    phase: str
    artifact_type: str
    artifact_preview: dict[str, Any]

class WSWorkflowCompleted(WSMessage):
    """Workflow completed"""
    type: str = "workflow_completed"
    status: str
    duration_ms: int
    summary: dict[str, Any]

class WSError(WSMessage):
    """Error occurred"""
    type: str = "error"
    error_code: str
    error_message: str
    phase: Optional[str] = None
    agent_id: Optional[str] = None

class WSLog(WSMessage):
    """Log message"""
    type: str = "log"
    level: str  # info, warning, error
    agent_id: Optional[str] = None
    message: str
