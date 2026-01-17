# Project Bootstrap Web App API Documentation

Complete API documentation for the Project Bootstrap Web App - a multi-agent orchestration system for automated project scaffolding.

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Authentication](#authentication)
4. [Core Concepts](#core-concepts)
5. [API Endpoints](#api-endpoints)
6. [WebSocket Real-time Updates](#websocket-real-time-updates)
7. [Error Handling](#error-handling)
8. [Examples](#examples)
9. [Integration Points](#integration-points)

## Overview

The Project Bootstrap API enables automated creation of new software projects with integrated tooling for Git, CI/CD, and Jira. The system supports two operational modes:

- **Discovery Mode**: Users provide a high-level project overview, and the system generates detailed specifications
- **Direct Mode**: Users specify exact technology stack and configuration upfront

## Getting Started

### Base URL

Development:
```
http://localhost:8000/api/v1
```

Production:
```
https://api.bootstrap.example.com/api/v1
```

### Health Check

Verify API availability:

```bash
curl -X GET http://localhost:8000/api/v1/health
```

Response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Authentication

Authentication is currently optional but prepared for JWT Bearer token integration.

### Future Bearer Token Usage

Include the token in request headers:

```bash
curl -X GET http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <your-jwt-token>"
```

## Core Concepts

### Project Workflow Phases

Projects progress through the following phases:

1. **Input** - Specification collection and validation
   - Discovery Mode: Receives project overview
   - Direct Mode: Receives full specification

2. **Designing** - Product design and architecture planning
   - Product Owner Agent generates product design
   - Architecture Agents generate system design
   - Domain Experts provide compliance guidance
   - Status: AWAITING_APPROVAL (requires user feedback)

3. **Executing** - Implementation and provisioning
   - Filesystem scaffolding
   - Git repository initialization
   - CI/CD pipeline generation
   - Jira project provisioning (optional)

4. **Completed** - Project ready for development
   - All artifacts generated
   - Remote repositories created
   - CI/CD pipelines deployed

### Project Statuses

- `pending` - Project created, awaiting processing
- `input_received` - Input specification received
- `designing` - Design phase in progress
- `awaiting_approval` - Awaiting user approval of artifacts
- `executing` - Execution phase in progress
- `completed` - Project creation complete
- `failed` - Execution failed
- `cancelled` - Project cancelled by user

### Request Schemas

#### ProjectOverviewCreate (Discovery Mode)

Used when users provide high-level project description:

```json
{
  "project_name": "task-manager",
  "project_overview": "A collaborative task management application for small teams to organize, track, and complete work together. Support for real-time updates, task dependencies, and team collaboration.",
  "target_users": "Small to medium teams, project managers, developers",
  "key_features": "Real-time collaboration, task dependencies, team messaging, progress tracking",
  "constraints": "Must support 1000+ concurrent users, deployable on AWS",
  "similar_products": "Jira, Asana, Monday.com",
  "project_type_hint": "web-app"
}
```

**Field Requirements:**
- `project_name`: 2-64 chars, alphanumeric with hyphens/underscores, must start with letter
- `project_overview`: 100-5000 chars, detailed project description
- `target_users`: Optional, 0-1000 chars
- `key_features`: Optional, 0-2000 chars
- `constraints`: Optional, 0-1000 chars
- `similar_products`: Optional, 0-500 chars
- `project_type_hint`: Optional, hint for system selection

#### ProjectSpecCreate (Direct Mode)

Used when users specify exact configuration:

```json
{
  "project_name": "task-api",
  "project_path": "/home/user/projects/",
  "project_type": "api",
  "language_stack": "python",
  "framework": "fastapi",
  "include_repo": true,
  "include_ci": true,
  "include_jira": false,
  "ci_provider": "github-actions",
  "vcs_provider": "github",
  "vcs_config": {
    "visibility": "private",
    "create_remote": true,
    "default_branch": "main"
  },
  "jira_config": {
    "key_prefix": "PROJ",
    "project_type": "scrum"
  }
}
```

**Field Requirements:**
- `project_name`: 2-64 chars, lowercase alphanumeric with hyphens
- `project_path`: Valid filesystem path
- `project_type`: One of [web-app, api, library, cli, monorepo, ml-project, ai-app, full-platform]
- `language_stack`: One of [python, node, java, go, rust, dotnet, multi]
- `framework`: Optional (e.g., fastapi, django, express, spring-boot)
- `include_repo`: Boolean, initialize Git repository
- `include_ci`: Boolean, generate CI/CD pipeline
- `include_jira`: Boolean, create Jira project
- `ci_provider`: One of [github-actions, gitlab-ci, azure-pipelines]
- `vcs_provider`: One of [github, gitlab, bitbucket]
- `vcs_config`: Optional VCS configuration
- `jira_config`: Required if include_jira is true

## API Endpoints

### Projects

#### Create Project

Create a new project in either Discovery or Direct mode.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "task-manager",
    "project_overview": "A collaborative task management application...",
    "project_type_hint": "web-app"
  }'
```

**Response:** `201 Created`
```json
{
  "id": "proj_abc123xyz",
  "status": "input_received",
  "mode": "discovery",
  "current_phase": "input",
  "project_name": "task-manager",
  "created_at": "2024-01-14T10:30:00Z",
  "updated_at": "2024-01-14T10:30:00Z",
  "completed_at": null
}
```

**Error Responses:**
- `400 Bad Request`: Invalid project specification
- `422 Unprocessable Entity`: Validation error

---

#### List Projects

Retrieve paginated list of projects with optional filtering.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/projects?status=completed&limit=20&offset=0"
```

**Query Parameters:**
- `status` (optional): Filter by project status
- `limit` (optional, default: 20, max: 100): Results per page
- `offset` (optional, default: 0): Pagination offset

**Response:** `200 OK`
```json
{
  "projects": [
    {
      "id": "proj_abc123xyz",
      "status": "completed",
      "mode": "discovery",
      "current_phase": "executing",
      "project_name": "task-manager",
      "created_at": "2024-01-14T10:30:00Z",
      "updated_at": "2024-01-14T11:00:00Z",
      "completed_at": "2024-01-14T11:00:00Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

---

#### Get Project Details

Retrieve detailed information about a specific project.

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/projects/proj_abc123xyz
```

**Response:** `200 OK`
```json
{
  "id": "proj_abc123xyz",
  "status": "awaiting_approval",
  "mode": "discovery",
  "current_phase": "designing",
  "project_name": "task-manager",
  "created_at": "2024-01-14T10:30:00Z",
  "updated_at": "2024-01-14T10:35:00Z",
  "completed_at": null,
  "project_overview": {
    "target_users": "Small to medium teams",
    "key_features": "Real-time collaboration"
  },
  "product_design": {
    "vision": "Collaborative task management platform",
    "goals": ["Enable team collaboration", "Improve productivity"],
    "personas": [...],
    "epics": [...],
    "mvp_scope": {...},
    "risks": [...],
    "success_metrics": [...]
  },
  "architecture_design": {
    "tech_stack": {
      "backend": "FastAPI + Python",
      "frontend": "React",
      "database": "PostgreSQL",
      "infrastructure": "AWS"
    },
    "system_components": [...],
    "data_model": {...},
    "api_design": {...},
    "security": {...},
    "infrastructure": {...}
  }
}
```

**Error Response:** `404 Not Found`
```json
{
  "error": "not_found",
  "message": "Project proj_abc123xyz not found",
  "request_id": "req_xyz789"
}
```

---

#### Get Project Progress

Retrieve current workflow progress.

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/projects/proj_abc123xyz/progress
```

**Response:** `200 OK`
```json
{
  "project_id": "proj_abc123xyz",
  "status": "awaiting_approval",
  "mode": "discovery",
  "current_phase": "designing",
  "activated_experts": ["healthcare-expert", "security-expert"],
  "has_product_design": true,
  "has_architecture": true
}
```

---

#### Validate Specification

Validate a project specification without creating a project.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/projects/validate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "task-api",
    "project_path": "/home/user/projects/",
    "project_type": "api",
    "language_stack": "python",
    "framework": "fastapi"
  }'
```

**Response:** `200 OK`
```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Jira integration enabled but no config provided"
  ]
}
```

---

#### Approve Phase

Approve current workflow phase and resume execution.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/projects/proj_abc123xyz/approve \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Looks good, proceed with execution",
    "modifications": null
  }'
```

**Response:** `200 OK`
```json
{
  "id": "proj_abc123xyz",
  "status": "executing",
  "mode": "discovery",
  "current_phase": "executing",
  "project_name": "task-manager",
  "created_at": "2024-01-14T10:30:00Z",
  "updated_at": "2024-01-14T10:36:00Z"
}
```

**Error Response:** `400 Bad Request`
```json
{
  "error": "invalid_state",
  "message": "Project is not awaiting approval",
  "request_id": "req_xyz789"
}
```

---

#### Reject Phase

Reject current workflow phase with feedback.

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/projects/proj_abc123xyz/reject \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "The architecture doesn'\''t align with our security requirements. Please revise.",
    "specific_issues": [
      "No end-to-end encryption mentioned",
      "HIPAA compliance not addressed"
    ]
  }'
```

**Response:** `200 OK`
```json
{
  "id": "proj_abc123xyz",
  "status": "designing",
  "mode": "discovery",
  "current_phase": "designing",
  "project_name": "task-manager",
  "created_at": "2024-01-14T10:30:00Z",
  "updated_at": "2024-01-14T10:37:00Z"
}
```

---

#### Cancel Project

Cancel a running project.

**Request:**
```bash
curl -X DELETE http://localhost:8000/api/v1/projects/proj_abc123xyz
```

**Response:** `204 No Content`

**Error Responses:**
- `400 Bad Request`: Project already completed or cancelled
- `404 Not Found`: Project not found

---

### Templates

#### List Templates

Retrieve available project templates.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/templates?project_type=api&language_stack=python"
```

**Query Parameters:**
- `project_type` (optional): Filter by project type
- `language_stack` (optional): Filter by language

**Response:** `200 OK`
```json
{
  "templates": [
    {
      "id": "template_fastapi_001",
      "name": "FastAPI REST API",
      "description": "Production-ready FastAPI REST API template",
      "project_type": "api",
      "language_stack": "python",
      "framework": "fastapi"
    }
  ]
}
```

---

#### Get Template Details

Retrieve detailed information about a template.

**Request:**
```bash
curl -X GET http://localhost:8000/api/v1/templates/template_fastapi_001
```

**Response:** `200 OK`
```json
{
  "id": "template_fastapi_001",
  "name": "FastAPI REST API",
  "description": "Production-ready FastAPI REST API template",
  "project_type": "api",
  "language_stack": "python",
  "frameworks": ["fastapi"],
  "directory_structure": {
    "src": {
      "app": ["main.py", "config.py"]
    },
    "tests": ["test_api.py"],
    "docs": ["README.md"]
  },
  "files": ["setup.py", "requirements.txt", "Dockerfile", ".github/workflows/ci.yml"]
}
```

---

## WebSocket Real-time Updates

Connect to receive real-time project updates as the workflow progresses.

### Connection

```javascript
const projectId = 'proj_abc123xyz';
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/projects/${projectId}`);

ws.onopen = (event) => {
  console.log('Connected to project updates');
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = (event) => {
  console.log('Disconnected from project updates');
};
```

### Message Types

#### Connected
Sent when client successfully connects.

```json
{
  "type": "connected",
  "timestamp": "2024-01-14T10:30:00Z",
  "project_id": "proj_123",
  "message": "Connected to project updates"
}
```

---

#### Phase Started
Sent when a workflow phase begins.

```json
{
  "type": "phase_started",
  "timestamp": "2024-01-14T10:30:05Z",
  "project_id": "proj_123",
  "phase": "designing",
  "phase_display_name": "Designing"
}
```

---

#### Phase Completed
Sent when a workflow phase finishes.

```json
{
  "type": "phase_completed",
  "timestamp": "2024-01-14T10:35:00Z",
  "project_id": "proj_123",
  "phase": "designing",
  "status": "completed",
  "duration_ms": 295000
}
```

---

#### Agent Started
Sent when an agent begins execution.

```json
{
  "type": "agent_started",
  "timestamp": "2024-01-14T10:30:10Z",
  "project_id": "proj_123",
  "agent_id": "agent_po",
  "agent_name": "Product Owner",
  "phase": "designing"
}
```

---

#### Agent Progress
Sent periodically during agent execution.

```json
{
  "type": "agent_progress",
  "timestamp": "2024-01-14T10:31:00Z",
  "project_id": "proj_123",
  "agent_id": "agent_po",
  "agent_name": "Product Owner",
  "progress_percent": 45,
  "message": "Generating user stories"
}
```

---

#### Agent Completed
Sent when an agent finishes execution.

```json
{
  "type": "agent_completed",
  "timestamp": "2024-01-14T10:32:00Z",
  "project_id": "proj_123",
  "agent_id": "agent_po",
  "agent_name": "Product Owner",
  "status": "completed",
  "duration_ms": 120000,
  "output_preview": "Generated product design with 5 epics and 23 user stories"
}
```

---

#### Approval Required
Sent when workflow pauses for user approval.

```json
{
  "type": "approval_required",
  "timestamp": "2024-01-14T10:33:00Z",
  "project_id": "proj_123",
  "phase": "designing",
  "artifact_type": "product_design",
  "artifact_preview": {
    "vision": "Collaborative task management platform",
    "epics": 5,
    "user_stories": 23
  }
}
```

---

#### Workflow Completed
Sent when entire workflow finishes.

```json
{
  "type": "workflow_completed",
  "timestamp": "2024-01-14T11:00:00Z",
  "project_id": "proj_123",
  "status": "completed",
  "duration_ms": 1800000,
  "summary": {
    "phases_completed": 4,
    "agents_executed": 12,
    "artifacts_generated": 8
  }
}
```

---

#### Error
Sent when an error occurs.

```json
{
  "type": "error",
  "timestamp": "2024-01-14T10:34:00Z",
  "project_id": "proj_123",
  "error_code": "AGENT_FAILURE",
  "error_message": "Agent failed with exception",
  "phase": "designing",
  "agent_id": "agent_architect"
}
```

---

#### Log
Sent for informational logging.

```json
{
  "type": "log",
  "timestamp": "2024-01-14T10:30:15Z",
  "project_id": "proj_123",
  "level": "info",
  "agent_id": "agent_po",
  "message": "Analyzing project overview"
}
```

---

## Error Handling

The API uses standard HTTP status codes and provides structured error responses.

### Error Status Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input or operation |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "request_id": "req_xyz789"
}
```

### Validation Errors

```json
{
  "error": "validation_error",
  "message": "Validation failed",
  "details": [
    {
      "field": "project_name",
      "message": "Project name must start with a letter",
      "code": "pattern_mismatch"
    },
    {
      "field": "language_stack",
      "message": "This field is required",
      "code": "required"
    }
  ]
}
```

---

## Examples

### Complete Workflow: Discovery Mode

#### Step 1: Create Project
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "task-manager",
    "project_overview": "A collaborative task management application for small teams to organize, track, and complete work together. Support for real-time updates, task dependencies, and team collaboration.",
    "target_users": "Small to medium teams, project managers, developers",
    "key_features": "Real-time collaboration, task dependencies, team messaging, progress tracking",
    "project_type_hint": "web-app"
  }'
```

Response:
```json
{
  "id": "proj_abc123xyz",
  "status": "input_received",
  "mode": "discovery",
  "current_phase": "input",
  "project_name": "task-manager",
  "created_at": "2024-01-14T10:30:00Z"
}
```

#### Step 2: Connect WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/projects/proj_abc123xyz');
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(`[${msg.type}] ${msg.message || msg.phase}`);
};
```

#### Step 3: Monitor Workflow
The WebSocket receives events as the system processes:
- `phase_started`: designing
- `agent_started`: Product Owner Agent
- `agent_progress`: Generating product design
- `agent_completed`: Product Owner Agent
- `approval_required`: Artifact type: product_design

#### Step 4: Get Project Details
```bash
curl -X GET http://localhost:8000/api/v1/projects/proj_abc123xyz
```

Returns detailed product design and architecture artifacts.

#### Step 5: Approve Phase
```bash
curl -X POST http://localhost:8000/api/v1/projects/proj_abc123xyz/approve \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Looks good, proceed"}'
```

Workflow resumes with execution phase.

#### Step 6: Wait for Completion
Monitor WebSocket for `workflow_completed` event, then:

```bash
curl -X GET http://localhost:8000/api/v1/projects/proj_abc123xyz
```

Project is now ready with generated code, repo, and CI/CD pipelines.

---

### Complete Workflow: Direct Mode

#### Step 1: Validate Specification
```bash
curl -X POST http://localhost:8000/api/v1/projects/validate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "task-api",
    "project_path": "/home/user/projects/",
    "project_type": "api",
    "language_stack": "python",
    "framework": "fastapi",
    "include_repo": true,
    "include_ci": true,
    "include_jira": false,
    "ci_provider": "github-actions",
    "vcs_provider": "github"
  }'
```

#### Step 2: Create Project
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "task-api",
    "project_path": "/home/user/projects/",
    "project_type": "api",
    "language_stack": "python",
    "framework": "fastapi",
    "include_repo": true,
    "include_ci": true,
    "include_jira": false,
    "ci_provider": "github-actions",
    "vcs_provider": "github"
  }'
```

Direct mode skips approval gates and proceeds directly to execution.

---

## Integration Points

### GitHub/GitLab Integration

The system can create remote repositories and setup webhooks:

- Creates repository in GitHub/GitLab
- Sets default branch to configured value
- Sets visibility (public/private)
- Configures webhooks for CI/CD triggers

### Jira Integration

When `include_jira: true`:

- Creates Jira project with specified key prefix
- Initializes project structure (scrum/kanban/basic)
- Creates epics and user stories from generated requirements
- Links commits to Jira issues

### CI/CD Integration

Generates CI/CD pipelines for selected providers:

- **GitHub Actions**: `.github/workflows/` configuration
- **GitLab CI**: `.gitlab-ci.yml` configuration
- **Azure Pipelines**: `azure-pipelines.yml` configuration

Pipelines include:
- Dependency installation and caching
- Code quality checks (linting, formatting)
- Test execution
- Build and artifact generation
- Automated deployment triggers

### Local Filesystem

Scaffolds project structure:

- Creates directories and configuration files
- Initializes local Git repository
- Creates .gitignore based on language/framework
- Generates README with setup instructions
- Creates LICENSE file (MIT by default)

---

## Rate Limiting and Quotas

Currently no rate limiting is enforced, but this will be implemented in production:

- Per-minute request limits
- Per-project concurrent operation limits
- Storage quotas for generated artifacts

---

## Support and Feedback

For API issues or feature requests:

- Email: dev-team@bootstrap.local
- Slack: #project-bootstrap-api
- GitHub Issues: [project repository]

---

## Version History

### v1.0.0 (Current)
- Initial release
- Projects CRUD endpoints
- Discovery and Direct modes
- WebSocket real-time updates
- Template browsing
- Approval gates for workflow phases

---

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:

- File: `docs/api/openapi.yaml`
- Swagger UI: `/api/docs`
- ReDoc: `/api/redoc`

---

Last Updated: 2024-01-14
