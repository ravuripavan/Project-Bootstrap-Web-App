from datetime import datetime
from sqlalchemy import Column, String, Enum, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from typing import Optional

from app.models.base import Base, TimestampMixin, generate_id
from app.schemas.enums import ProjectStatus, WorkflowMode


class Project(Base, TimestampMixin):
    """
    Project model - stores project state and artifacts.
    """
    __tablename__ = "projects"

    # Primary key with prefix
    id = Column(String(32), primary_key=True, default=lambda: generate_id("proj_"))

    # Basic info
    name = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)

    # Workflow state
    status = Column(
        Enum(ProjectStatus),
        default=ProjectStatus.PENDING,
        nullable=False,
    )
    mode = Column(Enum(WorkflowMode), nullable=False)
    current_phase = Column(String(50), nullable=True)

    # Input data (JSON)
    project_overview = Column(JSON, nullable=True)  # Discovery mode input
    project_spec = Column(JSON, nullable=True)      # Direct mode input

    # Generated artifacts (JSON)
    product_design = Column(JSON, nullable=True)
    architecture_design = Column(JSON, nullable=True)
    requirements = Column(JSON, nullable=True)
    generated_code = Column(JSON, nullable=True)

    # Activated domain experts
    activated_experts = Column(JSON, default=list)

    # Timing
    completed_at = Column(DateTime, nullable=True)

    # Error info
    error_message = Column(Text, nullable=True)

    # Relationships
    execution_steps = relationship(
        "ExecutionStep",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    approval_gates = relationship(
        "ApprovalGate",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    agent_results = relationship(
        "AgentResult",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def is_complete(self) -> bool:
        return self.status == ProjectStatus.COMPLETED

    @property
    def is_awaiting_approval(self) -> bool:
        return self.status == ProjectStatus.AWAITING_APPROVAL
