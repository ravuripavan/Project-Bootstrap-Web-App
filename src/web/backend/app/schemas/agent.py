from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime

from app.schemas.enums import AgentCategory, AgentStatus

class AgentDefinition(BaseModel):
    """Agent definition loaded from .claude/agents/*.md"""
    id: str
    name: str
    description: str
    category: AgentCategory
    model: str = "sonnet"
    tools: list[str] = []
    activation_rules: Optional[dict[str, Any]] = None
    instructions: Optional[str] = None

class AgentInput(BaseModel):
    """Input to an agent"""
    project_id: str
    context: dict[str, Any]
    dependencies: dict[str, Any] = {}

class AgentOutput(BaseModel):
    """Output from an agent"""
    status: AgentStatus
    output: dict[str, Any]
    artifacts: list[dict[str, Any]] = []
    messages: list[str] = []
    errors: list[str] = []
    duration_ms: int
    token_usage: Optional[dict[str, int]] = None

class AgentExecutionRecord(BaseModel):
    """Record of agent execution"""
    id: str
    agent_id: str
    agent_name: str
    status: AgentStatus
    phase: str
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class DomainExpertMatch(BaseModel):
    """Domain expert activation match"""
    domain: str
    agent_id: str
    confidence: float
    matched_keywords: list[str]
