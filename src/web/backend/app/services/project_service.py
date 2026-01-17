"""
Project service - Business logic for project management.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any

from app.models.project import Project
from app.schemas.enums import WorkflowMode, ProjectStatus


class ProjectService:
    """Service for project CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_project(
        self,
        name: str,
        mode: WorkflowMode,
        input_data: Dict[str, Any],
    ) -> Project:
        """Create a new project."""
        project = Project(
            name=name,
            mode=mode,
            status=ProjectStatus.PENDING,
            current_phase="input",
        )

        # Store input based on mode
        if mode == WorkflowMode.DISCOVERY:
            project.project_overview = input_data
        else:
            project.project_spec = input_data

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
        current_phase: Optional[str] = None,
    ) -> Optional[Project]:
        """Update project status."""
        project = await self.get_project(project_id)
        if not project:
            return None

        project.status = status
        if current_phase:
            project.current_phase = current_phase

        await self.db.commit()
        await self.db.refresh(project)

        return project

    async def save_artifact(
        self,
        project_id: str,
        artifact_type: str,
        artifact_data: Dict[str, Any],
    ) -> Optional[Project]:
        """Save an artifact to the project."""
        project = await self.get_project(project_id)
        if not project:
            return None

        if artifact_type == "product_design":
            project.product_design = artifact_data
        elif artifact_type == "architecture_design":
            project.architecture_design = artifact_data
        elif artifact_type == "requirements":
            project.requirements = artifact_data
        elif artifact_type == "generated_code":
            project.generated_code = artifact_data

        await self.db.commit()
        await self.db.refresh(project)

        return project
