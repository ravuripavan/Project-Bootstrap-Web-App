# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Project Bootstrap Web App** - a multi-agent orchestration system designed to automate project scaffolding and setup. The system coordinates specialized agents to create new software projects with integrated tooling for Git, CI/CD, and Jira.

**Current Status:** Specification/Design phase - architecture and orchestration specs are defined, but no source code implementations exist yet.

## Architecture

The system uses a 6-layer architecture:

```
Web App UI
    ↓
Web App Backend (normalizes inputs)
    ↓
Orchestration Engine (core coordinator)
    ↓
Agent Layer (9 specialized agents)
    ↓
Integration Layer (Jira API, GitHub/GitLab API, CI/CD providers)
    ↓
Local System / Filesystem
```

### Agent Workflow

Execution happens in 4 phases with dependency graph ordering:

1. **Phase 1 - Collection & Validation:** ProjectSpecCollectorAgent → SpecValidatorAgent
2. **Phase 2 - Template Resolution:** TemplateSelectorAgent → PlanBuilderAgent
3. **Phase 3 - Execution:** FilesystemScaffolderAgent → GitRepoProvisionerAgent → WorkflowGeneratorAgent / JiraSpaceProvisionerAgent (parallel, conditional)
4. **Phase 4 - Summary:** SummaryReporterAgent

The `OrchestrationAgent` coordinates all agents and manages execution order.

### Agent I/O Contract

Each agent receives:
- `project_spec`: ProjectSpec object
- `plan_step`: Current orchestration step
- `context`: Execution context with prior results

Each agent returns:
- `status`: success | failure | warning
- `output`: Agent-specific result data
- `errors`: Error messages (if applicable)

## Project Structure

```
Project-Bootstrap-Web-App/
├── docs/                           # Documentation
│   ├── specs/                      # Specification documents
│   │   ├── agent-orchestration.yml # Primary orchestration config
│   │   ├── architecture-diag.txt   # ASCII architecture diagrams
│   │   ├── mermaid-seq-diag.txt    # Mermaid sequence diagram
│   │   └── project-overview.txt    # High-level architecture overview
│   ├── design/                     # Product design documents
│   └── api/                        # API documentation
├── src/                            # Source code
│   ├── web/                        # Web Application
│   │   ├── frontend/               # Web UI (React/Vue/etc.)
│   │   └── backend/                # Web Backend API
│   ├── orchestrator/               # Orchestration Engine
│   ├── agents/                     # Agent implementations
│   └── integrations/               # Integration Layer (Jira, GitHub, CI)
├── config/                         # Configuration files
├── tests/                          # Test suites
├── templates/                      # Project scaffold templates
├── .claude/                        # Claude Code agent definitions
│   └── agents/                     # Custom agent prompts
└── CLAUDE.md                       # Project instructions
```

## Key Files

| File | Purpose |
|------|---------|
| `docs/specs/agent-orchestration.yml` | Primary orchestration configuration - defines schemas, agents, and workflow phases |
| `docs/specs/project-overview.txt` | High-level architecture and CLI command mapping |
| `docs/specs/architecture-diag.txt` | ASCII architecture diagrams with layer-by-layer explanation |
| `docs/specs/mermaid-seq-diag.txt` | Sequence diagram (Mermaid format) showing complete agent flow |

## OrchestrationSpec Schema

Required fields:
- `project_name`, `project_path`, `project_type`, `language_stack`
- `include_repo`, `include_ci`, `include_jira` (booleans)

Optional fields:
- `ci_provider` (e.g., "github-actions", "gitlab-ci")
- `vcs_provider` (e.g., "github", "gitlab")
- `jira_config` (object with key_prefix, project_type)

## CLI Commands (Planned)

```bash
bootstrap init       # Phases 1-2: Collect, validate, select templates, build plan
bootstrap plan       # Same as init, outputs plan only (no execution)
bootstrap apply      # All phases (1-4): Full execution
bootstrap validate   # Phase 1 only: Spec validation
bootstrap dry-run    # All phases but no side effects
```

## Integration Points

- **Jira REST API:** Project creation, epics/issues setup
- **GitHub/GitLab API:** Remote repository creation and configuration
- **CI/CD Providers:** GitHub Actions, GitLab CI workflow generation
- **Local Filesystem:** Directory scaffolding, Git initialization

## Custom Agents

Custom Claude Code agents are defined in `.claude/agents/`. Invoke with `/agent:<name>`.

### Core Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `orchestration` | sonnet | Master coordinator - delegates to specialized agents, manages workflow |
| `requirement` | sonnet | Requirements analyst - gathers specs, creates user stories |
| `po` | sonnet | Product Owner - manages backlog, acceptance criteria |

### Architect Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `architecture` | opus | General software architect - designs system architecture, ADRs |
| `fullstack-architect` | opus | End-to-end system design, tech stack selection |
| `backend-architect` | opus | API design, microservices, database architecture |
| `frontend-architect` | sonnet | UI architecture, component structure, state management |
| `database-architect` | opus | Data modeling, storage selection, optimization |
| `infrastructure-architect` | sonnet | Cloud architecture, DevOps, IaC |
| `security-architect` | opus | Auth, compliance, threat modeling |
| `ml-architect` | opus | ML pipelines, model architecture, MLOps |
| `ai-architect` | opus | LLM integration, RAG systems, AI agents |

### Developer Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `developer` | sonnet | General senior developer - generates production-ready code |
| `fullstack-developer` | sonnet | End-to-end feature implementation |
| `backend-developer` | sonnet | API implementation, services, database operations |
| `frontend-developer` | sonnet | UI components, state management, testing |
| `aiml-developer` | sonnet | ML models, training pipelines, LLM integration |

### Support Agents

| Agent | Model | Purpose |
|-------|-------|---------|
| `testing` | sonnet | QA engineer - creates test suites, identifies edge cases |
| `cicd` | haiku | DevOps engineer - generates CI/CD pipelines |
| `documentation` | haiku | Technical writer - README, API docs, architecture docs |
| `expert` | sonnet | General domain expert - tech stack guidance |

### Domain Expert Agents

Domain experts are activated dynamically based on project keywords.

| Agent | Model | Purpose |
|-------|-------|---------|
| `healthcare-expert` | opus | HIPAA compliance, HL7/FHIR, medical systems |
| `finance-expert` | opus | PCI-DSS, SOX compliance, payment systems |
| `ecommerce-expert` | sonnet | Payment integration, inventory, marketplace |
| `edtech-expert` | sonnet | LMS, FERPA compliance, accessibility |
| `iot-expert` | sonnet | MQTT, edge computing, device security |
| `gaming-expert` | sonnet | Game loops, multiplayer, anti-cheat |
| `social-expert` | sonnet | Content moderation, social graphs, feeds |
| `legaltech-expert` | opus | E-signature, document management, compliance |
| `logistics-expert` | sonnet | Route optimization, tracking, supply chain |
| `hrtech-expert` | sonnet | Payroll, PII handling, HR compliance |

### Agent Workflow

The orchestration agent coordinates the bootstrap process in phases:

1. **Discovery Phase**
   - `po` → Product design from user overview (vision, personas, high-level epics, MVP scope)
   - User approval of product design

2. **Requirements & Architecture Phase** (PARALLEL EXECUTION)
   - `requirement` → Detailed requirements generation:
     - Detailed epics with story points
     - User stories (INVEST format)
     - Acceptance criteria (Given/When/Then)
     - Non-functional requirements
     - Sprint plan recommendations
     - Story dependency graph
   - Architect agents (selected based on project type) → System design:
     - Architecture diagrams
     - Technology stack recommendation
     - Component breakdown
   - Domain expert agents (activated based on keywords) → Compliance guidance
   - User approval of combined architecture + requirements

3. **Implementation Phase** (parallel)
   - `developer` agents → Code generation
   - `testing` → Test suites
   - `cicd` → CI/CD pipelines

4. **Documentation Phase**
   - `documentation` → README, API docs
   - `po` → Finalized backlog with all user stories

### Usage Examples
```bash
# Full project bootstrap
/agent:orchestration "Bootstrap a FastAPI project with PostgreSQL"

# Product design
/agent:po "Design product for a task management application"

# Requirements generation (after PO approval)
/agent:requirement "Generate epics and user stories for the task management app"

# Architecture design
/agent:fullstack-architect "Design a real-time collaboration platform"
/agent:backend-architect "Design microservices for e-commerce"

# Development
/agent:backend-developer "Implement user authentication with JWT"
/agent:frontend-developer "Create dashboard with data visualization"

# Testing & DevOps
/agent:testing "Write tests for the auth module"
/agent:cicd "Create GitHub Actions workflow for Python"

# Domain expertise
/agent:healthcare-expert "Review HIPAA compliance for patient portal"
/agent:finance-expert "Implement PCI-DSS compliant payment flow"
```
