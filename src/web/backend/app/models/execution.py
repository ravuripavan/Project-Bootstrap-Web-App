from datetime import datetime
from sqlalchemy import Column, String, Integer, Enum, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, generate_id
from app.schemas.enums import PhaseStatus, ApprovalStatus


class ExecutionStep(Base, TimestampMixin):
    """
    Execution step - tracks individual agent executions.
    """
    __tablename__ = "execution_steps"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("step_"))
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=False)

    # Step info
    phase = Column(String(50), nullable=False)
    step_order = Column(Integer, nullable=False)
    agent_id = Column(String(50), nullable=False)
    agent_name = Column(String(100), nullable=True)

    # Status
    status = Column(
        Enum(PhaseStatus),
        default=PhaseStatus.PENDING,
        nullable=False,
    )

    # Data
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Dependencies (stored as JSON array for SQLite compatibility)
    depends_on = Column(JSON, default=list)

    # Timing
    duration_ms = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="execution_steps")

    def __repr__(self) -> str:
        return f"<ExecutionStep(id={self.id}, agent={self.agent_id}, status={self.status})>"

    def mark_started(self):
        self.status = PhaseStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()

    def mark_completed(self, output: dict, duration_ms: int):
        self.status = PhaseStatus.COMPLETED
        self.output_data = output
        self.duration_ms = duration_ms
        self.completed_at = datetime.utcnow()

    def mark_failed(self, error: str):
        self.status = PhaseStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.utcnow()


class ApprovalGate(Base, TimestampMixin):
    """
    Approval gate - user review points in workflow.
    """
    __tablename__ = "approval_gates"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("gate_"))
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=False)

    # Gate info
    phase = Column(String(50), nullable=False)
    artifact_type = Column(String(50), nullable=False)  # product_design, architecture_design

    # Status
    status = Column(
        Enum(ApprovalStatus),
        default=ApprovalStatus.PENDING,
        nullable=False,
    )

    # Artifact data
    artifact_snapshot = Column(JSON, nullable=False)

    # User response
    feedback = Column(Text, nullable=True)
    modifications = Column(JSON, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="approval_gates")

    def __repr__(self) -> str:
        return f"<ApprovalGate(id={self.id}, phase={self.phase}, status={self.status})>"

    def approve(self, feedback: str = None, user: str = None):
        self.status = ApprovalStatus.APPROVED
        self.feedback = feedback
        self.resolved_by = user
        self.resolved_at = datetime.utcnow()

    def reject(self, feedback: str, user: str = None):
        self.status = ApprovalStatus.REJECTED
        self.feedback = feedback
        self.resolved_by = user
        self.resolved_at = datetime.utcnow()
