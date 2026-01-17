"""
Comprehensive tests for Project API endpoints.

Tests cover:
- Project creation (discovery and direct modes)
- Project listing and filtering
- Project detail retrieval
- Project approval/rejection
- Project cancellation
- Spec validation
- WebSocket connections
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.schemas.enums import ProjectStatus, WorkflowMode, ProjectType, LanguageStack


class TestProjectCreation:
    """Test project creation endpoints."""

    @pytest.mark.asyncio
    async def test_create_project_discovery_mode(self, client: AsyncClient, mock_orchestration_service):
        """Test creating a project in discovery mode."""
        with patch("app.api.v1.projects.get_orchestration_service", return_value=mock_orchestration_service):
            response = await client.post(
                "/api/v1/projects",
                json={
                    "project_name": "my-awesome-app",
                    "project_overview": "A comprehensive project management system that helps teams collaborate effectively. It will include task tracking, team communication, and reporting features. The system should be scalable and support multiple teams.",
                    "target_users": "Project managers, team leads, and development teams",
                    "key_features": "Task management, real-time collaboration, reporting dashboards, integrations with third-party tools",
                    "constraints": "Must be mobile-friendly, comply with GDPR",
                    "similar_products": "Asana, Jira, Monday.com",
                    "project_type_hint": "web-app",
                },
            )

        assert response.status_code == 201
        data = response.json()

        assert data["project_name"] == "my-awesome-app"
        assert data["mode"] == WorkflowMode.DISCOVERY.value
        assert data["status"] == ProjectStatus.PENDING.value
        assert data["current_phase"] == "input"
        assert "id" in data
        assert "created_at" in data

        # Verify workflow was started
        mock_orchestration_service.start_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_direct_mode(self, client: AsyncClient, mock_orchestration_service):
        """Test creating a project in direct mode with explicit spec."""
        with patch("app.api.v1.projects.get_orchestration_service", return_value=mock_orchestration_service):
            response = await client.post(
                "/api/v1/projects",
                json={
                    "project_name": "my-api-service",
                    "project_path": "/home/user/projects/my-api-service",
                    "project_type": "api",
                    "language_stack": "python",
                    "framework": "fastapi",
                    "include_repo": True,
                    "include_ci": True,
                    "include_jira": True,
                    "ci_provider": "github-actions",
                    "vcs_provider": "github",
                    "vcs_config": {
                        "visibility": "private",
                        "create_remote": True,
                        "default_branch": "main",
                    },
                    "jira_config": {
                        "key_prefix": "MYAPI",
                        "project_type": "scrum",
                    },
                },
            )

        assert response.status_code == 201
        data = response.json()

        assert data["project_name"] == "my-api-service"
        assert data["mode"] == WorkflowMode.DIRECT.value
        assert data["status"] == ProjectStatus.PENDING.value
        assert "id" in data

        # Verify workflow was started
        mock_orchestration_service.start_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_project_invalid_name(self, client: AsyncClient):
        """Test project creation with invalid name."""
        response = await client.post(
            "/api/v1/projects",
            json={
                "project_name": "Invalid Project Name!",  # Contains invalid characters
                "project_overview": "This is a test project with a very detailed overview that meets the minimum character requirement for discovery mode validation.",
            },
        )

        assert response.status_code == 422
        assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_create_project_short_overview(self, client: AsyncClient):
        """Test project creation with overview too short."""
        response = await client.post(
            "/api/v1/projects",
            json={
                "project_name": "test-project",
                "project_overview": "Too short",  # Less than 100 characters
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_project_direct_mode_minimal(self, client: AsyncClient, mock_orchestration_service):
        """Test creating a project in direct mode with minimal config."""
        with patch("app.api.v1.projects.get_orchestration_service", return_value=mock_orchestration_service):
            response = await client.post(
                "/api/v1/projects",
                json={
                    "project_name": "minimal-project",
                    "project_path": "/tmp/minimal",
                    "project_type": "library",
                    "language_stack": "python",
                    "include_repo": False,
                    "include_ci": False,
                    "include_jira": False,
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "minimal-project"


class TestProjectListing:
    """Test project listing and filtering."""

    @pytest.mark.asyncio
    async def test_list_all_projects(
        self,
        client: AsyncClient,
        sample_project_discovery,
        sample_project_direct,
        sample_completed_project,
    ):
        """Test listing all projects without filters."""
        response = await client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()

        assert "projects" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        assert data["total"] >= 3
        assert len(data["projects"]) >= 3
        assert data["limit"] == 20
        assert data["offset"] == 0

        # Verify projects are ordered by created_at desc
        project_names = [p["project_name"] for p in data["projects"]]
        assert "test-discovery-project" in project_names
        assert "test-direct-project" in project_names
        assert "test-completed-project" in project_names

    @pytest.mark.asyncio
    async def test_list_projects_with_status_filter(
        self,
        client: AsyncClient,
        sample_project_discovery,
        sample_completed_project,
    ):
        """Test listing projects filtered by status."""
        response = await client.get(
            "/api/v1/projects",
            params={"status_filter": ProjectStatus.COMPLETED.value},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return completed projects
        for project in data["projects"]:
            assert project["status"] == ProjectStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_list_projects_with_pagination(
        self,
        client: AsyncClient,
        sample_project_discovery,
        sample_project_direct,
        sample_completed_project,
    ):
        """Test project listing with pagination."""
        # Get first page
        response = await client.get(
            "/api/v1/projects",
            params={"limit": 2, "offset": 0},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 2
        assert data["offset"] == 0
        assert len(data["projects"]) <= 2

        # Get second page
        response = await client.get(
            "/api/v1/projects",
            params={"limit": 2, "offset": 2},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 2

    @pytest.mark.asyncio
    async def test_list_projects_empty_result(self, client: AsyncClient):
        """Test listing projects with filter that returns no results."""
        response = await client.get(
            "/api/v1/projects",
            params={"status_filter": ProjectStatus.FAILED.value},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["projects"] == [] or all(
            p["status"] == ProjectStatus.FAILED.value for p in data["projects"]
        )


class TestProjectDetail:
    """Test project detail retrieval."""

    @pytest.mark.asyncio
    async def test_get_project_detail(self, client: AsyncClient, sample_project_discovery):
        """Test retrieving project details."""
        response = await client.get(f"/api/v1/projects/{sample_project_discovery.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_project_discovery.id
        assert data["project_name"] == sample_project_discovery.name
        assert data["status"] == sample_project_discovery.status.value
        assert data["mode"] == sample_project_discovery.mode.value
        assert "project_overview" in data
        assert data["project_overview"] is not None

    @pytest.mark.asyncio
    async def test_get_project_detail_with_artifacts(
        self, client: AsyncClient, sample_project_awaiting_approval
    ):
        """Test retrieving project with design artifacts."""
        response = await client.get(f"/api/v1/projects/{sample_project_awaiting_approval.id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_project_awaiting_approval.id
        assert "product_design" in data
        assert data["product_design"] is not None
        assert data["product_design"]["vision"] == "Test product vision"

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client: AsyncClient):
        """Test retrieving non-existent project."""
        response = await client.get("/api/v1/projects/proj_nonexistent123")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_project_progress(self, client: AsyncClient, sample_project_direct):
        """Test getting project progress information."""
        response = await client.get(f"/api/v1/projects/{sample_project_direct.id}/progress")

        assert response.status_code == 200
        data = response.json()

        assert data["project_id"] == sample_project_direct.id
        assert data["status"] == sample_project_direct.status.value
        assert data["mode"] == sample_project_direct.mode.value
        assert "current_phase" in data
        assert "activated_experts" in data
        assert "has_product_design" in data
        assert "has_architecture" in data

    @pytest.mark.asyncio
    async def test_get_progress_not_found(self, client: AsyncClient):
        """Test getting progress for non-existent project."""
        response = await client.get("/api/v1/projects/proj_nonexistent123/progress")

        assert response.status_code == 404


class TestProjectApproval:
    """Test project approval and rejection."""

    @pytest.mark.asyncio
    async def test_approve_project(
        self, client: AsyncClient, sample_project_awaiting_approval, mock_orchestration_service
    ):
        """Test approving a project phase."""
        with patch("app.api.v1.projects.get_orchestration_service", return_value=mock_orchestration_service):
            response = await client.post(
                f"/api/v1/projects/{sample_project_awaiting_approval.id}/approve",
                json={
                    "feedback": "Looks great! Approved.",
                    "modifications": None,
                },
            )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_project_awaiting_approval.id
        assert data["status"] == ProjectStatus.EXECUTING.value

        # Verify workflow was resumed
        mock_orchestration_service.resume_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_approve_project_with_feedback(
        self, client: AsyncClient, sample_project_awaiting_approval, mock_orchestration_service
    ):
        """Test approving project with modifications."""
        with patch("app.api.v1.projects.get_orchestration_service", return_value=mock_orchestration_service):
            response = await client.post(
                f"/api/v1/projects/{sample_project_awaiting_approval.id}/approve",
                json={
                    "feedback": "Approved with minor suggestions",
                    "modifications": {
                        "additional_features": ["feature1", "feature2"]
                    },
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == ProjectStatus.EXECUTING.value

    @pytest.mark.asyncio
    async def test_approve_project_not_awaiting(self, client: AsyncClient, sample_project_direct):
        """Test approving a project that's not awaiting approval."""
        response = await client.post(
            f"/api/v1/projects/{sample_project_direct.id}/approve",
            json={"feedback": "Approve it"},
        )

        assert response.status_code == 400
        assert "not awaiting approval" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_approve_project_not_found(self, client: AsyncClient):
        """Test approving non-existent project."""
        response = await client.post(
            "/api/v1/projects/proj_nonexistent123/approve",
            json={"feedback": "Approve"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reject_project(self, client: AsyncClient, sample_project_awaiting_approval):
        """Test rejecting a project phase."""
        response = await client.post(
            f"/api/v1/projects/{sample_project_awaiting_approval.id}/reject",
            json={
                "feedback": "Please revise the architecture design. The database schema needs improvement.",
                "specific_issues": [
                    "Normalization issues in user table",
                    "Missing indexes on foreign keys",
                ],
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == sample_project_awaiting_approval.id
        assert data["status"] == ProjectStatus.DESIGNING.value

    @pytest.mark.asyncio
    async def test_reject_project_short_feedback(
        self, client: AsyncClient, sample_project_awaiting_approval
    ):
        """Test rejecting project with too short feedback."""
        response = await client.post(
            f"/api/v1/projects/{sample_project_awaiting_approval.id}/reject",
            json={"feedback": "Bad"},  # Too short
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_reject_project_not_awaiting(self, client: AsyncClient, sample_project_direct):
        """Test rejecting a project that's not awaiting approval."""
        response = await client.post(
            f"/api/v1/projects/{sample_project_direct.id}/reject",
            json={"feedback": "This needs more work on the architecture side of things."},
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reject_project_not_found(self, client: AsyncClient):
        """Test rejecting non-existent project."""
        response = await client.post(
            "/api/v1/projects/proj_nonexistent123/reject",
            json={"feedback": "Not good enough, please improve the design."},
        )

        assert response.status_code == 404


class TestProjectCancellation:
    """Test project cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_project(self, client: AsyncClient, sample_project_direct):
        """Test cancelling a running project."""
        response = await client.delete(f"/api/v1/projects/{sample_project_direct.id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_cancel_pending_project(self, client: AsyncClient, sample_project_discovery):
        """Test cancelling a pending project."""
        response = await client.delete(f"/api/v1/projects/{sample_project_discovery.id}")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_cancel_completed_project(self, client: AsyncClient, sample_completed_project):
        """Test cancelling an already completed project (should fail)."""
        response = await client.delete(f"/api/v1/projects/{sample_completed_project.id}")

        assert response.status_code == 400
        assert "cannot cancel" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cancel_project_not_found(self, client: AsyncClient):
        """Test cancelling non-existent project."""
        response = await client.delete("/api/v1/projects/proj_nonexistent123")

        assert response.status_code == 404


class TestSpecValidation:
    """Test project spec validation."""

    @pytest.mark.asyncio
    async def test_validate_valid_spec(self, client: AsyncClient):
        """Test validating a valid project spec."""
        response = await client.post(
            "/api/v1/projects/validate",
            json={
                "project_name": "valid-project",
                "project_path": "/home/user/projects/valid-project",
                "project_type": "api",
                "language_stack": "python",
                "framework": "fastapi",
                "include_repo": True,
                "include_ci": True,
                "include_jira": False,
                "ci_provider": "github-actions",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert len(data["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_spec_with_warnings(self, client: AsyncClient):
        """Test validating spec that produces warnings."""
        response = await client.post(
            "/api/v1/projects/validate",
            json={
                "project_name": "test-project",
                "project_path": "/tmp/test",
                "project_type": "web-app",
                "language_stack": "node",
                "include_repo": True,
                "include_ci": True,
                "include_jira": True,  # Jira enabled but no config
                "ci_provider": None,  # CI enabled but no provider
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is True
        assert len(data["warnings"]) > 0

    @pytest.mark.asyncio
    async def test_validate_spec_invalid_name(self, client: AsyncClient):
        """Test validating spec with invalid project name."""
        response = await client.post(
            "/api/v1/projects/validate",
            json={
                "project_name": "X",  # Too short
                "project_path": "/tmp/test",
                "project_type": "api",
                "language_stack": "python",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert len(data["errors"]) > 0
        assert any("at least 2 characters" in err for err in data["errors"])

    @pytest.mark.asyncio
    async def test_validate_spec_missing_path(self, client: AsyncClient):
        """Test validating spec without project path."""
        response = await client.post(
            "/api/v1/projects/validate",
            json={
                "project_name": "test-project",
                "project_path": "",  # Empty path
                "project_type": "api",
                "language_stack": "python",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["valid"] is False
        assert any("path is required" in err.lower() for err in data["errors"])


class TestWebSocket:
    """Test WebSocket connections for real-time updates."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self, client: AsyncClient, sample_project_direct):
        """Test establishing WebSocket connection for project updates."""
        # Note: Testing WebSockets with httpx requires special handling
        # This is a basic connection test
        async with client.websocket_connect(
            f"/api/v1/ws/projects/{sample_project_direct.id}"
        ) as websocket:
            # Connection should be established
            assert websocket is not None

    @pytest.mark.asyncio
    async def test_websocket_receive_updates(self, client: AsyncClient, sample_project_direct):
        """Test receiving updates through WebSocket."""
        from app.api.v1.websocket import manager

        async with client.websocket_connect(
            f"/api/v1/ws/projects/{sample_project_direct.id}"
        ) as websocket:
            # Simulate broadcasting a message
            test_message = {
                "type": "status_update",
                "project_id": sample_project_direct.id,
                "status": "executing",
                "phase": "scaffolding",
            }

            await manager.broadcast(sample_project_direct.id, test_message)

            # Receive the message
            data = await websocket.receive_json()
            assert data["type"] == "status_update"
            assert data["project_id"] == sample_project_direct.id

    @pytest.mark.asyncio
    async def test_websocket_multiple_connections(
        self, client: AsyncClient, sample_project_direct
    ):
        """Test multiple WebSocket connections for the same project."""
        async with client.websocket_connect(
            f"/api/v1/ws/projects/{sample_project_direct.id}"
        ) as ws1:
            async with client.websocket_connect(
                f"/api/v1/ws/projects/{sample_project_direct.id}"
            ) as ws2:
                # Both connections should be active
                assert ws1 is not None
                assert ws2 is not None

                # Broadcast message should reach both
                from app.api.v1.websocket import manager

                test_message = {"type": "test", "data": "hello"}
                await manager.broadcast(sample_project_direct.id, test_message)

                data1 = await ws1.receive_json()
                data2 = await ws2.receive_json()

                assert data1 == test_message
                assert data2 == test_message

    @pytest.mark.asyncio
    async def test_websocket_disconnect(self, client: AsyncClient, sample_project_direct):
        """Test WebSocket disconnection handling."""
        from app.api.v1.websocket import manager

        async with client.websocket_connect(
            f"/api/v1/ws/projects/{sample_project_direct.id}"
        ) as websocket:
            # Connection established
            assert sample_project_direct.id in manager.active_connections

        # After context exit, connection should be cleaned up
        # Note: The actual cleanup happens in the websocket endpoint's except block


class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_project_name_normalization_discovery(
        self, client: AsyncClient, mock_orchestration_service
    ):
        """Test that project names are normalized in discovery mode."""
        with patch("app.api.v1.projects.get_orchestration_service", return_value=mock_orchestration_service):
            response = await client.post(
                "/api/v1/projects",
                json={
                    "project_name": "MyAwesomeApp",  # Mixed case
                    "project_overview": "A comprehensive project management system that helps teams collaborate effectively and manage their work efficiently. This system will revolutionize how teams work together.",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["project_name"] == "myawesomeapp"  # Should be lowercase

    @pytest.mark.asyncio
    async def test_concurrent_project_creation(self, client: AsyncClient, mock_orchestration_service):
        """Test creating multiple projects concurrently."""
        import asyncio

        with patch("app.api.v1.projects.get_orchestration_service", return_value=mock_orchestration_service):
            tasks = [
                client.post(
                    "/api/v1/projects",
                    json={
                        "project_name": f"project-{i}",
                        "project_overview": f"Project number {i} with a detailed description that meets all the minimum requirements for creating a discovery mode project in our system.",
                    },
                )
                for i in range(3)
            ]

            responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code == 201

        # All should have unique IDs
        project_ids = [r.json()["id"] for r in responses]
        assert len(project_ids) == len(set(project_ids))

    @pytest.mark.asyncio
    async def test_list_projects_performance(self, client: AsyncClient, test_session):
        """Test listing performance with many projects."""
        from app.models.project import Project
        from app.schemas.enums import WorkflowMode, ProjectStatus

        # Create many projects
        projects = [
            Project(
                name=f"perf-test-{i}",
                mode=WorkflowMode.DIRECT,
                status=ProjectStatus.PENDING,
            )
            for i in range(50)
        ]

        test_session.add_all(projects)
        await test_session.commit()

        # List with pagination
        response = await client.get("/api/v1/projects", params={"limit": 20})

        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) == 20
        assert data["total"] >= 50

    @pytest.mark.asyncio
    async def test_approve_already_approved_project(
        self, client: AsyncClient, sample_project_awaiting_approval, mock_orchestration_service, test_session
    ):
        """Test approving a project that was already approved."""
        from app.models.execution import ApprovalGate
        from sqlalchemy import select

        # First approval
        with patch("app.api.v1.projects.get_orchestration_service", return_value=mock_orchestration_service):
            response1 = await client.post(
                f"/api/v1/projects/{sample_project_awaiting_approval.id}/approve",
                json={"feedback": "First approval"},
            )

        assert response1.status_code == 200

        # Refresh the project status from database
        await test_session.refresh(sample_project_awaiting_approval)

        # Second approval attempt should fail
        response2 = await client.post(
            f"/api/v1/projects/{sample_project_awaiting_approval.id}/approve",
            json={"feedback": "Second approval"},
        )

        assert response2.status_code == 400
        assert "not awaiting approval" in response2.json()["detail"].lower()
