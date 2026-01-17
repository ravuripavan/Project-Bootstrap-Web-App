from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import datetime
import re

from app.schemas.enums import (
    WorkflowMode, ProjectStatus, ProjectType, LanguageStack,
    CIProvider, VCSProvider
)

# --- Discovery Mode Input ---

class ProjectOverviewCreate(BaseModel):
    """Discovery Mode input - user provides project overview"""
    project_name: str = Field(..., min_length=2, max_length=64)
    project_overview: str = Field(..., min_length=100, max_length=5000)
    target_users: Optional[str] = Field(None, max_length=1000)
    key_features: Optional[str] = Field(None, max_length=2000)
    constraints: Optional[str] = Field(None, max_length=1000)
    similar_products: Optional[str] = Field(None, max_length=500)
    project_type_hint: Optional[ProjectType] = None

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9-_]*$", v):
            raise ValueError("Project name must start with a letter and contain only letters, numbers, hyphens, and underscores")
        return v.lower()

# --- Direct Mode Input ---

class VCSConfig(BaseModel):
    """Version control configuration"""
    visibility: str = Field(default="private", pattern="^(public|private)$")
    create_remote: bool = True
    default_branch: str = "main"

class JiraConfig(BaseModel):
    """Jira project configuration"""
    key_prefix: str = Field(..., min_length=2, max_length=10, pattern="^[A-Z]+$")
    project_type: str = Field(default="scrum", pattern="^(scrum|kanban|basic)$")

class ProjectSpecCreate(BaseModel):
    """Direct Mode input - user specifies exact stack"""
    project_name: str = Field(..., min_length=2, max_length=64)
    project_path: str = Field(..., min_length=1)
    project_type: ProjectType
    language_stack: LanguageStack
    framework: Optional[str] = None
    include_repo: bool = True
    include_ci: bool = True
    include_jira: bool = False
    ci_provider: Optional[CIProvider] = CIProvider.GITHUB_ACTIONS
    vcs_provider: Optional[VCSProvider] = VCSProvider.GITHUB
    vcs_config: Optional[VCSConfig] = None
    jira_config: Optional[JiraConfig] = None

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        if not re.match(r"^[a-z][a-z0-9-]*$", v):
            raise ValueError("Project name must be lowercase, start with a letter, and contain only letters, numbers, and hyphens")
        return v

# --- Project Response ---

class ProductDesign(BaseModel):
    """Product design output from PO Agent"""
    vision: str
    problem_statement: Optional[str] = None
    target_audience: Optional[str] = None
    value_proposition: Optional[list[str]] = None
    goals: list[dict[str, Any]]  # Rich goals with type and priority
    personas: list[dict[str, Any]]
    user_journey: Optional[dict[str, Any]] = None
    epics: list[dict[str, Any]]
    user_stories: Optional[list[dict[str, Any]]] = None
    mvp_scope: dict[str, Any]
    risks: list[dict[str, Any]]
    success_metrics: list[dict[str, Any]]
    competitive_analysis: Optional[dict[str, Any]] = None

class ArchitectureDesign(BaseModel):
    """Architecture design output from Architect Agents"""
    tech_stack: dict[str, Any]
    system_components: list[dict[str, Any]]
    data_model: dict[str, Any]
    api_design: dict[str, Any]
    security: dict[str, Any]
    infrastructure: dict[str, Any]
    domain_considerations: Optional[list[dict[str, Any]]] = None

class ProjectResponse(BaseModel):
    """Project response with current state"""
    id: str
    status: ProjectStatus
    mode: WorkflowMode
    current_phase: str
    project_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ProjectDetailResponse(ProjectResponse):
    """Detailed project response including artifacts"""
    project_overview: Optional[dict[str, Any]] = None
    project_spec: Optional[dict[str, Any]] = None
    product_design: Optional[ProductDesign] = None
    architecture_design: Optional[ArchitectureDesign] = None
    execution_progress: Optional[dict[str, Any]] = None

class ProjectListResponse(BaseModel):
    """Paginated project list"""
    projects: list[ProjectResponse]
    total: int
    limit: int
    offset: int

# --- Approval ---

class ApprovalRequest(BaseModel):
    """Approve current phase"""
    feedback: Optional[str] = Field(None, max_length=2000)
    modifications: Optional[dict[str, Any]] = None

class RejectionRequest(BaseModel):
    """Reject current phase with feedback"""
    feedback: str = Field(..., min_length=10, max_length=2000)
    specific_issues: Optional[list[str]] = None

# --- Validation ---

class ValidationResult(BaseModel):
    """Spec validation result"""
    valid: bool
    errors: list[str] = []
    warnings: list[str] = []
