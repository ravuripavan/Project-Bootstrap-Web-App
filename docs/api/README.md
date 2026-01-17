# Project Bootstrap API Documentation

Complete API documentation for the Project Bootstrap Web App - a multi-agent orchestration system for automated project scaffolding.

## Documentation Overview

This directory contains comprehensive API documentation for developers, API consumers, and integrators.

### Documentation Files

#### 1. **openapi.yaml** - OpenAPI 3.0 Specification
The complete OpenAPI 3.0 specification for the Project Bootstrap API.

- **Format**: YAML (OpenAPI 3.0.3)
- **Usage**:
  - Import into Swagger Editor, Postman, or API tooling
  - Swagger UI available at: `http://localhost:8000/api/docs`
  - ReDoc available at: `http://localhost:8000/api/redoc`
- **Content**:
  - All REST endpoints with detailed descriptions
  - Complete request and response schemas
  - WebSocket endpoint specifications
  - Error response definitions
  - Security scheme definitions
  - Server configurations (dev and production)
  - Example requests and responses

#### 2. **API.md** - Complete API Documentation
Detailed human-readable documentation covering all aspects of the API.

- **Audience**: Developers, API consumers
- **Content**:
  - Overview and core concepts
  - Getting started guide
  - Authentication information
  - Complete endpoint reference with examples
  - Request/response schemas
  - WebSocket message types and examples
  - Error handling guidelines
  - Integration points (GitHub, GitLab, Jira, CI/CD)
  - Complete workflow examples

#### 3. **QUICK_START.md** - Quick Reference Guide
Fast reference for common API operations and usage patterns.

- **Audience**: Developers looking for quick answers
- **Content**:
  - cURL command examples
  - Common query parameters
  - Enum values reference
  - Status codes and error formats
  - Example workflows
  - Useful tools and utilities
  - Troubleshooting guide

#### 4. **SCHEMAS.md** - Detailed Schema Reference
Complete reference for all request and response schemas.

- **Audience**: Developers integrating with the API
- **Content**:
  - Input schemas (ProjectOverviewCreate, ProjectSpecCreate)
  - Response schemas (ProjectResponse, ProjectDetailResponse, etc.)
  - Nested schemas (VCSConfig, JiraConfig, etc.)
  - Error schemas
  - WebSocket message schemas
  - Field definitions and validation rules
  - Enum values and descriptions
  - Schema relationships diagram

#### 5. **README.md** (this file) - Documentation Index
Overview and navigation guide for all API documentation.

---

## API Overview

### What is Project Bootstrap?

Project Bootstrap is a multi-agent orchestration system that automates the creation of new software projects. It:

- Accepts high-level project descriptions or detailed specifications
- Uses AI agents to design product and architecture
- Generates production-ready project scaffolding
- Integrates with GitHub/GitLab for repository management
- Optionally creates Jira projects and CI/CD pipelines
- Provides real-time progress updates via WebSocket

### Two Operational Modes

#### Discovery Mode
Users provide a high-level project overview, and the system:
1. Analyzes the requirements
2. Generates detailed product design
3. Creates architecture design
4. Requests user approval
5. Executes the plan

#### Direct Mode
Users provide exact specifications (language, framework, tools), and the system:
1. Validates the specification
2. Executes project scaffolding immediately
3. No approval gates required

---

## Quick Links

### For API Consumers

1. **Just getting started?**
   - Read: [Getting Started](#getting-started) below
   - Reference: [QUICK_START.md](QUICK_START.md)

2. **Building an integration?**
   - Read: [API.md](API.md)
   - Reference: [SCHEMAS.md](SCHEMAS.md)
   - Spec: [openapi.yaml](openapi.yaml)

3. **Need to understand a schema?**
   - Reference: [SCHEMAS.md](SCHEMAS.md)
   - View: [openapi.yaml](openapi.yaml) components section

4. **Want to see examples?**
   - Reference: [QUICK_START.md](QUICK_START.md) - Examples section
   - Reference: [API.md](API.md) - Examples section

### For Developers

1. **Backend API development?**
   - Reference: [openapi.yaml](openapi.yaml)
   - Reference: [SCHEMAS.md](SCHEMAS.md)

2. **Frontend implementation?**
   - Read: [API.md](API.md) - WebSocket section
   - Reference: [QUICK_START.md](QUICK_START.md) - WebSocket examples

3. **Integration development?**
   - Read: [API.md](API.md) - Integration Points section
   - Reference: [SCHEMAS.md](SCHEMAS.md)

---

## Getting Started

### 1. Health Check

Verify the API is running:

```bash
curl http://localhost:8000/api/v1/health
```

### 2. Create a Project

**Discovery Mode** (AI generates specifications):

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-app",
    "project_overview": "A collaborative task management application for teams",
    "project_type_hint": "web-app"
  }'
```

**Direct Mode** (you specify everything):

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-api",
    "project_path": "/home/user/projects/",
    "project_type": "api",
    "language_stack": "python",
    "framework": "fastapi"
  }'
```

### 3. Monitor Progress

Connect to WebSocket for real-time updates:

```javascript
const projectId = 'proj_abc123xyz'; // From create response
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/projects/${projectId}`);

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(`[${msg.type}] ${msg.message || msg.phase}`);
};
```

### 4. Approve Generated Design

When you receive `approval_required` event:

```bash
curl -X POST http://localhost:8000/api/v1/projects/proj_abc123xyz/approve \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Looks good, proceed"}'
```

### 5. Get Results

After workflow completes:

```bash
curl http://localhost:8000/api/v1/projects/proj_abc123xyz
```

---

## API Concepts

### Project Workflow Phases

```
┌─────────────┐
│    Input    │  Specification received
└──────┬──────┘
       ↓
┌─────────────┐
│  Designing  │  Product & architecture design (requires approval)
└──────┬──────┘
       ↓
┌─────────────┐
│ Executing   │  Project scaffolding and provisioning
└──────┬──────┘
       ↓
┌─────────────┐
│ Completed   │  Ready for development
└─────────────┘
```

### Project Statuses

| Status | Phase | Description |
|--------|-------|-------------|
| `pending` | Input | Awaiting processing |
| `input_received` | Input | Specification received |
| `designing` | Designing | Design phase in progress |
| `awaiting_approval` | Designing | Awaiting user approval |
| `executing` | Executing | Execution in progress |
| `completed` | Completed | Project created successfully |
| `failed` | Any | Execution failed |
| `cancelled` | Any | User cancelled project |

---

## Endpoint Summary

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/projects` | Create new project |
| GET | `/projects` | List all projects |
| GET | `/projects/{id}` | Get project details |
| DELETE | `/projects/{id}` | Cancel project |
| GET | `/projects/{id}/progress` | Get progress |
| POST | `/projects/{id}/approve` | Approve phase |
| POST | `/projects/{id}/reject` | Reject phase |
| POST | `/projects/validate` | Validate spec |

### Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/templates` | List templates |
| GET | `/templates/{id}` | Get template details |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| WS | `/ws/projects/{id}` | Real-time project updates |

---

## Authentication

Currently optional but prepared for JWT Bearer token integration.

### Future Implementation

```bash
curl -X GET http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <your-jwt-token>"
```

---

## Error Handling

All errors follow a standard format:

```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "request_id": "req_xyz789"
}
```

### Common Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (delete successful) |
| 400 | Bad Request |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |

See [API.md](API.md#error-handling) for detailed error handling documentation.

---

## Request/Response Examples

### Create Project (Discovery Mode)

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "task-manager",
    "project_overview": "A collaborative task management application for small teams..."
  }'
```

**Response (201 Created):**
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

### Get Project Details

**Request:**
```bash
curl http://localhost:8000/api/v1/projects/proj_abc123xyz
```

**Response (200 OK):**
```json
{
  "id": "proj_abc123xyz",
  "status": "awaiting_approval",
  "mode": "discovery",
  "current_phase": "designing",
  "project_name": "task-manager",
  "product_design": {
    "vision": "...",
    "goals": [...],
    "epics": [...]
  },
  "architecture_design": {
    "tech_stack": {...},
    "system_components": [...],
    ...
  }
}
```

### WebSocket Message

**Connected Event:**
```json
{
  "type": "connected",
  "timestamp": "2024-01-14T10:30:00Z",
  "project_id": "proj_123",
  "message": "Connected to project updates"
}
```

**Approval Required Event:**
```json
{
  "type": "approval_required",
  "timestamp": "2024-01-14T10:33:00Z",
  "project_id": "proj_123",
  "phase": "designing",
  "artifact_type": "product_design",
  "artifact_preview": {
    "vision": "...",
    "epics": 5,
    "user_stories": 23
  }
}
```

---

## Integration Examples

### Python

```python
import requests
import json

# Create project
response = requests.post(
    'http://localhost:8000/api/v1/projects',
    json={
        'project_name': 'my-app',
        'project_overview': 'Description...',
        'project_type_hint': 'web-app'
    }
)
project = response.json()
print(f"Project ID: {project['id']}")

# Get project details
response = requests.get(
    f"http://localhost:8000/api/v1/projects/{project['id']}"
)
project_detail = response.json()
print(f"Status: {project_detail['status']}")
```

### JavaScript

```javascript
// Create project
const response = await fetch('http://localhost:8000/api/v1/projects', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    project_name: 'my-app',
    project_overview: 'Description...',
    project_type_hint: 'web-app'
  })
});
const project = await response.json();
console.log(`Project ID: ${project.id}`);

// Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/projects/${project.id}`);
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(`[${msg.type}] ${msg.message || msg.phase}`);
};
```

### cURL

```bash
# Create project
PROJECT=$(curl -s -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-app",
    "project_overview": "Description..."
  }' | jq -r '.id')

echo "Project ID: $PROJECT"

# Get details
curl http://localhost:8000/api/v1/projects/$PROJECT | jq '.'
```

---

## Tools and Resources

### API Testing Tools

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **Postman**: Import `openapi.yaml`
- **cURL**: Command-line HTTP client
- **httpie**: User-friendly HTTP client

### WebSocket Tools

- **wscat** (Node.js): `npm install -g wscat && wscat -c ws://...`
- **websocat** (Rust): `websocat ws://...`
- **Browser Console**: Use WebSocket API

### JSON Tools

- **jq**: JSON parsing and formatting
- **Visual Studio Code**: JSON validation and schema support

---

## Support

### Documentation Navigation

- **Quick answers**: [QUICK_START.md](QUICK_START.md)
- **Complete guide**: [API.md](API.md)
- **Schema details**: [SCHEMAS.md](SCHEMAS.md)
- **Machine-readable**: [openapi.yaml](openapi.yaml)

### Getting Help

- **Email**: dev-team@bootstrap.local
- **Slack**: #project-bootstrap-api
- **Issues**: GitHub repository issues

---

## Related Documentation

- **Project Overview**: `docs/specs/project-overview.txt`
- **Architecture**: `docs/specs/architecture-diag.txt`
- **Orchestration**: `docs/specs/agent-orchestration.yml`
- **Workflow Sequence**: `docs/specs/mermaid-seq-diag.txt`

---

## Version Information

| Component | Version |
|-----------|---------|
| API Spec | OpenAPI 3.0.3 |
| API Version | v1 |
| Release | 1.0.0 |
| Last Updated | 2024-01-14 |

---

## File Structure

```
docs/api/
├── README.md                 # This file - Documentation index
├── openapi.yaml             # OpenAPI 3.0 specification
├── API.md                   # Complete API documentation
├── QUICK_START.md          # Quick reference guide
└── SCHEMAS.md              # Detailed schema reference
```

---

## Quick Navigation

- [OpenAPI Specification](openapi.yaml)
- [Complete API Documentation](API.md)
- [Quick Reference](QUICK_START.md)
- [Schema Reference](SCHEMAS.md)

---

Last Updated: 2024-01-14
Maintained by: Project Bootstrap Team
