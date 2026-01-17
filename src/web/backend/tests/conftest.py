"""
Pytest configuration and fixtures for backend tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.models.base import Base
from app.core.database import get_db
from app.config import get_settings, Settings

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/bootstrap_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(test_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    # Override database dependency
    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def mock_orchestration_service(monkeypatch):
    """Mock OrchestrationService for testing."""
    from unittest.mock import AsyncMock

    mock_service = AsyncMock()
    mock_service.start_workflow = AsyncMock()
    mock_service.resume_workflow = AsyncMock()

    return mock_service


@pytest.fixture
async def sample_project_discovery(test_session: AsyncSession):
    """Create a sample project in discovery mode."""
    from app.models.project import Project
    from app.schemas.enums import WorkflowMode, ProjectStatus

    project = Project(
        name="test-discovery-project",
        mode=WorkflowMode.DISCOVERY,
        status=ProjectStatus.PENDING,
        current_phase="input",
        project_overview={
            "project_name": "test-discovery-project",
            "project_overview": "A test project for discovering requirements and architecture through AI agents.",
            "target_users": "Developers who want to bootstrap new projects",
            "key_features": "AI-driven project setup, template selection, automated scaffolding",
        },
    )

    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    return project


@pytest.fixture
async def sample_project_direct(test_session: AsyncSession):
    """Create a sample project in direct mode."""
    from app.models.project import Project
    from app.schemas.enums import WorkflowMode, ProjectStatus, ProjectType, LanguageStack

    project = Project(
        name="test-direct-project",
        mode=WorkflowMode.DIRECT,
        status=ProjectStatus.EXECUTING,
        current_phase="scaffolding",
        project_spec={
            "project_name": "test-direct-project",
            "project_path": "/tmp/test-project",
            "project_type": ProjectType.API.value,
            "language_stack": LanguageStack.PYTHON.value,
            "framework": "fastapi",
            "include_repo": True,
            "include_ci": True,
            "include_jira": False,
        },
    )

    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    return project


@pytest.fixture
async def sample_project_awaiting_approval(test_session: AsyncSession):
    """Create a project awaiting approval with a pending gate."""
    from app.models.project import Project
    from app.models.execution import ApprovalGate
    from app.schemas.enums import WorkflowMode, ProjectStatus, ApprovalStatus

    project = Project(
        name="test-approval-project",
        mode=WorkflowMode.DISCOVERY,
        status=ProjectStatus.AWAITING_APPROVAL,
        current_phase="product_design",
        product_design={
            "vision": "Test product vision",
            "goals": ["Goal 1", "Goal 2"],
            "personas": [{"name": "Developer", "role": "Backend Engineer"}],
            "epics": [{"title": "Epic 1", "description": "Test epic"}],
            "mvp_scope": {"features": ["Feature 1"]},
            "risks": [],
            "success_metrics": [],
        },
    )

    test_session.add(project)
    await test_session.flush()

    # Create approval gate
    gate = ApprovalGate(
        project_id=project.id,
        phase="product_design",
        artifact_type="product_design",
        status=ApprovalStatus.PENDING,
        artifact_snapshot=project.product_design,
    )

    test_session.add(gate)
    await test_session.commit()
    await test_session.refresh(project)

    return project


@pytest.fixture
async def sample_completed_project(test_session: AsyncSession):
    """Create a completed project."""
    from app.models.project import Project
    from app.schemas.enums import WorkflowMode, ProjectStatus
    from datetime import datetime, timedelta

    project = Project(
        name="test-completed-project",
        mode=WorkflowMode.DIRECT,
        status=ProjectStatus.COMPLETED,
        current_phase="summary",
        completed_at=datetime.utcnow(),
        project_spec={
            "project_name": "test-completed-project",
            "project_path": "/tmp/completed-project",
            "project_type": "api",
            "language_stack": "python",
        },
    )

    test_session.add(project)
    await test_session.commit()
    await test_session.refresh(project)

    return project
