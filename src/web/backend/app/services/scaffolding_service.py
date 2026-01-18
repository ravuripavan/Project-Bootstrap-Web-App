"""
Scaffolding Service - Creates Claude Code CLI-ready projects.
Copies agent templates from templates/agents/ and customizes for each project.
"""
import os
import subprocess
import json
import shutil
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

logger = structlog.get_logger()

# Path to templates directory (relative to this file's location in the repo)
# scaffolding_service.py -> services -> app -> backend -> web -> src -> [project root]
TEMPLATES_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "templates"


class ScaffoldingService:
    """
    Creates Claude Code CLI-ready project scaffolding.
    Copies agents from templates/agents/, generates CLAUDE.md, docs/, tests/.
    """

    def __init__(self, base_output_dir: Optional[str] = None, templates_dir: Optional[str] = None):
        self.base_output_dir = Path(base_output_dir or os.path.expanduser("~/bootstrapped-projects"))
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir = Path(templates_dir) if templates_dir else TEMPLATES_DIR

    def validate_project_agents(self, project_path: str) -> Dict[str, Any]:
        """
        Public method to validate agents in an existing project.
        Can be called independently of scaffolding.

        Args:
            project_path: Path to the project directory

        Returns:
            Validation results with agent status, errors, and warnings
        """
        project_dir = Path(project_path)

        if not project_dir.exists():
            return {
                "valid": False,
                "error": f"Project path does not exist: {project_path}",
                "agents": [],
            }

        validation_results = self._validate_agents(project_dir)

        # Build list of available agents for CLI
        available_agents = []
        for agent in validation_results["agents"]:
            if agent["valid"]:
                available_agents.append({
                    "name": agent["name"],
                    "command": f"/agent:{agent['name']}",
                    "file": agent["file"],
                    "has_frontmatter": agent["has_frontmatter"],
                })

        return {
            "project_path": str(project_dir),
            "valid": validation_results["valid"],
            "summary": {
                "total_agents": validation_results["total_agents"],
                "valid_agents": validation_results["valid_agents"],
                "agents_with_errors": validation_results["agents_with_errors"],
                "agents_with_warnings": validation_results["agents_with_warnings"],
            },
            "available_agents": available_agents,
            "errors": validation_results["errors"],
            "warnings": validation_results["warnings"],
            "agent_details": validation_results["agents"],
        }

    def fix_project_agents(self, project_path: str) -> Dict[str, Any]:
        """
        Public method to fix common agent errors in an existing project.

        Args:
            project_path: Path to the project directory

        Returns:
            Fix results and updated validation status
        """
        project_dir = Path(project_path)

        if not project_dir.exists():
            return {
                "success": False,
                "error": f"Project path does not exist: {project_path}",
            }

        # First validate
        validation_results = self._validate_agents(project_dir)

        if validation_results["valid"]:
            return {
                "success": True,
                "message": "All agents are already valid, no fixes needed",
                "validation": self.validate_project_agents(project_path),
            }

        # Apply fixes
        fix_results = self._fix_agent_errors(project_dir, validation_results)

        # Re-validate
        new_validation = self.validate_project_agents(project_path)

        return {
            "success": new_validation["valid"],
            "fixes_applied": fix_results["fixed"],
            "fixes_failed": fix_results["failed"],
            "fix_details": fix_results["details"],
            "validation": new_validation,
        }

    async def scaffold_project(
        self,
        project_name: str,
        product_design: Dict[str, Any],
        architecture_design: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Main entry point - scaffolds a complete Claude Code CLI project."""
        logger.info("Starting Claude Code CLI project scaffolding", project_name=project_name)

        project_dir = self.base_output_dir / project_name

        # Clean up if exists (Windows requires special handling for .git)
        if project_dir.exists():
            def remove_readonly(func, path, exc_info):
                """Handle read-only files on Windows"""
                import stat
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(project_dir, onerror=remove_readonly)

        project_dir.mkdir(parents=True)

        created_files = []
        created_dirs = []

        # Extract info
        tech_stack = architecture_design.get("tech_stack", {})
        vision = product_design.get("vision", "")
        epics = product_design.get("epics", [])

        # 1. Create directory structure
        dirs = self._create_directory_structure(project_dir)
        created_dirs.extend(dirs)

        # 2. Generate .claude/agents/*.md (20+ agents)
        files = self._generate_claude_agents(project_dir, project_name, product_design, architecture_design)
        created_files.extend(files)

        # 3. Generate CLAUDE.md
        files = self._generate_claude_md(project_dir, project_name, product_design, architecture_design)
        created_files.extend(files)

        # 4. Generate workflow file
        files = self._generate_workflow(project_dir, project_name, product_design)
        created_files.extend(files)

        # 5. Generate docs structure
        files = self._generate_docs(project_dir, project_name, product_design, architecture_design)
        created_files.extend(files)

        # 6. Generate source code structure
        files = self._generate_source_structure(project_dir, project_name, tech_stack, architecture_design)
        created_files.extend(files)

        # 7. Generate tests structure
        files = self._generate_tests_structure(project_dir, project_name)
        created_files.extend(files)

        # 8. Generate configs
        files = self._generate_configs(project_dir, project_name, tech_stack)
        created_files.extend(files)

        # 9. Initialize git with branches (main, dev, test) and checkout to dev
        git_result = self._init_git(project_dir)

        # 10. Validate all agents and auto-fix errors
        logger.info("Validating agent files", project_name=project_name)
        validation_results = self._validate_agents(project_dir)

        # Auto-fix any errors found
        fix_results = None
        if not validation_results["valid"]:
            logger.warning(
                "Agent validation found errors, attempting auto-fix",
                errors=validation_results["agents_with_errors"]
            )
            fix_results = self._fix_agent_errors(project_dir, validation_results)

            # Re-validate after fixes
            validation_results = self._validate_agents(project_dir)
            if validation_results["valid"]:
                logger.info("All agent errors auto-fixed successfully")
            else:
                logger.error(
                    "Some agent errors could not be auto-fixed",
                    remaining_errors=validation_results["agents_with_errors"]
                )

        result = {
            "project_path": str(project_dir),
            "created_directories": len(created_dirs),
            "created_files": len(created_files),
            "files": created_files,
            "directories": created_dirs,
            "git": git_result,
            "claude_code_ready": validation_results["valid"],
            "agents_count": len([f for f in created_files if ".claude/agents/" in f]),
            "agent_validation": {
                "valid": validation_results["valid"],
                "total": validation_results["total_agents"],
                "valid_count": validation_results["valid_agents"],
                "errors_count": validation_results["agents_with_errors"],
                "warnings_count": validation_results["agents_with_warnings"],
                "errors": validation_results["errors"][:10],  # Limit to first 10
                "warnings": validation_results["warnings"][:10],  # Limit to first 10
            },
        }

        if fix_results:
            result["agent_fixes"] = fix_results

        logger.info(
            "Claude Code CLI project scaffolding complete",
            project_name=project_name,
            path=str(project_dir),
            files=len(created_files),
            agents=result["agents_count"],
            agents_valid=validation_results["valid"]
        )

        return result

    def _create_directory_structure(self, project_dir: Path) -> List[str]:
        """Create Claude Code CLI project directory structure."""
        dirs = [
            ".claude",
            ".claude/agents",
            "docs",
            "docs/specs",
            "docs/product",
            "docs/requirements",
            "docs/architecture",
            "docs/api",
            "docs/project-status",
            "src",
            "tests",
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            "config",
            ".github",
            ".github/workflows",
        ]

        created = []
        for d in dirs:
            path = project_dir / d
            path.mkdir(parents=True, exist_ok=True)
            created.append(d)

        return created

    def _generate_claude_agents(
        self,
        project_dir: Path,
        project_name: str,
        product_design: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> List[str]:
        """Copy agent templates from templates/agents/ and customize for project."""
        files = []
        agents_dir = project_dir / ".claude" / "agents"
        templates_agents_dir = self.templates_dir / "agents"

        vision = product_design.get("vision", "Build an amazing application")
        tech_stack = architecture.get("tech_stack", {})

        # Check if templates exist
        if templates_agents_dir.exists():
            logger.info("Copying agent templates", templates_dir=str(templates_agents_dir))

            # Copy all agent template files
            for template_file in templates_agents_dir.glob("*.md"):
                content = template_file.read_text(encoding="utf-8")

                # Customize content by replacing "Life OS" with project name
                customized_content = content.replace("Life OS", project_name)
                customized_content = customized_content.replace("life-os", project_name.lower().replace(" ", "-"))

                # Write to project's .claude/agents/
                dest_file = agents_dir / template_file.name
                self._write_file(dest_file, customized_content)
                files.append(f".claude/agents/{template_file.name}")

            logger.info(f"Copied {len(files)} agent templates")
        else:
            logger.warning("Templates directory not found, generating basic agents", path=str(templates_agents_dir))
            # Fallback to generating basic agent definitions
            files = self._generate_basic_agents(agents_dir, project_name, product_design, architecture)

        return files

    def _generate_basic_agents(
        self,
        agents_dir: Path,
        project_name: str,
        product_design: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> List[str]:
        """Generate basic agent files when templates are not available."""
        files = []
        tech_stack = architecture.get("tech_stack", {})
        backend = tech_stack.get("backend", "FastAPI")
        frontend = tech_stack.get("frontend", "React")

        # Core agents to create
        basic_agents = {
            "orchestration": {
                "description": f"Master coordinator for {project_name}. Manages the complete development workflow.",
                "model": "opus",
            },
            "po": {
                "description": "Product Owner - Defines vision, user stories, and acceptance criteria.",
                "model": "sonnet",
            },
            "requirement": {
                "description": "Requirements Engineer - Creates detailed technical requirements.",
                "model": "sonnet",
            },
            "fullstack-architect": {
                "description": f"Full-Stack Architect - Designs {backend} backend and {frontend} frontend architecture.",
                "model": "opus",
            },
            "backend-architect": {
                "description": f"Backend Architect - Designs APIs, services, and data layer.",
                "model": "opus",
            },
            "fullstack-developer": {
                "description": f"Full-Stack Developer - Implements features with {backend} and {frontend}.",
                "model": "sonnet",
            },
            "backend-developer": {
                "description": f"Backend Developer - Implements APIs and services.",
                "model": "sonnet",
            },
            "frontend-developer": {
                "description": f"Frontend Developer - Implements UI components.",
                "model": "sonnet",
            },
            "qa-automation-engineer": {
                "description": "QA Engineer - Creates and runs automated tests.",
                "model": "sonnet",
            },
            "playwright-e2e-tester": {
                "description": "E2E Tester - Runs end-to-end tests with Playwright.",
                "model": "sonnet",
            },
        }

        for agent_name, config in basic_agents.items():
            content = f'''---
name: {agent_name}
description: {config["description"]}
model: {config["model"]}
---

You are the {agent_name.replace("-", " ").title()} for the {project_name} project.

{config["description"]}

## Responsibilities

Follow the multi-agent workflow defined in docs/workflow.md and coordinate with other agents through the orchestrator.

## Guidelines

1. Read all existing documentation before starting work
2. Follow established file naming conventions
3. Update existing documents instead of creating duplicates
4. Write tests for all code implementations
5. Document all decisions and changes
'''
            file_path = agents_dir / f"{agent_name}.md"
            self._write_file(file_path, content)
            files.append(f".claude/agents/{agent_name}.md")

        return files

    def _get_agent_definitions(
        self,
        project_name: str,
        product_design: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Define all 20+ agents."""
        vision = product_design.get("vision", "Build an amazing application")
        tech_stack = architecture.get("tech_stack", {})
        backend = tech_stack.get("backend", "FastAPI")
        frontend = tech_stack.get("frontend", "React")
        database = tech_stack.get("database", "PostgreSQL")

        return {
            # === Core Orchestration ===
            "orchestration": {
                "model": "sonnet",
                "description": f"Master coordinator for {project_name}. Manages the complete development workflow from product design through deployment.",
                "role": "orchestrator",
                "responsibilities": [
                    "Coordinate all specialized agents in the correct workflow order",
                    "Manage phase transitions and approval gates",
                    "Track project status and progress",
                    "Handle parallel execution of independent modules",
                    "Ensure dependencies are satisfied before phase transitions",
                ],
                "workflow_phases": [
                    "Phase 1: Planning & Design (PO → Requirements → UX → Architecture)",
                    "Phase 2: Development (Parallel module development)",
                    "Phase 3: Architect Review",
                    "Phase 4: Developer Rework (if needed)",
                    "Phase 5: Testing (Parallel testing)",
                    "Phase 6: Architect Re-Review",
                    "Phase 7: Final Approval",
                    "Phase 8: Next Phase/Deployment",
                ],
                "commands": [
                    "/agent:orchestration start - Begin project from Phase 1",
                    "/agent:orchestration status - Show current project status",
                    "/agent:orchestration next - Move to next phase",
                ],
            },

            # === Product & Requirements ===
            "po": {
                "model": "sonnet",
                "description": "Product Owner - Defines vision, scope, user stories, and acceptance criteria.",
                "role": "product_owner",
                "responsibilities": [
                    "Define product vision and goals",
                    "Create user personas and user journeys",
                    "Write user stories in INVEST format",
                    "Define acceptance criteria (Given/When/Then)",
                    "Prioritize backlog and define MVP scope",
                    "Manage epics and story points",
                ],
                "outputs": [
                    "docs/product/vision.md",
                    "docs/product/personas.md",
                    "docs/product/user-stories.md",
                    "docs/product/epics.md",
                    "docs/product/mvp-scope.md",
                ],
            },

            "requirement": {
                "model": "sonnet",
                "description": "Requirements Engineer - Converts product vision into detailed technical requirements.",
                "role": "requirements_engineer",
                "responsibilities": [
                    "Convert user stories to functional requirements",
                    "Define non-functional requirements (performance, security, scalability)",
                    "Create data requirements and validation rules",
                    "Define integration requirements",
                    "Ensure requirements are testable and traceable",
                ],
                "outputs": [
                    "docs/specs/functional-requirements.md",
                    "docs/specs/non-functional-requirements.md",
                    "docs/specs/data-requirements.md",
                    "docs/specs/integration-requirements.md",
                ],
            },

            # === Architecture Agents ===
            "architecture": {
                "model": "opus",
                "description": "General Software Architect - Designs overall system architecture and makes technology decisions.",
                "role": "architect",
                "responsibilities": [
                    "Design system architecture and component structure",
                    "Create Architecture Decision Records (ADRs)",
                    "Define system boundaries and interfaces",
                    "Ensure architectural consistency across modules",
                    "Review and approve technical designs",
                ],
                "outputs": [
                    "docs/architecture/system-design.md",
                    "docs/architecture/adr/",
                    "docs/architecture/component-diagram.md",
                ],
            },

            "fullstack-architect": {
                "model": "opus",
                "description": f"Full-Stack Architect - Designs end-to-end system with {backend} backend and {frontend} frontend.",
                "role": "fullstack_architect",
                "tech_stack": tech_stack,
                "responsibilities": [
                    "Design frontend-backend integration patterns",
                    "Select and configure tech stack",
                    "Define API contracts between layers",
                    "Design state management and data flow",
                    "Ensure cross-platform consistency",
                ],
            },

            "backend-architect": {
                "model": "opus",
                "description": f"Backend Architect - Designs {backend} APIs, services, and {database} data layer.",
                "role": "backend_architect",
                "responsibilities": [
                    "Design RESTful/GraphQL API architecture",
                    "Define microservices boundaries (if applicable)",
                    "Design database schema and relationships",
                    "Define authentication/authorization patterns",
                    "Design caching and performance strategies",
                ],
                "outputs": [
                    "docs/architecture/backend-architecture.md",
                    "docs/architecture/api-design.md",
                    "docs/architecture/database-schema.md",
                ],
            },

            "frontend-architect": {
                "model": "sonnet",
                "description": f"Frontend Architect - Designs {frontend} UI architecture and component structure.",
                "role": "frontend_architect",
                "responsibilities": [
                    "Design component hierarchy and structure",
                    "Define state management patterns",
                    "Design routing and navigation",
                    "Create design system specifications",
                    "Ensure accessibility compliance",
                ],
                "outputs": [
                    "docs/architecture/frontend-architecture.md",
                    "docs/architecture/component-structure.md",
                    "docs/architecture/design-system.md",
                ],
            },

            "database-architect": {
                "model": "opus",
                "description": f"Database Architect - Designs {database} data model and optimization strategies.",
                "role": "database_architect",
                "responsibilities": [
                    "Design normalized database schema",
                    "Define indexes and query optimization",
                    "Design data migration strategies",
                    "Plan backup and recovery procedures",
                    "Define data retention policies",
                ],
            },

            "security-architect": {
                "model": "opus",
                "description": "Security Architect - Designs authentication, authorization, and compliance measures.",
                "role": "security_architect",
                "responsibilities": [
                    "Design authentication flows (OAuth, JWT, etc.)",
                    "Define authorization and RBAC patterns",
                    "Conduct threat modeling",
                    "Ensure compliance (GDPR, HIPAA, PCI-DSS as needed)",
                    "Design encryption and data protection",
                ],
                "outputs": [
                    "docs/architecture/security-design.md",
                    "docs/architecture/threat-model.md",
                ],
            },

            "infrastructure-architect": {
                "model": "sonnet",
                "description": "Infrastructure Architect - Designs cloud architecture, DevOps, and IaC.",
                "role": "infrastructure_architect",
                "responsibilities": [
                    "Design cloud infrastructure (AWS/GCP/Azure)",
                    "Define Infrastructure as Code (Terraform/Pulumi)",
                    "Design CI/CD pipelines",
                    "Plan scaling and high availability",
                    "Design monitoring and observability",
                ],
            },

            "ai-architect": {
                "model": "opus",
                "description": "AI Architect - Designs LLM integration, RAG systems, and AI agent orchestration.",
                "role": "ai_architect",
                "responsibilities": [
                    "Design RAG pipeline architecture",
                    "Define embedding and vector search strategies",
                    "Design multi-agent orchestration patterns",
                    "Plan LLM context management",
                    "Design AI safety and guardrails",
                ],
            },

            "ml-architect": {
                "model": "opus",
                "description": "ML Architect - Designs ML pipelines, model architecture, and MLOps.",
                "role": "ml_architect",
                "responsibilities": [
                    "Design ML training pipelines",
                    "Define model architecture and selection",
                    "Design feature engineering pipelines",
                    "Plan model versioning and deployment",
                    "Design A/B testing for models",
                ],
            },

            # === Developer Agents ===
            "developer": {
                "model": "sonnet",
                "description": "Senior Developer - Generates production-ready code following best practices.",
                "role": "developer",
                "responsibilities": [
                    "Implement features according to specifications",
                    "Write clean, maintainable code",
                    "Follow coding standards and patterns",
                    "Write unit tests for all code",
                    "Document code and APIs",
                ],
            },

            "fullstack-developer": {
                "model": "sonnet",
                "description": f"Full-Stack Developer - Implements end-to-end features with {backend} and {frontend}.",
                "role": "fullstack_developer",
                "tech_stack": tech_stack,
                "responsibilities": [
                    "Implement frontend components and pages",
                    "Implement backend APIs and services",
                    "Integrate frontend with backend APIs",
                    "Handle state management and data flow",
                    "Write tests for both layers",
                ],
            },

            "backend-developer": {
                "model": "sonnet",
                "description": f"Backend Developer - Implements {backend} APIs, services, and database operations.",
                "role": "backend_developer",
                "responsibilities": [
                    "Implement RESTful/GraphQL endpoints",
                    "Implement business logic services",
                    "Write database queries and migrations",
                    "Implement authentication/authorization",
                    "Write unit and integration tests",
                ],
            },

            "frontend-developer": {
                "model": "sonnet",
                "description": f"Frontend Developer - Implements {frontend} UI components and state management.",
                "role": "frontend_developer",
                "responsibilities": [
                    "Implement UI components following design system",
                    "Implement state management",
                    "Handle routing and navigation",
                    "Integrate with backend APIs",
                    "Write component tests",
                ],
            },

            "aiml-developer": {
                "model": "sonnet",
                "description": "AI/ML Developer - Implements ML models, training pipelines, and LLM integration.",
                "role": "aiml_developer",
                "responsibilities": [
                    "Implement ML model training pipelines",
                    "Integrate LLM APIs (Claude, OpenAI)",
                    "Implement RAG and embedding pipelines",
                    "Build AI agent orchestration",
                    "Write ML-specific tests",
                ],
            },

            # === Testing Agents ===
            "testing": {
                "model": "sonnet",
                "description": "QA Engineer - Creates comprehensive test suites and identifies edge cases.",
                "role": "qa_engineer",
                "responsibilities": [
                    "Create test plans and test cases",
                    "Write unit tests for all modules",
                    "Write integration tests for APIs",
                    "Identify edge cases and boundary conditions",
                    "Perform regression testing",
                ],
                "outputs": [
                    "tests/unit/",
                    "tests/integration/",
                    "docs/testing/test-plan.md",
                ],
            },

            "playwright-e2e-tester": {
                "model": "sonnet",
                "description": "Playwright E2E Tester - Runs end-to-end tests across browsers.",
                "role": "e2e_tester",
                "responsibilities": [
                    "Write Playwright E2E test scripts",
                    "Test critical user flows",
                    "Cross-browser testing (Chromium, Firefox, WebKit)",
                    "Visual regression testing",
                    "Generate test reports",
                ],
                "outputs": [
                    "tests/e2e/",
                    "playwright.config.ts",
                ],
            },

            # === Support Agents ===
            "cicd": {
                "model": "haiku",
                "description": "DevOps Engineer - Generates CI/CD pipelines and deployment configurations.",
                "role": "devops",
                "responsibilities": [
                    "Create GitHub Actions workflows",
                    "Configure build and test pipelines",
                    "Set up deployment pipelines",
                    "Configure environment variables",
                    "Set up monitoring and alerts",
                ],
                "outputs": [
                    ".github/workflows/ci.yml",
                    ".github/workflows/deploy.yml",
                    "docker-compose.yml",
                    "Dockerfile",
                ],
            },

            "documentation": {
                "model": "haiku",
                "description": "Technical Writer - Creates README, API docs, and architecture documentation.",
                "role": "documentation",
                "responsibilities": [
                    "Write README with setup instructions",
                    "Document API endpoints",
                    "Create architecture documentation",
                    "Write developer guides",
                    "Maintain changelog",
                ],
                "outputs": [
                    "README.md",
                    "docs/api/",
                    "CHANGELOG.md",
                    "CONTRIBUTING.md",
                ],
            },

            "expert": {
                "model": "sonnet",
                "description": "Domain Expert - Provides tech stack guidance and best practices.",
                "role": "expert",
                "responsibilities": [
                    "Provide domain-specific expertise",
                    "Recommend best practices",
                    "Review technical decisions",
                    "Identify potential issues",
                    "Suggest optimizations",
                ],
            },
        }

    def _format_agent_md(self, agent_name: str, config: Dict[str, Any]) -> str:
        """Format agent configuration as markdown."""
        lines = [
            f"# {agent_name}",
            "",
            f"**Model**: {config.get('model', 'sonnet')}",
            "",
            f"## Description",
            config.get('description', ''),
            "",
            f"## Role",
            config.get('role', agent_name),
            "",
        ]

        if 'responsibilities' in config:
            lines.extend([
                "## Responsibilities",
                "",
            ])
            for resp in config['responsibilities']:
                lines.append(f"- {resp}")
            lines.append("")

        if 'workflow_phases' in config:
            lines.extend([
                "## Workflow Phases",
                "",
            ])
            for phase in config['workflow_phases']:
                lines.append(f"- {phase}")
            lines.append("")

        if 'outputs' in config:
            lines.extend([
                "## Outputs",
                "",
            ])
            for output in config['outputs']:
                lines.append(f"- `{output}`")
            lines.append("")

        if 'commands' in config:
            lines.extend([
                "## Commands",
                "",
            ])
            for cmd in config['commands']:
                lines.append(f"- `{cmd}`")
            lines.append("")

        if 'tech_stack' in config:
            lines.extend([
                "## Tech Stack",
                "",
            ])
            for key, value in config['tech_stack'].items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")

        return "\n".join(lines)

    def _generate_claude_md(
        self,
        project_dir: Path,
        project_name: str,
        product_design: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> List[str]:
        """Generate CLAUDE.md with project instructions."""
        files = []
        vision = product_design.get("vision", "")
        tech_stack = architecture.get("tech_stack", {})

        claude_md = f'''# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**{project_name}** - {vision}

**Current Status:** Development phase - Use orchestration agent to manage workflow.

## Quick Start

```bash
# Start the full development workflow
/agent:orchestration start

# Check project status
/agent:orchestration status

# Move to next phase
/agent:orchestration next
```

## Architecture

```
{project_name}/
├── .claude/agents/          # Agent definitions (20+ agents)
├── docs/
│   ├── specs/               # Technical specifications
│   ├── product/             # Product design documents
│   ├── architecture/        # Architecture documents
│   └── project-status/      # Status tracking
├── src/
│   ├── orchestrator/        # Orchestration engine
│   ├── agents/              # Agent implementations
│   ├── web/
│   │   ├── frontend/        # {tech_stack.get("frontend", "React")} frontend
│   │   └── backend/         # {tech_stack.get("backend", "FastAPI")} backend
│   └── integrations/        # External integrations
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
└── config/                  # Configuration files
```

## Workflow Phases

The project follows an 8-phase development workflow:

### Phase 1: Planning & Design
1. **Product Owner** (`/agent:po`) - Defines vision, user stories, acceptance criteria
2. **Requirements Engineer** (`/agent:requirement`) - Creates detailed requirements
3. **UX Designer** - Creates user flows and wireframes
4. **Architects** (`/agent:architecture`, `/agent:backend-architect`, etc.) - Technical design

### Phase 2: Development (Parallel)
- **Full-Stack Developer** (`/agent:fullstack-developer`)
- **Backend Developer** (`/agent:backend-developer`)
- **Frontend Developer** (`/agent:frontend-developer`)
- **AI/ML Developer** (`/agent:aiml-developer`)

### Phase 3-4: Review & Rework
- Architect review of implementations
- Developer fixes based on feedback

### Phase 5: Testing (Parallel)
- **QA Engineer** (`/agent:testing`) - Unit and integration tests
- **E2E Tester** (`/agent:playwright-e2e-tester`) - End-to-end tests

### Phase 6-7: Re-Review & Approval
- Final architect review
- Lead architect sign-off

### Phase 8: Next Phase
- Deploy or start next sprint

## Agent Usage

### Core Agents
| Agent | Command | Purpose |
|-------|---------|---------|
| orchestration | `/agent:orchestration` | Master coordinator |
| po | `/agent:po` | Product Owner |
| requirement | `/agent:requirement` | Requirements Engineer |

### Architect Agents
| Agent | Command | Purpose |
|-------|---------|---------|
| architecture | `/agent:architecture` | System architecture |
| fullstack-architect | `/agent:fullstack-architect` | Full-stack design |
| backend-architect | `/agent:backend-architect` | Backend/API design |
| frontend-architect | `/agent:frontend-architect` | Frontend/UI design |
| database-architect | `/agent:database-architect` | Database design |
| security-architect | `/agent:security-architect` | Security design |
| ai-architect | `/agent:ai-architect` | AI/LLM design |

### Developer Agents
| Agent | Command | Purpose |
|-------|---------|---------|
| developer | `/agent:developer` | General development |
| fullstack-developer | `/agent:fullstack-developer` | Full-stack implementation |
| backend-developer | `/agent:backend-developer` | Backend implementation |
| frontend-developer | `/agent:frontend-developer` | Frontend implementation |
| aiml-developer | `/agent:aiml-developer` | AI/ML implementation |

### Support Agents
| Agent | Command | Purpose |
|-------|---------|---------|
| testing | `/agent:testing` | QA and test creation |
| playwright-e2e-tester | `/agent:playwright-e2e-tester` | E2E testing |
| cicd | `/agent:cicd` | CI/CD pipelines |
| documentation | `/agent:documentation` | Documentation |

## Tech Stack

- **Backend**: {tech_stack.get("backend", "FastAPI (Python)")}
- **Frontend**: {tech_stack.get("frontend", "React")}
- **Database**: {tech_stack.get("database", "PostgreSQL")}
- **Cache**: {tech_stack.get("cache", "Redis")}

## Development Guidelines

### Before Starting Development
1. Read existing documentation in `docs/`
2. Follow existing file naming conventions
3. Update existing documents, don't create duplicates
4. Use the "Embed Not Add-On" principle

### Code Standards
- Write unit tests for all new code
- Follow existing code patterns
- Document public APIs
- Use type hints (Python) / TypeScript

### Commit Standards
- Write clear commit messages
- Include test files with implementation
- Never commit with failing tests

## Project Status

Check `docs/project-status/` for:
- `module-tracking.md` - Module-level status
- `phase-completion.md` - Phase completion records
'''
        self._write_file(project_dir / "CLAUDE.md", claude_md)
        files.append("CLAUDE.md")

        return files

    def _generate_workflow(
        self,
        project_dir: Path,
        project_name: str,
        product_design: Dict[str, Any]
    ) -> List[str]:
        """Copy workflow template or generate one."""
        files = []

        # Try to copy from templates/WorkFlow.txt
        workflow_template = self.templates_dir / "WorkFlow.txt"
        if workflow_template.exists():
            logger.info("Copying workflow template", template=str(workflow_template))
            workflow_content = workflow_template.read_text(encoding="utf-8")
            # Customize for this project
            workflow_content = workflow_content.replace("LIFE OS", project_name.upper())
            workflow_content = workflow_content.replace("Life OS", project_name)
            self._write_file(project_dir / "docs" / "workflow.md", workflow_content)
            files.append("docs/workflow.md")
            return files

        # Fallback: generate workflow
        workflow = f'''# {project_name.upper()} — MULTI-AGENT WORKFLOW

## PARALLEL DEVELOPMENT STRATEGY

This project supports parallel development execution to accelerate delivery while maintaining quality.

### Parallel Execution Principles
1. **Module Independence**: Each feature module designed for independent development
2. **Concurrent Agent Instances**: Multiple developer and tester agents work simultaneously
3. **Orchestrator Coordination**: Central orchestrator manages parallel workstreams
4. **Dependency Graph**: Orchestrator maintains module dependency graph

### When Parallelization Occurs
- **Phase 2 (Development)**: Multiple modules developed concurrently
- **Phase 3 (Architect Review)**: Architects can review multiple modules in parallel
- **Phase 5 (Testing)**: Multiple modules tested concurrently
- **Phase 6 (Re-Review)**: Parallel re-review of multiple fixed modules

---

## PHASE 1 — PLANNING & DESIGN

### Pre-Work Requirements (MANDATORY)

**BEFORE any agent begins Phase 1 work:**

1. **Read ALL Existing Documentation**
   - Orchestrator MUST search for and read all existing documentation
   - Identify existing file naming conventions
   - Provide agents with complete context

2. **Follow Existing File Naming Conventions**
   - NEVER create new files if existing files serve the same purpose
   - ALWAYS follow established naming patterns
   - MAINTAIN existing numbering schemes

3. **"EMBED NOT ADD-ON" PRINCIPLE**
   - New features MUST be embedded into existing documentation
   - NOT created as separate add-on files

### Phase 1 Agent Workflow

1. **Product Owner** (`/agent:po`)
   - Defines vision, scope, goals, feature list
   - Produces user stories and acceptance criteria
   - Outputs: `docs/product/`

2. **Requirements Engineer** (`/agent:requirement`)
   - Converts PO output into technical requirements
   - Defines functional/non-functional requirements
   - Outputs: `docs/specs/`

3. **Architects** (fullstack, backend, frontend, database, security, ai)
   - Review PO + Requirements outputs
   - Design system architecture
   - Outputs: `docs/architecture/`

4. **Orchestrator Review**
   - Ensures all planning artifacts are complete
   - Validates no duplicate files created
   - Approves move to Development

---

## PHASE 2 — DEVELOPMENT (PARALLEL)

### Developer Agents
- **fullstack-developer**: End-to-end feature implementation
- **backend-developer**: API and service implementation
- **frontend-developer**: UI component implementation
- **aiml-developer**: AI/ML feature implementation

### Development Requirements (MANDATORY)

1. **Write Unit Tests**
   - Create comprehensive unit tests for ALL new code
   - Test coverage: happy paths, edge cases, error handling

2. **Execute Tests Locally**
   - Run tests and verify ALL pass before submitting
   - Fix any failing tests before proceeding

3. **Commit Requirements**
   - NEVER commit code without unit tests
   - NEVER commit with failing tests

---

## PHASE 3 — ARCHITECT REVIEW (ROUND 1)

All Architects review the implementation:
- Full-Stack Architect: frontend/backend integration
- Backend Architect: APIs, services, data models
- Frontend Architect: UI components, state management
- AI/ML Architect: AI behavior, RAG, embeddings

**Result**: Approved → Testing | Rework → Back to Developers

---

## PHASE 4 — DEVELOPER REWORK (IF NEEDED)

- Fix issues identified by architects
- Update implementation and resubmit
- Loop continues until architects approve

---

## PHASE 5 — TESTING (PARALLEL)

### Testing Agents
- **testing**: Unit tests, integration tests, API tests
- **playwright-e2e-tester**: E2E tests across browsers

### Test Types
1. Unit Tests - Individual component testing
2. Integration Tests - Cross-component testing
3. E2E Tests - Full user flow testing
4. Visual Tests - UI regression testing

**Result**: Pass → Re-Review | Fail → Back to Developers

---

## PHASE 6 — ARCHITECT RE-REVIEW

- Validate fixes
- Ensure no regressions
- Confirm architecture integrity

**Result**: Approved → Final Approval | More Fixes → Developers

---

## PHASE 7 — FINAL APPROVAL

- Lead Architect + QA Lead sign-off
- Confirm requirements met
- Confirm no open defects

---

## PHASE 8 — NEXT PHASE

- Trigger next module/sprint
- Deploy to environment
- Update project status

---

## SUMMARY

### Sequential Flow
PO → Requirements → Architecture → Development → Review → Rework → Testing → Re-Review → Approval → Next

### Parallel Execution Model
- Phase 1: Sequential (planning)
- Phase 2: **PARALLEL** (development)
- Phase 3: **PARALLEL** (review)
- Phase 5: **PARALLEL** (testing)
- Phase 7: Sequential (approval)

### Key Benefits
- Faster time to market
- Resource optimization
- Risk mitigation
- Scalability
'''
        self._write_file(project_dir / "docs" / "workflow.md", workflow)
        files.append("docs/workflow.md")

        return files

    def _generate_docs(
        self,
        project_dir: Path,
        project_name: str,
        product_design: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> List[str]:
        """Generate documentation structure."""
        files = []
        vision = product_design.get("vision", "")
        epics = product_design.get("epics", [])
        personas = product_design.get("personas", [])
        tech_stack = architecture.get("tech_stack", {})

        # Product Vision
        vision_md = f'''# Product Vision

## Overview
{vision}

## Goals
{self._format_list(product_design.get("goals", []))}

## Target Audience
{product_design.get("target_audience", "To be defined")}

## Value Proposition
{self._format_list(product_design.get("value_proposition", []))}
'''
        self._write_file(project_dir / "docs" / "product" / "vision.md", vision_md)
        files.append("docs/product/vision.md")

        # Personas
        personas_md = "# User Personas\n\n"
        for persona in personas:
            if isinstance(persona, dict):
                personas_md += f'''## {persona.get("name", "User")}
- **Role**: {persona.get("role", "User")}
- **Description**: {persona.get("description", "")}
- **Goals**: {", ".join(persona.get("goals", []))}
- **Pain Points**: {", ".join(persona.get("pain_points", []))}

'''
        self._write_file(project_dir / "docs" / "product" / "personas.md", personas_md)
        files.append("docs/product/personas.md")

        # Epics
        epics_md = "# Epics\n\n"
        for epic in epics:
            if isinstance(epic, dict):
                epics_md += f'''## {epic.get("id", "E001")}: {epic.get("title", "Epic")}
- **Priority**: {epic.get("priority", "P1")}
- **Story Points**: {epic.get("story_points", 0)}
- **Description**: {epic.get("description", "")}

'''
        self._write_file(project_dir / "docs" / "product" / "epics.md", epics_md)
        files.append("docs/product/epics.md")

        # Architecture Overview
        arch_md = f'''# Architecture Overview

## Tech Stack
- **Backend**: {tech_stack.get("backend", "FastAPI")}
- **Frontend**: {tech_stack.get("frontend", "React")}
- **Database**: {tech_stack.get("database", "PostgreSQL")}

## System Components
{self._format_components(architecture.get("system_components", []))}

## Data Model
{json.dumps(architecture.get("data_model", {}), indent=2)}

## API Design
{json.dumps(architecture.get("api_design", {}), indent=2)}

## Security
{json.dumps(architecture.get("security", {}), indent=2)}
'''
        self._write_file(project_dir / "docs" / "architecture" / "overview.md", arch_md)
        files.append("docs/architecture/overview.md")

        # Project Status
        status_md = f'''# Project Status

## Module Tracking

| Module | Status | Current Phase | Last Updated |
|--------|--------|---------------|--------------|
| Core | Not Started | - | {datetime.now().strftime("%Y-%m-%d")} |

## Phase Completion

| Phase | Status | Completed Date |
|-------|--------|----------------|
| Phase 1: Planning | Not Started | - |
| Phase 2: Development | Not Started | - |
| Phase 3: Review | Not Started | - |
| Phase 5: Testing | Not Started | - |
| Phase 7: Approval | Not Started | - |
'''
        self._write_file(project_dir / "docs" / "project-status" / "status.md", status_md)
        files.append("docs/project-status/status.md")

        # Specs placeholder
        specs_md = '''# Technical Specifications

## Functional Requirements
_To be generated by Requirements Engineer_

## Non-Functional Requirements
_To be generated by Requirements Engineer_

## Data Requirements
_To be generated by Requirements Engineer_
'''
        self._write_file(project_dir / "docs" / "specs" / "requirements.md", specs_md)
        files.append("docs/specs/requirements.md")

        # Requirements directory - detailed requirements from Requirements Engineer
        func_req_md = f'''# Functional Requirements

## Overview
Functional requirements for {project_name} generated by Requirements Engineer.

## User Stories Traceability
_Maps requirements to user stories from Product Owner_

## FR-001: [Requirement Title]
- **Priority**: High
- **User Story**: US-001
- **Description**: _To be defined_
- **Acceptance Criteria**:
  - [ ] Criteria 1
  - [ ] Criteria 2

## FR-002: [Requirement Title]
- **Priority**: Medium
- **User Story**: US-002
- **Description**: _To be defined_
- **Acceptance Criteria**:
  - [ ] Criteria 1
  - [ ] Criteria 2

_Add more functional requirements as defined by Requirements Engineer_
'''
        self._write_file(project_dir / "docs" / "requirements" / "functional-requirements.md", func_req_md)
        files.append("docs/requirements/functional-requirements.md")

        nfr_md = f'''# Non-Functional Requirements

## Overview
Non-functional requirements for {project_name}.

## Performance Requirements
- **NFR-P001**: Response time < 200ms for API calls
- **NFR-P002**: Support 1000 concurrent users
- **NFR-P003**: Page load time < 3 seconds

## Security Requirements
- **NFR-S001**: All data encrypted at rest and in transit
- **NFR-S002**: Authentication required for all protected endpoints
- **NFR-S003**: Session timeout after 30 minutes of inactivity

## Scalability Requirements
- **NFR-SC001**: Horizontal scaling capability
- **NFR-SC002**: Database supports read replicas

## Availability Requirements
- **NFR-A001**: 99.9% uptime SLA
- **NFR-A002**: Automated failover capability

## Compliance Requirements
_Add compliance requirements as needed (GDPR, HIPAA, PCI-DSS, etc.)_

## Accessibility Requirements
- **NFR-AC001**: WCAG 2.1 AA compliance
- **NFR-AC002**: Screen reader support
'''
        self._write_file(project_dir / "docs" / "requirements" / "non-functional-requirements.md", nfr_md)
        files.append("docs/requirements/non-functional-requirements.md")

        data_req_md = f'''# Data Requirements

## Overview
Data requirements and models for {project_name}.

## Data Entities
_Defined by Database Architect based on architecture design_

## Data Validation Rules
| Field | Type | Validation |
|-------|------|------------|
| email | string | Valid email format |
| password | string | Min 8 chars, 1 uppercase, 1 number |

## Data Retention Policy
- User data: Retained for account lifetime + 30 days after deletion
- Logs: Retained for 90 days
- Analytics: Aggregated after 1 year

## Data Privacy
- PII fields must be encrypted
- User consent required for data collection
- Right to deletion supported
'''
        self._write_file(project_dir / "docs" / "requirements" / "data-requirements.md", data_req_md)
        files.append("docs/requirements/data-requirements.md")

        integration_req_md = f'''# Integration Requirements

## Overview
External integrations and API requirements for {project_name}.

## Third-Party Integrations
_List external services to integrate with_

## API Contracts
_Define API contracts for integrations_

## Authentication
_Define authentication methods for integrations (OAuth, API keys, etc.)_

## Error Handling
_Define error handling for integration failures_
'''
        self._write_file(project_dir / "docs" / "requirements" / "integration-requirements.md", integration_req_md)
        files.append("docs/requirements/integration-requirements.md")

        return files

    def _generate_source_structure(
        self,
        project_dir: Path,
        project_name: str,
        tech_stack: Dict[str, Any],
        architecture: Dict[str, Any]
    ) -> List[str]:
        """Generate source code structure - just a .gitkeep to keep src/ in git."""
        files = []
        # Just create a .gitkeep so src/ is tracked in git
        # Actual source structure will be created by developers using Claude Code CLI
        self._write_file(project_dir / "src" / ".gitkeep", "# Source code directory - structure created during development\n")
        files.append("src/.gitkeep")
        return files

    def _generate_fastapi_backend(self, project_dir: Path, project_name: str, architecture: Dict[str, Any]) -> List[str]:
        """Generate FastAPI backend structure."""
        files = []
        backend_dir = project_dir / "src" / "web" / "backend"

        # pyproject.toml
        pyproject = f'''[project]
name = "{project_name}"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "sqlalchemy[asyncio]>=2.0.25",
    "alembic>=1.13.0",
    "httpx>=0.26.0",
    "structlog>=24.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",
]
'''
        self._write_file(backend_dir / "pyproject.toml", pyproject)
        files.append("src/web/backend/pyproject.toml")

        # main.py
        main_py = f'''"""
{project_name} - FastAPI Application
Generated by Project Bootstrap
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="{project_name}", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {{"status": "healthy"}}

@app.get("/api/v1")
async def api_root():
    return {{"message": "{project_name} API"}}
'''
        self._write_file(backend_dir / "app" / "main.py", main_py)
        files.append("src/web/backend/app/main.py")

        # __init__.py files
        for init_dir in ["app", "app/api", "app/models", "app/schemas", "app/services"]:
            self._write_file(backend_dir / init_dir / "__init__.py", '"""Package."""\n')
            files.append(f"src/web/backend/{init_dir}/__init__.py")

        return files

    def _generate_react_frontend(self, project_dir: Path, project_name: str) -> List[str]:
        """Generate React frontend structure."""
        files = []
        frontend_dir = project_dir / "src" / "web" / "frontend"

        # package.json
        package_json = {
            "name": f"{project_name}-frontend",
            "version": "0.1.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "tsc && vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "react-router-dom": "^6.21.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "@vitejs/plugin-react": "^4.2.0",
                "typescript": "^5.3.0",
                "vite": "^5.0.0",
                "tailwindcss": "^3.4.0"
            }
        }
        self._write_file(frontend_dir / "package.json", json.dumps(package_json, indent=2))
        files.append("src/web/frontend/package.json")

        # index.html
        index_html = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
'''
        self._write_file(frontend_dir / "index.html", index_html)
        files.append("src/web/frontend/index.html")

        # src/main.tsx
        main_tsx = '''import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
'''
        self._write_file(frontend_dir / "src" / "main.tsx", main_tsx)
        files.append("src/web/frontend/src/main.tsx")

        # src/App.tsx
        app_tsx = f'''function App() {{
  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <h1 className="text-4xl font-bold">{project_name}</h1>
      <p className="mt-4">Welcome to your new project!</p>
    </div>
  );
}}

export default App;
'''
        self._write_file(frontend_dir / "src" / "App.tsx", app_tsx)
        files.append("src/web/frontend/src/App.tsx")

        return files

    def _generate_orchestrator(self, project_dir: Path, project_name: str) -> List[str]:
        """Generate orchestrator structure."""
        files = []
        orch_dir = project_dir / "src" / "orchestrator"

        # engine.py
        engine_py = f'''"""
Orchestration Engine for {project_name}
Coordinates multi-agent workflow execution.
"""
from typing import Dict, Any, List
from enum import Enum

class WorkflowPhase(Enum):
    PLANNING = "planning"
    DEVELOPMENT = "development"
    REVIEW = "review"
    TESTING = "testing"
    APPROVAL = "approval"
    DEPLOYMENT = "deployment"

class OrchestrationEngine:
    """Coordinates the multi-agent development workflow."""

    def __init__(self):
        self.current_phase = WorkflowPhase.PLANNING
        self.agents: Dict[str, Any] = {{}}
        self.status: Dict[str, Any] = {{}}

    async def start_workflow(self):
        """Start the orchestration workflow from Phase 1."""
        self.current_phase = WorkflowPhase.PLANNING
        # TODO: Implement workflow start logic

    async def next_phase(self):
        """Transition to the next workflow phase."""
        # TODO: Implement phase transition logic
        pass

    async def get_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        return {{
            "phase": self.current_phase.value,
            "agents": self.agents,
            "status": self.status,
        }}
'''
        self._write_file(orch_dir / "engine.py", engine_py)
        files.append("src/orchestrator/engine.py")

        # __init__.py
        self._write_file(orch_dir / "__init__.py", '"""Orchestration engine package."""\n')
        files.append("src/orchestrator/__init__.py")

        return files

    def _generate_tests_structure(self, project_dir: Path, project_name: str) -> List[str]:
        """Generate tests structure."""
        files = []
        tests_dir = project_dir / "tests"

        # conftest.py
        conftest = '''"""Pytest configuration and fixtures."""
import pytest

@pytest.fixture
def app():
    """Create test application."""
    from src.web.backend.app.main import app
    return app
'''
        self._write_file(tests_dir / "conftest.py", conftest)
        files.append("tests/conftest.py")

        # Unit test example
        unit_test = '''"""Unit tests example."""
import pytest

def test_example():
    """Example unit test."""
    assert True
'''
        self._write_file(tests_dir / "unit" / "test_example.py", unit_test)
        files.append("tests/unit/test_example.py")

        # E2E test example
        e2e_test = '''"""E2E tests with Playwright."""
from playwright.sync_api import Page, expect

def test_homepage(page: Page):
    """Test homepage loads."""
    page.goto("/")
    expect(page).to_have_title_matching(r".*")
'''
        self._write_file(tests_dir / "e2e" / "test_homepage.py", e2e_test)
        files.append("tests/e2e/test_homepage.py")

        # playwright.config.ts
        playwright_config = '''import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  use: {
    baseURL: "http://localhost:3000",
  },
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
    { name: "firefox", use: { browserName: "firefox" } },
  ],
});
'''
        self._write_file(project_dir / "playwright.config.ts", playwright_config)
        files.append("playwright.config.ts")

        return files

    def _generate_configs(self, project_dir: Path, project_name: str, tech_stack: Dict[str, Any]) -> List[str]:
        """Generate configuration files."""
        files = []

        # .gitignore
        gitignore = '''# Python
__pycache__/
*.py[cod]
venv/
.venv/
.env

# Node
node_modules/
dist/

# IDE
.idea/
.vscode/
*.swp

# Database
*.db
*.sqlite3

# Logs
*.log
'''
        self._write_file(project_dir / ".gitignore", gitignore)
        files.append(".gitignore")

        # GitHub Actions CI
        ci_yml = f'''name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd src/web/backend
          pip install -e ".[dev]"

      - name: Run tests
        run: pytest tests/
'''
        self._write_file(project_dir / ".github" / "workflows" / "ci.yml", ci_yml)
        files.append(".github/workflows/ci.yml")

        # README.md
        readme = f'''# {project_name}

## Quick Start with Claude Code

```bash
# Start development workflow
/agent:orchestration start

# Check status
/agent:orchestration status
```

## Project Structure

- `.claude/agents/` - Agent definitions
- `docs/` - Documentation
- `src/` - Source code
- `tests/` - Test suites

## Development

See `CLAUDE.md` for full development workflow.
'''
        self._write_file(project_dir / "README.md", readme)
        files.append("README.md")

        return files

    def _format_list(self, items: List[Any]) -> str:
        """Format a list as markdown."""
        if not items:
            return "_None defined_"
        lines = []
        for item in items:
            if isinstance(item, dict):
                lines.append(f"- {item.get('goal', item.get('name', str(item)))}")
            else:
                lines.append(f"- {item}")
        return "\n".join(lines)

    def _format_components(self, components: List[Dict[str, Any]]) -> str:
        """Format components as markdown."""
        if not components:
            return "_None defined_"
        lines = []
        for comp in components:
            if isinstance(comp, dict):
                lines.append(f"- **{comp.get('name', 'Component')}**: {comp.get('description', '')}")
        return "\n".join(lines)

    def _init_git(self, project_dir: Path) -> dict:
        """Initialize git repository with branches: main, dev, test. Checkout to dev."""
        result = {
            "initialized": False,
            "branches": [],
            "current_branch": None,
            "error": None
        }
        try:
            # Initialize git
            subprocess.run(["git", "init"], cwd=project_dir, capture_output=True, check=True)

            # Configure git user if not set (needed for commits)
            subprocess.run(
                ["git", "config", "user.email", "bootstrap@project.local"],
                cwd=project_dir, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Project Bootstrap"],
                cwd=project_dir, capture_output=True
            )

            # Add all files and commit on main
            subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit - scaffolded by Project Bootstrap"],
                cwd=project_dir,
                capture_output=True,
                check=True
            )

            # Rename default branch to main (in case it's master)
            subprocess.run(
                ["git", "branch", "-M", "main"],
                cwd=project_dir, capture_output=True
            )
            result["branches"].append("main")

            # Create dev branch
            subprocess.run(
                ["git", "branch", "dev"],
                cwd=project_dir, capture_output=True, check=True
            )
            result["branches"].append("dev")

            # Create test branch
            subprocess.run(
                ["git", "branch", "test"],
                cwd=project_dir, capture_output=True, check=True
            )
            result["branches"].append("test")

            # Checkout to dev branch
            subprocess.run(
                ["git", "checkout", "dev"],
                cwd=project_dir, capture_output=True, check=True
            )
            result["current_branch"] = "dev"
            result["initialized"] = True

            return result
        except subprocess.CalledProcessError as e:
            result["error"] = str(e)
            return result
        except FileNotFoundError:
            result["error"] = "Git not found"
            return result

    def _write_file(self, path: Path, content: str):
        """Write content to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _validate_agents(self, project_dir: Path) -> Dict[str, Any]:
        """
        Validate all agent files in .claude/agents/ directory.
        Checks for:
        1. File exists and is readable
        2. No literal \\n strings (should be actual newlines)
        3. Valid frontmatter structure (--- delimited)
        4. Required fields in frontmatter (name, description)
        5. Non-empty content after frontmatter

        Returns validation results with errors and warnings.
        """
        agents_dir = project_dir / ".claude" / "agents"
        results = {
            "valid": True,
            "total_agents": 0,
            "valid_agents": 0,
            "agents_with_errors": 0,
            "agents_with_warnings": 0,
            "agents": [],
            "errors": [],
            "warnings": [],
        }

        if not agents_dir.exists():
            results["valid"] = False
            results["errors"].append("Agents directory does not exist: .claude/agents/")
            return results

        agent_files = list(agents_dir.glob("*.md"))
        results["total_agents"] = len(agent_files)

        for agent_file in agent_files:
            agent_result = self._validate_single_agent(agent_file)
            results["agents"].append(agent_result)

            if agent_result["errors"]:
                results["agents_with_errors"] += 1
                results["errors"].extend(
                    [f"{agent_file.name}: {e}" for e in agent_result["errors"]]
                )
            elif agent_result["warnings"]:
                results["agents_with_warnings"] += 1
                results["warnings"].extend(
                    [f"{agent_file.name}: {w}" for w in agent_result["warnings"]]
                )
            else:
                results["valid_agents"] += 1

        results["valid"] = results["agents_with_errors"] == 0
        return results

    def _validate_single_agent(self, agent_file: Path) -> Dict[str, Any]:
        """Validate a single agent file."""
        result = {
            "name": agent_file.stem,
            "file": agent_file.name,
            "valid": True,
            "errors": [],
            "warnings": [],
            "has_frontmatter": False,
            "has_content": False,
            "frontmatter_fields": [],
        }

        try:
            content = agent_file.read_text(encoding="utf-8")
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Cannot read file: {str(e)}")
            return result

        # Check for literal \n strings (common template error)
        if "\\n" in content:
            # Count occurrences
            count = content.count("\\n")
            result["errors"].append(
                f"Contains {count} literal '\\\\n' strings that should be actual newlines"
            )
            result["valid"] = False

        # Check for other escaped characters that shouldn't be there
        if "\\t" in content:
            result["warnings"].append("Contains literal '\\\\t' strings")

        # Check for frontmatter (--- delimited YAML)
        lines = content.split("\n")
        if lines and lines[0].strip() == "---":
            # Find closing ---
            closing_idx = -1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == "---":
                    closing_idx = i
                    break

            if closing_idx > 0:
                result["has_frontmatter"] = True
                frontmatter_lines = lines[1:closing_idx]

                # Extract fields from frontmatter
                for line in frontmatter_lines:
                    if ":" in line:
                        field = line.split(":")[0].strip()
                        result["frontmatter_fields"].append(field)

                # Check required fields
                required_fields = ["name", "description"]
                for field in required_fields:
                    if field not in result["frontmatter_fields"]:
                        result["warnings"].append(f"Missing recommended frontmatter field: {field}")

                # Check for content after frontmatter
                content_after = "\n".join(lines[closing_idx + 1:]).strip()
                result["has_content"] = len(content_after) > 0

                if not result["has_content"]:
                    result["warnings"].append("No content after frontmatter")
            else:
                result["warnings"].append("Frontmatter not properly closed (missing closing ---)")
        else:
            # No frontmatter - check if there's still useful content
            if content.strip():
                result["has_content"] = True
                result["warnings"].append("No frontmatter found (agent may not be properly recognized by CLI)")
            else:
                result["errors"].append("File is empty")
                result["valid"] = False

        # Check minimum content length
        if len(content.strip()) < 50:
            result["warnings"].append("Agent file has very little content")

        # Check for common CLI agent requirements
        # Agent should have some instruction text
        if result["has_content"]:
            lower_content = content.lower()
            if "you are" not in lower_content and "your role" not in lower_content:
                result["warnings"].append("Agent may be missing role definition (no 'You are' or 'Your role' found)")

        return result

    def _fix_agent_errors(self, project_dir: Path, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Attempt to automatically fix common agent errors.
        Returns fix results.
        """
        agents_dir = project_dir / ".claude" / "agents"
        fix_results = {
            "fixed": 0,
            "failed": 0,
            "details": [],
        }

        for agent in validation_results["agents"]:
            if not agent["valid"]:
                agent_file = agents_dir / agent["file"]
                try:
                    content = agent_file.read_text(encoding="utf-8")
                    original_content = content

                    # Fix literal \n strings
                    if "\\n" in content:
                        content = content.replace("\\n", "\n")

                    # Fix literal \t strings
                    if "\\t" in content:
                        content = content.replace("\\t", "\t")

                    # Only write if changed
                    if content != original_content:
                        agent_file.write_text(content, encoding="utf-8")
                        fix_results["fixed"] += 1
                        fix_results["details"].append(f"Fixed: {agent['file']}")
                    else:
                        fix_results["failed"] += 1
                        fix_results["details"].append(f"No auto-fix available: {agent['file']}")

                except Exception as e:
                    fix_results["failed"] += 1
                    fix_results["details"].append(f"Fix failed for {agent['file']}: {str(e)}")

        return fix_results
