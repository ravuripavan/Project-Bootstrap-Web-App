# API Schemas Reference

Complete reference for all request and response schemas used by the Project Bootstrap API.

## Schema Organization

Schemas are organized by category:

1. **Input Schemas** - Request bodies for creating projects
2. **Response Schemas** - API responses
3. **Nested Schemas** - Reusable components within larger schemas
4. **Error Schemas** - Error response formats
5. **WebSocket Schemas** - Real-time message types

## Input Schemas

### ProjectOverviewCreate (Discovery Mode)

High-level project description for AI-driven specification generation.

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

**Field Definitions:**

| Field | Type | Required | Length | Pattern | Description |
|-------|------|----------|--------|---------|-------------|
| `project_name` | string | Yes | 2-64 | `^[a-zA-Z][a-zA-Z0-9-_]*$` | Project name, starts with letter |
| `project_overview` | string | Yes | 100-5000 | - | Detailed project description |
| `target_users` | string | No | 0-1000 | - | Target user personas |
| `key_features` | string | No | 0-2000 | - | Key features to implement |
| `constraints` | string | No | 0-1000 | - | Project constraints and requirements |
| `similar_products` | string | No | 0-500 | - | Similar products for reference |
| `project_type_hint` | enum | No | - | - | Hint for project type selection |

**project_type_hint values:**
```
web-app, api, library, cli, monorepo, ml-project, ai-app, full-platform
```

---

### ProjectSpecCreate (Direct Mode)

Complete technical specification for direct project creation.

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

**Field Definitions:**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `project_name` | string | Yes | - | Project name (lowercase alphanumeric + hyphens) |
| `project_path` | string | Yes | - | Local filesystem path for project root |
| `project_type` | enum | Yes | - | Type of project to scaffold |
| `language_stack` | enum | Yes | - | Primary programming language |
| `framework` | string | No | - | Framework (e.g., fastapi, django, express) |
| `include_repo` | boolean | No | true | Initialize Git repository locally |
| `include_ci` | boolean | No | true | Generate CI/CD pipeline configuration |
| `include_jira` | boolean | No | false | Create Jira project and populate issues |
| `ci_provider` | enum | No | github-actions | CI/CD provider to use |
| `vcs_provider` | enum | No | github | Version control service provider |
| `vcs_config` | object | No | - | VCS configuration (see below) |
| `jira_config` | object | No | - | Jira configuration (required if include_jira=true) |

**project_type values:**
```
web-app          # Web application with frontend and backend
api              # REST/GraphQL API service
library          # Reusable code library/package
cli              # Command-line tool
monorepo         # Monorepo with multiple packages
ml-project       # Machine learning project
ai-app           # AI/LLM application
full-platform    # Complete platform with multiple services
```

**language_stack values:**
```
python    # Python 3.x
node      # Node.js/TypeScript
java      # Java
go        # Go
rust      # Rust
dotnet    # .NET Core/C#
multi     # Multiple languages
```

**ci_provider values:**
```
github-actions       # GitHub Actions
gitlab-ci            # GitLab CI/CD
azure-pipelines      # Azure Pipelines
```

**vcs_provider values:**
```
github      # GitHub
gitlab      # GitLab
bitbucket   # Bitbucket
```

---

### VCSConfig (Nested)

Version control and Git repository configuration.

```json
{
  "visibility": "private",
  "create_remote": true,
  "default_branch": "main"
}
```

**Field Definitions:**

| Field | Type | Default | Enum | Description |
|-------|------|---------|------|-------------|
| `visibility` | string | private | public, private | Repository visibility |
| `create_remote` | boolean | true | - | Create remote repository on VCS provider |
| `default_branch` | string | main | - | Default branch name |

---

### JiraConfig (Nested)

Jira project creation configuration.

```json
{
  "key_prefix": "PROJ",
  "project_type": "scrum"
}
```

**Field Definitions:**

| Field | Type | Required | Length | Pattern | Description |
|-------|------|----------|--------|---------|-------------|
| `key_prefix` | string | Yes | 2-10 | `^[A-Z]+$` | Jira project key (uppercase letters only) |
| `project_type` | enum | No | - | - | Jira project template type |

**project_type values:**
```
scrum       # Scrum project (default)
kanban      # Kanban project
basic       # Basic project
```

---

### ApprovalRequest (Nested)

Request to approve a workflow phase.

```json
{
  "feedback": "Looks good, proceed with execution",
  "modifications": null
}
```

**Field Definitions:**

| Field | Type | Required | Length | Description |
|-------|------|----------|--------|-------------|
| `feedback` | string | No | 0-2000 | Optional feedback on artifacts |
| `modifications` | object | No | - | Optional modifications to apply |

---

### RejectionRequest (Nested)

Request to reject a workflow phase.

```json
{
  "feedback": "The architecture doesn't align with our security requirements. Please revise.",
  "specific_issues": [
    "No end-to-end encryption mentioned",
    "HIPAA compliance not addressed"
  ]
}
```

**Field Definitions:**

| Field | Type | Required | Length | Description |
|-------|------|----------|--------|-------------|
| `feedback` | string | Yes | 10-2000 | Explanation of rejection |
| `specific_issues` | array[string] | No | - | List of specific issues to address |

---

## Response Schemas

### ProjectResponse

Basic project information and current state.

```json
{
  "id": "proj_abc123xyz",
  "status": "designing",
  "mode": "discovery",
  "current_phase": "designing",
  "project_name": "task-manager",
  "created_at": "2024-01-14T10:30:00Z",
  "updated_at": "2024-01-14T10:35:00Z",
  "completed_at": null
}
```

**Field Definitions:**

| Field | Type | Format | Example | Description |
|-------|------|--------|---------|-------------|
| `id` | string | - | proj_abc123xyz | Unique project identifier |
| `status` | enum | - | designing | Current project status |
| `mode` | enum | - | discovery | Workflow mode (discovery or direct) |
| `current_phase` | string | - | designing | Current workflow phase name |
| `project_name` | string | - | task-manager | Project name |
| `created_at` | string | date-time | 2024-01-14T10:30:00Z | Creation timestamp (ISO 8601) |
| `updated_at` | string | date-time | 2024-01-14T10:35:00Z | Last update timestamp (ISO 8601) |
| `completed_at` | string | date-time | null | Completion timestamp (if completed) |

**status values:**
```
pending              # Initial state, awaiting processing
input_received       # Specification received
designing            # Design phase in progress
awaiting_approval    # Awaiting user approval
executing            # Execution phase in progress
completed            # Project creation complete
failed               # Execution failed with error
cancelled            # Project cancelled by user
```

**mode values:**
```
discovery    # User provides overview, system generates specs
direct       # User provides complete specification
```

---

### ProjectDetailResponse

Extended project response with all artifacts and design outputs.

Extends `ProjectResponse` with:

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
  "project_spec": {
    "project_type": "web-app",
    "language_stack": "python"
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
    "tech_stack": {...},
    "system_components": [...],
    "data_model": {...},
    "api_design": {...},
    "security": {...},
    "infrastructure": {...}
  },
  "execution_progress": {
    "current_phase": "designing"
  }
}
```

**Additional Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `project_overview` | object | Original project overview input (Discovery mode) |
| `project_spec` | object | Technical specification |
| `product_design` | object | Generated product design (see ProductDesign schema) |
| `architecture_design` | object | Generated architecture (see ArchitectureDesign schema) |
| `execution_progress` | object | Execution phase progress details |

---

### ProductDesign

Product design output from PO and design agents.

```json
{
  "vision": "Collaborative task management platform for teams",
  "goals": [
    "Enable effective team collaboration on tasks",
    "Improve project visibility and productivity",
    "Reduce communication overhead"
  ],
  "personas": [
    {
      "name": "Project Manager",
      "description": "Manages team and project",
      "goals": ["Track progress", "Identify blockers"],
      "pain_points": ["Too many communication channels", "Unclear task status"]
    },
    {
      "name": "Team Member",
      "description": "Executes assigned tasks",
      "goals": ["Know what to work on", "Update team on progress"],
      "pain_points": ["Email overload", "Context switching"]
    }
  ],
  "epics": [
    {
      "id": "EPIC-001",
      "name": "User Authentication",
      "description": "User login and account management",
      "story_points": 13,
      "priority": "P0"
    },
    {
      "id": "EPIC-002",
      "name": "Task Management",
      "description": "Create, assign, and track tasks",
      "story_points": 21,
      "priority": "P0"
    }
  ],
  "mvp_scope": {
    "must_have": ["User auth", "Task CRUD", "Team collaboration"],
    "should_have": ["Real-time updates", "File attachments"],
    "could_have": ["Advanced analytics", "Integrations"],
    "wont_have": ["AI recommendations", "Mobile native app"]
  },
  "risks": [
    {
      "risk": "Real-time sync complexity",
      "probability": "medium",
      "impact": "high",
      "mitigation": "Use WebSocket and event sourcing"
    }
  ],
  "success_metrics": [
    {
      "metric": "User adoption",
      "target": "1000 users in first month",
      "measurement": "Active user count"
    }
  ]
}
```

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `vision` | string | Project vision statement |
| `goals` | array[string] | Strategic goals |
| `personas` | array[object] | Target user personas with characteristics |
| `epics` | array[object] | Product epics with stories and story points |
| `mvp_scope` | object | MVP scope (must, should, could, won't haves) |
| `risks` | array[object] | Identified risks with mitigation strategies |
| `success_metrics` | array[object] | Success metrics and KPIs |

---

### ArchitectureDesign

System architecture output from architect agents.

```json
{
  "tech_stack": {
    "backend": "FastAPI + Python 3.11",
    "frontend": "React 18 + TypeScript",
    "database": "PostgreSQL 15",
    "cache": "Redis",
    "messaging": "RabbitMQ",
    "infrastructure": "AWS (ECS, RDS, ElastiCache)"
  },
  "system_components": [
    {
      "name": "API Gateway",
      "description": "FastAPI REST API",
      "technology": "FastAPI",
      "responsibilities": ["Request routing", "Authentication", "Rate limiting"]
    },
    {
      "name": "Task Service",
      "description": "Task management microservice",
      "technology": "FastAPI",
      "responsibilities": ["Task CRUD", "Task state management", "Task history"]
    }
  ],
  "data_model": {
    "entities": [
      {
        "name": "User",
        "fields": [
          {"name": "id", "type": "UUID", "primary": true},
          {"name": "email", "type": "String", "unique": true},
          {"name": "created_at", "type": "DateTime"}
        ]
      },
      {
        "name": "Task",
        "fields": [
          {"name": "id", "type": "UUID", "primary": true},
          {"name": "title", "type": "String"},
          {"name": "status", "type": "Enum", "values": ["pending", "in_progress", "completed"]}
        ]
      }
    ]
  },
  "api_design": {
    "version": "1.0.0",
    "base_path": "/api/v1",
    "endpoints": [
      {
        "path": "/tasks",
        "methods": ["GET", "POST"],
        "authentication": "JWT",
        "rate_limit": "1000/hour"
      }
    ]
  },
  "security": {
    "authentication": "JWT with 24h expiry",
    "authorization": "Role-based access control (RBAC)",
    "encryption": "TLS 1.3 for transport, AES-256 for sensitive data",
    "data_protection": "Personal data encrypted at rest",
    "compliance": ["GDPR", "SOC2"]
  },
  "infrastructure": {
    "deployment": "Kubernetes on AWS EKS",
    "scaling": "Horizontal pod autoscaling",
    "monitoring": "Prometheus + Grafana",
    "logging": "ELK Stack",
    "disaster_recovery": "Multi-region failover"
  },
  "domain_considerations": [
    {
      "domain": "Healthcare",
      "requirement": "HIPAA compliance",
      "implementation": "Data encryption, audit logging, access controls"
    }
  ]
}
```

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `tech_stack` | object | Technology recommendations by layer |
| `system_components` | array[object] | System components and their responsibilities |
| `data_model` | object | Entity-relationship model and database schema |
| `api_design` | object | API design specifications and endpoints |
| `security` | object | Security architecture and requirements |
| `infrastructure` | object | Infrastructure and deployment architecture |
| `domain_considerations` | array[object] | Domain-specific compliance and best practices |

---

### ProjectListResponse

Paginated list of projects.

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
    },
    {
      "id": "proj_def456uvw",
      "status": "awaiting_approval",
      "mode": "discovery",
      "current_phase": "designing",
      "project_name": "chat-app",
      "created_at": "2024-01-14T10:25:00Z",
      "updated_at": "2024-01-14T10:35:00Z",
      "completed_at": null
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `projects` | array[ProjectResponse] | List of projects |
| `total` | integer | Total number of projects |
| `limit` | integer | Pagination limit used |
| `offset` | integer | Pagination offset used |

---

### WorkflowProgress

Current workflow progress information.

```json
{
  "project_id": "proj_abc123xyz",
  "status": "awaiting_approval",
  "mode": "discovery",
  "current_phase": "designing",
  "activated_experts": [
    "healthcare-expert",
    "security-expert"
  ],
  "has_product_design": true,
  "has_architecture": true
}
```

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | string | Project identifier |
| `status` | string | Current project status |
| `mode` | string | Workflow mode |
| `current_phase` | string | Current phase name |
| `activated_experts` | array[string] | List of activated domain experts |
| `has_product_design` | boolean | Whether product design has been generated |
| `has_architecture` | boolean | Whether architecture design has been generated |

---

### ValidationResult

Result of specification validation.

```json
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Jira integration enabled but no config provided"
  ]
}
```

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `valid` | boolean | Whether specification is valid |
| `errors` | array[string] | List of validation errors (blocking) |
| `warnings` | array[string] | List of validation warnings (non-blocking) |

---

## Error Schemas

### ErrorResponse

Standard error response for API errors.

```json
{
  "error": "not_found",
  "message": "Project proj_123 not found",
  "request_id": "req_abc123"
}
```

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `error` | string | Error code (machine-readable) |
| `message` | string | Human-readable error message |
| `request_id` | string | Request identifier for debugging/support |

**Common error codes:**

```
not_found              # Resource doesn't exist
invalid_state          # Operation not allowed in current state
invalid_input          # Invalid request parameters
validation_error       # One or more validation errors
internal_error         # Server-side error
unauthorized           # Authentication required/failed
forbidden              # Insufficient permissions
conflict               # Conflicting resource state
```

---

### ValidationErrorResponse

Detailed validation error response.

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
    },
    {
      "field": "jira_config",
      "message": "This field is required when include_jira is true",
      "code": "conditional_required"
    }
  ]
}
```

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `error` | string | Always "validation_error" |
| `message` | string | General validation failure message |
| `details` | array[object] | List of field validation errors |

**Detail fields:**

| Field | Type | Description |
|-------|------|-------------|
| `field` | string | Field name |
| `message` | string | Validation error message |
| `code` | string | Error code |

**Validation error codes:**

```
required                    # Field is required
type_mismatch              # Wrong data type
length_violation           # String too short/long
pattern_mismatch           # Doesn't match regex pattern
enum_violation             # Not in allowed enum values
min_violation              # Below minimum value
max_violation              # Above maximum value
conditional_required       # Required based on another field
dependency_violation       # Invalid combination with other fields
```

---

## WebSocket Message Schemas

All WebSocket messages include base fields:

```json
{
  "type": "message_type",
  "timestamp": "2024-01-14T10:30:00Z",
  "project_id": "proj_123"
}
```

### WSConnected

Connection established message.

```json
{
  "type": "connected",
  "timestamp": "2024-01-14T10:30:00Z",
  "project_id": "proj_123",
  "message": "Connected to project updates"
}
```

---

### WSPhaseStarted

Workflow phase started.

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

### WSPhaseCompleted

Workflow phase completed.

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

### WSAgentStarted

Agent execution started.

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

### WSAgentProgress

Agent execution progress.

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

### WSAgentCompleted

Agent execution completed.

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

### WSApprovalRequired

User approval required.

```json
{
  "type": "approval_required",
  "timestamp": "2024-01-14T10:33:00Z",
  "project_id": "proj_123",
  "phase": "designing",
  "artifact_type": "product_design",
  "artifact_preview": {
    "vision": "Collaborative task management...",
    "epics": 5,
    "user_stories": 23
  }
}
```

---

### WSWorkflowCompleted

Entire workflow completed.

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

### WSError

Error occurred.

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

### WSLog

Informational log message.

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

**level values:**

```
info      # Informational message
warning   # Warning message
error     # Error message
```

---

## Schema Relationships Diagram

```
ProjectResponse
├── ProjectDetailResponse (extends)
│   ├── ProductDesign
│   │   ├── Personas (array)
│   │   ├── Epics (array)
│   │   ├── Risks (array)
│   │   └── SuccessMetrics (array)
│   ├── ArchitectureDesign
│   │   ├── TechStack (object)
│   │   ├── SystemComponents (array)
│   │   ├── DataModel (object)
│   │   ├── ApiDesign (object)
│   │   ├── Security (object)
│   │   ├── Infrastructure (object)
│   │   └── DomainConsiderations (array)
│   └── ExecutionProgress (object)
├── ProjectListResponse
│   └── ProjectResponse (array)
└── WorkflowProgress

ProjectOverviewCreate (Request)
ProjectSpecCreate (Request)
├── VCSConfig
└── JiraConfig

ApprovalRequest (Request)
RejectionRequest (Request)

ErrorResponse
└── ValidationErrorResponse

ValidationResult

WebSocket Messages
├── WSConnected
├── WSPhaseStarted
├── WSPhaseCompleted
├── WSAgentStarted
├── WSAgentProgress
├── WSAgentCompleted
├── WSApprovalRequired
├── WSWorkflowCompleted
├── WSError
└── WSLog
```

---

## Enums Reference

### ProjectStatus

```
pending              # Initial state
input_received       # Specification received
designing            # Design phase
awaiting_approval    # Awaiting approval
executing            # Execution phase
completed            # Completed
failed               # Failed
cancelled            # Cancelled
```

### WorkflowMode

```
discovery    # AI-generated specifications
direct       # User-provided specifications
```

### ProjectType

```
web-app         # Web application
api             # API service
library         # Reusable library
cli             # Command-line tool
monorepo        # Monorepo
ml-project      # Machine learning
ai-app          # AI/LLM application
full-platform   # Full platform
```

### LanguageStack

```
python      # Python
node        # Node.js/TypeScript
java        # Java
go          # Go
rust        # Rust
dotnet      # .NET Core
multi       # Multiple languages
```

### CIProvider

```
github-actions       # GitHub Actions
gitlab-ci            # GitLab CI
azure-pipelines      # Azure Pipelines
```

### VCSProvider

```
github      # GitHub
gitlab      # GitLab
bitbucket   # Bitbucket
```

### RepositoryVisibility

```
public       # Public repository
private      # Private repository
```

### JiraProjectType

```
scrum        # Scrum project
kanban       # Kanban project
basic        # Basic project
```

### AgentStatus

```
pending      # Awaiting execution
running      # Currently running
completed    # Successfully completed
failed       # Failed with error
skipped      # Skipped
```

### PhaseStatus

```
pending              # Awaiting start
in_progress          # Currently executing
awaiting_approval    # Awaiting user approval
completed            # Successfully completed
failed               # Failed with error
```

---

Last Updated: 2024-01-14
