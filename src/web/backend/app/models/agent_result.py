from datetime import datetime
from sqlalchemy import Column, String, Integer, Enum, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, generate_id
from app.schemas.enums import AgentStatus


class AgentResult(Base, TimestampMixin):
    """
    Agent result - stores detailed agent execution results.
    """
    __tablename__ = "agent_results"

    id = Column(String(64), primary_key=True, default=lambda: generate_id("result_"))
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=False)
    execution_step_id = Column(String(64), ForeignKey("execution_steps.id"), nullable=True)

    # Agent info
    agent_id = Column(String(50), nullable=False)
    agent_name = Column(String(100), nullable=True)
    phase = Column(String(50), nullable=False)

    # Status
    status = Column(
        Enum(AgentStatus),
        default=AgentStatus.PENDING,
        nullable=False,
    )

    # Output
    output = Column(JSON, nullable=True)
    artifacts = Column(JSON, default=list)  # List of generated artifacts

    # Messages and errors (stored as JSON arrays for SQLite compatibility)
    messages = Column(JSON, default=list)
    errors = Column(JSON, default=list)
    warnings = Column(JSON, default=list)

    # Performance
    duration_ms = Column(Integer, nullable=True)
    token_usage = Column(JSON, nullable=True)  # For LLM-based agents

    # Relationships
    project = relationship("Project", back_populates="agent_results")

    def __repr__(self) -> str:
        return f"<AgentResult(id={self.id}, agent={self.agent_id}, status={self.status})>"
