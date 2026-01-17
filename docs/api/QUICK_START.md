# API Quick Start Guide

Fast reference guide for the Project Bootstrap API endpoints and common use cases.

## Base URL

```
http://localhost:8000/api/v1
```

## Health Check

```bash
curl http://localhost:8000/api/v1/health
```

## Project Creation

### Discovery Mode (AI-Generated Specs)

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "task-manager",
    "project_overview": "A collaborative task management application for teams",
    "target_users": "Small to medium teams",
    "key_features": "Real-time collaboration, task dependencies, team messaging",
    "project_type_hint": "web-app"
  }'
```

### Direct Mode (Exact Specs)

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

## Project Management

### List All Projects

```bash
curl http://localhost:8000/api/v1/projects
```

### List Completed Projects Only

```bash
curl "http://localhost:8000/api/v1/projects?status=completed"
```

### Get Project Details

```bash
curl http://localhost:8000/api/v1/projects/{project_id}
```

### Get Project Progress

```bash
curl http://localhost:8000/api/v1/projects/{project_id}/progress
```

### Validate Specification

```bash
curl -X POST http://localhost:8000/api/v1/projects/validate \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-api",
    "project_path": "/home/user/projects/",
    "project_type": "api",
    "language_stack": "python"
  }'
```

## Approval Gates

### Approve Phase

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/approve \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Looks good, proceed with execution"
  }'
```

### Reject Phase with Feedback

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/reject \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": "Please revise the architecture to include better error handling",
    "specific_issues": [
      "No circuit breaker pattern",
      "Missing retry logic"
    ]
  }'
```

## Project Cancellation

```bash
curl -X DELETE http://localhost:8000/api/v1/projects/{project_id}
```

## Templates

### List All Templates

```bash
curl http://localhost:8000/api/v1/templates
```

### Filter Templates by Project Type

```bash
curl "http://localhost:8000/api/v1/templates?project_type=api"
```

### Filter by Language

```bash
curl "http://localhost:8000/api/v1/templates?language_stack=python"
```

### Get Template Details

```bash
curl http://localhost:8000/api/v1/templates/{template_id}
```

## WebSocket Real-time Updates

### JavaScript/Browser

```javascript
const projectId = 'proj_abc123xyz';
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/projects/${projectId}`);

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  console.log(`[${msg.type}] ${msg.message || msg.phase}`);
};
ws.onerror = (error) => console.error('Error:', error);
ws.onclose = () => console.log('Disconnected');
```

### Python

```python
import asyncio
import json
import websockets

async def watch_project(project_id):
    uri = f"ws://localhost:8000/api/v1/ws/projects/{project_id}"
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"[{data['type']}] {data.get('message', data.get('phase', ''))}")

asyncio.run(watch_project('proj_abc123xyz'))
```

### cURL (websocketcat)

```bash
wcat ws://localhost:8000/api/v1/ws/projects/{project_id}
```

## Common Query Parameters

### Pagination

```bash
# List with pagination
curl "http://localhost:8000/api/v1/projects?limit=10&offset=20"

# Parameters:
# - limit: 1-100 (default: 20)
# - offset: 0+ (default: 0)
```

### Status Filtering

```bash
# Valid status values:
# pending, input_received, designing, awaiting_approval,
# executing, completed, failed, cancelled

curl "http://localhost:8000/api/v1/projects?status=awaiting_approval"
```

## Project Types

```
web-app       # Web application (frontend + backend)
api           # REST/GraphQL API
library       # Reusable library
cli           # Command-line tool
monorepo      # Monorepo with multiple packages
ml-project    # Machine learning project
ai-app        # AI/LLM application
full-platform # Complete platform with multiple services
```

## Language Stacks

```
python   # Python
node     # Node.js/TypeScript
java     # Java
go       # Go
rust     # Rust
dotnet   # .NET Core/C#
multi    # Multiple languages
```

## CI/CD Providers

```
github-actions     # GitHub Actions
gitlab-ci          # GitLab CI/CD
azure-pipelines    # Azure Pipelines
```

## VCS Providers

```
github     # GitHub
gitlab     # GitLab
bitbucket  # Bitbucket
```

## Response Status Codes

```
200   Success
201   Created
204   No Content (delete successful)
400   Bad Request
404   Not Found
422   Validation Error
500   Server Error
```

## Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable message",
  "request_id": "req_xyz789"
}
```

## Project Workflow States

```
pending              → Input awaiting processing
    ↓
input_received       → Specification received
    ↓
designing            → Design phase in progress
    ↓
awaiting_approval    → Awaiting user approval
    ↓
executing            → Execution phase
    ↓
completed            → Project ready

(Alternative paths)
designing     ← rejected phase
failed        ← error during any phase
cancelled     ← user cancelled
```

## Example: Complete Workflow

```bash
# 1. Create project in Discovery mode
PROJECT=$(curl -s -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "project_name": "my-app",
    "project_overview": "My awesome application"
  }' | jq -r '.id')

echo "Project ID: $PROJECT"

# 2. Connect to WebSocket for real-time updates
# (in another terminal)
wcat ws://localhost:8000/api/v1/ws/projects/$PROJECT

# 3. Get project details
curl http://localhost:8000/api/v1/projects/$PROJECT

# 4. Wait for approval_required event on WebSocket...

# 5. Approve phase
curl -X POST http://localhost:8000/api/v1/projects/$PROJECT/approve \
  -H "Content-Type: application/json" \
  -d '{"feedback": "Looks good"}'

# 6. Wait for workflow_completed event on WebSocket...

# 7. Get final project details
curl http://localhost:8000/api/v1/projects/$PROJECT
```

## Useful Tools

### jq - JSON Parsing

```bash
# Extract project ID
curl ... | jq -r '.id'

# Format response
curl ... | jq '.'

# Filter array
curl ... | jq '.projects[] | select(.status=="completed")'
```

### httpie - Better cURL

```bash
# Installation
pip install httpie

# Usage
http POST localhost:8000/api/v1/projects \
  project_name=my-app \
  project_overview="Description here"
```

### WebSocket Tools

```bash
# websocat (Rust)
websocat ws://localhost:8000/api/v1/ws/projects/proj_123

# wscat (Node.js)
npm install -g wscat
wscat -c ws://localhost:8000/api/v1/ws/projects/proj_123

# webcat
wcat ws://localhost:8000/api/v1/ws/projects/proj_123
```

## API Documentation Links

- **OpenAPI Spec**: `/docs/api/openapi.yaml`
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **Full API Docs**: `docs/api/API.md`

## Common Errors and Solutions

### 400 Bad Request
Check that all required fields are present and valid according to schema.

### 404 Not Found
Verify the project ID is correct with `GET /projects`.

### 422 Validation Error
Check the `details` field in error response for specific field issues.

### Timeout during project creation
Discovery mode can take several minutes. Monitor progress via WebSocket.

### WebSocket connection refused
Ensure the project ID exists and the WebSocket connection is to the correct URL.

---

For detailed documentation, see `docs/api/API.md`
