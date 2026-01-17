"""
Project API endpoints - Create, manage, and monitor projects.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime

from app.core.database import get_db
from app.schemas.project import (
    ProjectOverviewCreate,
    ProjectSpecCreate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectListResponse,
    ApprovalRequest,
    RejectionRequest,
    ValidationResult,
)
from app.schemas.enums import WorkflowMode, ProjectStatus
from app.models.project import Project
from app.models.execution import ApprovalGate
from app.services.project_service import ProjectService
from app.services.orchestration_service import OrchestrationService
from app.services.scaffolding_service import ScaffoldingService

router = APIRouter()


def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    return ProjectService(db)


def get_orchestration_service() -> OrchestrationService:
    return OrchestrationService()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectOverviewCreate | ProjectSpecCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    project_service: ProjectService = Depends(get_project_service),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
):
    """
    Create a new project.

    - **Discovery Mode**: Provide ProjectOverviewCreate with project_overview
    - **Direct Mode**: Provide ProjectSpecCreate with exact stack specification
    """
    # Determine mode based on input type
    if isinstance(project_data, ProjectOverviewCreate):
        mode = WorkflowMode.DISCOVERY
        input_data = project_data.model_dump()
    else:
        mode = WorkflowMode.DIRECT
        input_data = project_data.model_dump()

    # Create project record
    project = await project_service.create_project(
        name=project_data.project_name,
        mode=mode,
        input_data=input_data,
    )

    # Start workflow in background
    background_tasks.add_task(
        orchestration_service.start_workflow,
        project_id=project.id,
        mode=mode,
        input_data=input_data,
    )

    return ProjectResponse(
        id=project.id,
        status=project.status,
        mode=project.mode,
        current_phase=project.current_phase or "input",
        project_name=project.name,
        created_at=project.created_at,
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    status_filter: Optional[ProjectStatus] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List all projects with optional filtering."""
    query = select(Project).order_by(Project.created_at.desc())

    if status_filter:
        query = query.where(Project.status == status_filter)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    projects = result.scalars().all()

    # Get total count
    count_query = select(Project)
    if status_filter:
        count_query = count_query.where(Project.status == status_filter)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return ProjectListResponse(
        projects=[
            ProjectResponse(
                id=p.id,
                status=p.status,
                mode=p.mode,
                current_phase=p.current_phase or "",
                project_name=p.name,
                created_at=p.created_at,
                updated_at=p.updated_at,
                completed_at=p.completed_at,
            )
            for p in projects
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed project information including artifacts."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    return ProjectDetailResponse(
        id=project.id,
        status=project.status,
        mode=project.mode,
        current_phase=project.current_phase or "",
        project_name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
        completed_at=project.completed_at,
        project_overview=project.project_overview,
        project_spec=project.project_spec,
        product_design=project.product_design,
        architecture_design=project.architecture_design,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project.status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed or already cancelled project",
        )

    project.status = ProjectStatus.CANCELLED
    await db.commit()


@router.post("/validate", response_model=ValidationResult)
async def validate_spec(
    spec: ProjectSpecCreate,
):
    """Validate a project specification without creating."""
    errors = []
    warnings = []

    # Validate project name
    if len(spec.project_name) < 2:
        errors.append("Project name must be at least 2 characters")

    # Validate path
    if not spec.project_path:
        errors.append("Project path is required")

    # Check for common issues
    if spec.include_jira and not spec.jira_config:
        warnings.append("Jira integration enabled but no config provided")

    if spec.include_ci and not spec.ci_provider:
        warnings.append("CI enabled but no provider specified, defaulting to GitHub Actions")

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


@router.post("/{project_id}/approve", response_model=ProjectResponse)
async def approve_phase(
    project_id: str,
    approval: ApprovalRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    orchestration_service: OrchestrationService = Depends(get_orchestration_service),
):
    """Approve the current phase and continue workflow."""
    # Get project
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project.status != ProjectStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is not awaiting approval",
        )

    # Get pending approval gate
    gate_result = await db.execute(
        select(ApprovalGate)
        .where(ApprovalGate.project_id == project_id)
        .where(ApprovalGate.status == "pending")
    )
    gate = gate_result.scalar_one_or_none()

    if gate:
        gate.status = "approved"
        gate.feedback = approval.feedback
        gate.resolved_at = datetime.utcnow()

    # Update project status
    project.status = ProjectStatus.EXECUTING
    await db.commit()

    # Resume workflow in background
    background_tasks.add_task(
        orchestration_service.resume_workflow,
        project_id=project_id,
    )

    return ProjectResponse(
        id=project.id,
        status=project.status,
        mode=project.mode,
        current_phase=project.current_phase or "",
        project_name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("/{project_id}/reject", response_model=ProjectResponse)
async def reject_phase(
    project_id: str,
    rejection: RejectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Reject the current phase with feedback."""
    # Get project
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project.status != ProjectStatus.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project is not awaiting approval",
        )

    # Get pending approval gate
    gate_result = await db.execute(
        select(ApprovalGate)
        .where(ApprovalGate.project_id == project_id)
        .where(ApprovalGate.status == "pending")
    )
    gate = gate_result.scalar_one_or_none()

    if gate:
        gate.status = "rejected"
        gate.feedback = rejection.feedback
        gate.resolved_at = datetime.utcnow()

    # Project stays in same phase, waiting for re-run
    project.status = ProjectStatus.DESIGNING
    await db.commit()

    return ProjectResponse(
        id=project.id,
        status=project.status,
        mode=project.mode,
        current_phase=project.current_phase or "",
        project_name=project.name,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.get("/{project_id}/progress")
async def get_progress(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get workflow progress for a project."""
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Build progress response
    return {
        "project_id": project.id,
        "status": project.status.value,
        "mode": project.mode.value,
        "current_phase": project.current_phase,
        "activated_experts": project.activated_experts or [],
        "has_product_design": project.product_design is not None,
        "has_architecture": project.architecture_design is not None,
    }


@router.post("/{project_id}/scaffold")
async def scaffold_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger scaffolding for a project.

    This creates the actual project directory structure with:
    - .claude/agents/*.md - All agent templates
    - docs/ - Documentation structure
    - src/ - Source code directories
    - tests/ - Test directories
    - CLAUDE.md - Project instructions
    """
    result = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Run scaffolding
    scaffolder = ScaffoldingService()

    try:
        scaffold_result = await scaffolder.scaffold_project(
            project_name=project.name,
            product_design=project.product_design,
            architecture_design=project.architecture_design,
        )

        return {
            "status": "success",
            "project_path": scaffold_result.get("project_path"),
            "created_files": scaffold_result.get("created_files", 0),
            "created_directories": scaffold_result.get("created_directories", 0),
            "agents_copied": scaffold_result.get("agents_copied", 0),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scaffolding failed: {str(e)}",
        )
