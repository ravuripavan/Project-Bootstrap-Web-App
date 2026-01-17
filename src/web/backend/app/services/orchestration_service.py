"""
Orchestration service - Coordinates workflow execution.
Uses Claude AI to generate contextual product and architecture designs.
Scaffolds real projects on disk.
"""
from typing import Dict, Any, List, Optional
import asyncio
import json
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.enums import WorkflowMode, ProjectStatus
from app.core.database import async_session_maker
from app.models.project import Project
from app.config import get_settings
from app.services.scaffolding_service import ScaffoldingService

logger = structlog.get_logger()

# Discovery mode phases
DISCOVERY_PHASES = ["input", "product_design", "architecture_design", "code_generation", "quality", "scaffolding", "summary"]
# Direct mode phases
DIRECT_PHASES = ["input", "validation", "scaffolding", "ci_setup", "summary"]


class ClaudeClient:
    """Client for interacting with Claude API."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.anthropic_api_key
        self._client = None

    @property
    def client(self):
        if self._client is None and self.api_key:
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    async def generate_product_design(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate product design using Claude."""
        if not self.client:
            logger.warning("No Anthropic API key configured, using fallback generation")
            return self._fallback_product_design(input_data)

        project_name = input_data.get('project_name', 'project')
        project_overview = input_data.get('project_overview', '')
        target_users = input_data.get('target_users', '')
        key_features = input_data.get('key_features', '')

        prompt = f"""You are a Product Owner AI agent. Based on the following project overview, generate a comprehensive product design document.

PROJECT NAME: {project_name}

PROJECT OVERVIEW:
{project_overview}

TARGET USERS: {target_users or 'Not specified'}

KEY FEATURES: {key_features or 'Not specified'}

Generate a product design in the following JSON format. Be specific and contextual to the project described above:

{{
  "vision": "A compelling vision statement for this specific project (2-3 sentences)",
  "problem_statement": "The specific problem this project solves (2-3 sentences)",
  "target_audience": "Detailed description of target users",
  "value_proposition": ["4 specific value propositions for this project"],
  "goals": [
    {{"goal": "Specific measurable goal", "type": "timeline|growth|reliability|satisfaction", "priority": "high|medium|critical"}}
  ],
  "personas": [
    {{
      "name": "Persona Name - Role",
      "role": "Primary User|Secondary User|Admin",
      "age": "age range",
      "description": "Detailed persona description relevant to this project",
      "goals": ["3 specific goals for this persona"],
      "pain_points": ["3 pain points this project addresses"],
      "tech_comfort": "High|Medium|Low"
    }}
  ],
  "user_journey": {{
    "stages": [
      {{"stage": "Stage Name", "touchpoints": ["touchpoint1", "touchpoint2"], "emotions": "emotion"}}
    ],
    "flow_diagram": "Stage1 -> Stage2 -> Stage3..."
  }},
  "epics": [
    {{"id": "E001", "title": "Epic Title", "description": "Description", "priority": "P0|P1|P2", "story_points": 21}}
  ],
  "user_stories": [
    {{"id": "US001", "epic": "E001", "story": "As a user, I want...", "acceptance_criteria": ["criteria1", "criteria2"]}}
  ],
  "mvp_scope": {{
    "included_epics": ["E001", "E002"],
    "excluded_epics": ["E003"],
    "total_story_points": 100,
    "rationale": "Why these epics are in MVP",
    "release_criteria": ["criteria1", "criteria2"]
  }},
  "risks": [
    {{"id": "R001", "description": "Risk description", "severity": "low|medium|high|critical", "probability": "low|medium|high", "impact": "Impact description", "mitigation": "Mitigation strategy"}}
  ],
  "success_metrics": [
    {{"id": "M001", "metric": "Metric name", "target": "Target value", "timeframe": "Timeframe", "measurement": "How to measure"}}
  ],
  "competitive_analysis": {{
    "competitors": ["competitor1", "competitor2"],
    "differentiators": ["differentiator1", "differentiator2"]
  }}
}}

Generate at least:
- 3 detailed personas relevant to this specific project
- 5-7 epics with realistic story points
- 4 user stories
- 6 user journey stages
- 4 risks
- 5 success metrics

Make sure ALL content is specific to "{project_name}" and the described functionality. Do not use generic placeholder content.

Return ONLY valid JSON, no markdown formatting or explanation."""

        try:
            # Run the synchronous Anthropic call in a thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}]
                )
            )

            # Parse response
            content = response.content[0].text

            # Try to extract JSON from response
            try:
                # Remove any markdown code blocks if present
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                product_design = json.loads(content.strip())
                logger.info("Successfully generated product design with Claude", project_name=project_name)
                return product_design

            except json.JSONDecodeError as e:
                logger.error("Failed to parse Claude response as JSON", error=str(e))
                return self._fallback_product_design(input_data)

        except Exception as e:
            logger.error("Claude API call failed", error=str(e))
            return self._fallback_product_design(input_data)

    async def generate_architecture_design(self, input_data: Dict[str, Any], product_design: Dict[str, Any]) -> Dict[str, Any]:
        """Generate architecture design using Claude."""
        if not self.client:
            logger.warning("No Anthropic API key configured, using fallback generation")
            return self._fallback_architecture_design(input_data)

        project_name = input_data.get('project_name', 'project')
        project_overview = input_data.get('project_overview', '')

        # Extract epics for context
        epics_summary = "\n".join([f"- {e['title']}: {e['description']}" for e in product_design.get('epics', [])])

        prompt = f"""You are a Software Architect AI agent. Based on the following project and product design, generate a comprehensive architecture design.

PROJECT NAME: {project_name}

PROJECT OVERVIEW:
{project_overview}

PRODUCT EPICS:
{epics_summary}

Generate an architecture design in the following JSON format. Be specific to this project:

{{
  "tech_stack": {{
    "backend": "Specific framework/language",
    "frontend": "Specific framework",
    "database": "Specific database",
    "cache": "Optional caching solution",
    "queue": "Optional message queue"
  }},
  "system_components": [
    {{"name": "Component Name", "description": "What it does", "type": "service|gateway|worker|storage"}}
  ],
  "data_model": {{
    "entities": ["Entity1", "Entity2"],
    "relationships": "Description of relationships"
  }},
  "api_design": {{
    "style": "REST|GraphQL|gRPC",
    "versioning": "Versioning strategy",
    "authentication": "Auth method"
  }},
  "security": {{
    "auth": "Authentication method",
    "encryption": "Encryption approach",
    "compliance": ["Compliance requirements"]
  }},
  "infrastructure": {{
    "hosting": "Hosting solution",
    "database": "Database hosting",
    "caching": "Caching solution",
    "cdn": "Optional CDN"
  }}
}}

Make recommendations specific to "{project_name}" and its requirements.

Return ONLY valid JSON, no markdown formatting or explanation."""

        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}]
                )
            )

            content = response.content[0].text

            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                arch_design = json.loads(content.strip())
                logger.info("Successfully generated architecture design with Claude", project_name=project_name)
                return arch_design

            except json.JSONDecodeError as e:
                logger.error("Failed to parse Claude architecture response as JSON", error=str(e))
                return self._fallback_architecture_design(input_data)

        except Exception as e:
            logger.error("Claude API call failed for architecture", error=str(e))
            return self._fallback_architecture_design(input_data)

    def _fallback_product_design(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback product design when API is not available."""
        project_name = input_data.get('project_name', 'project')
        project_overview = input_data.get('project_overview', '')
        target_users = input_data.get('target_users', 'End users')

        return {
            "vision": f"To build {project_name} - {project_overview[:200]}{'...' if len(project_overview) > 200 else ''} Our goal is to deliver an exceptional solution for {target_users}.",
            "problem_statement": f"Based on the requirements: {project_overview[:300]}{'...' if len(project_overview) > 300 else ''}",
            "target_audience": target_users,
            "value_proposition": [
                "Purpose-built solution addressing specific user needs",
                "Intuitive user experience reducing learning curve",
                "Reliable performance and security",
                "Scalable architecture for growth"
            ],
            "goals": [
                {"goal": "Deliver MVP with core functionality", "type": "timeline", "priority": "high"},
                {"goal": "Achieve user satisfaction (NPS > 40)", "type": "satisfaction", "priority": "high"},
                {"goal": "Maintain 99.9% uptime", "type": "reliability", "priority": "critical"},
                {"goal": "Enable seamless onboarding", "type": "growth", "priority": "medium"}
            ],
            "personas": [
                {"name": "Primary User", "role": "End User", "age": "25-45", "description": "Main user of the application", "goals": ["Accomplish tasks efficiently"], "pain_points": ["Complex workflows"], "tech_comfort": "Medium"},
                {"name": "Power User", "role": "Advanced User", "age": "30-50", "description": "Experienced user with advanced needs", "goals": ["Maximize productivity"], "pain_points": ["Limited features"], "tech_comfort": "High"},
                {"name": "Administrator", "role": "Admin", "age": "30-55", "description": "Manages system and users", "goals": ["Maintain system"], "pain_points": ["Limited controls"], "tech_comfort": "High"}
            ],
            "user_journey": {
                "stages": [
                    {"stage": "Discovery", "touchpoints": ["Landing page"], "emotions": "Curious"},
                    {"stage": "Evaluation", "touchpoints": ["Features", "Pricing"], "emotions": "Interested"},
                    {"stage": "Signup", "touchpoints": ["Registration"], "emotions": "Hopeful"},
                    {"stage": "Onboarding", "touchpoints": ["Setup wizard"], "emotions": "Engaged"},
                    {"stage": "Active Use", "touchpoints": ["Core features"], "emotions": "Productive"},
                    {"stage": "Advocacy", "touchpoints": ["Referrals"], "emotions": "Satisfied"}
                ],
                "flow_diagram": "Discovery -> Evaluation -> Signup -> Onboarding -> Active Use -> Advocacy"
            },
            "epics": [
                {"id": "E001", "title": "User Authentication", "description": "Login, registration, password management", "priority": "P0", "story_points": 21},
                {"id": "E002", "title": "Core Functionality", "description": "Main features as described in overview", "priority": "P0", "story_points": 55},
                {"id": "E003", "title": "User Dashboard", "description": "Main interface and navigation", "priority": "P0", "story_points": 34},
                {"id": "E004", "title": "Settings & Preferences", "description": "User configuration", "priority": "P1", "story_points": 13},
                {"id": "E005", "title": "Admin Panel", "description": "Administration features", "priority": "P1", "story_points": 21}
            ],
            "user_stories": [
                {"id": "US001", "epic": "E001", "story": "As a user, I want to register so I can access the system", "acceptance_criteria": ["Email validation", "Password requirements"]},
                {"id": "US002", "epic": "E002", "story": "As a user, I want to use core features efficiently", "acceptance_criteria": ["Feature works correctly", "Good performance"]},
                {"id": "US003", "epic": "E003", "story": "As a user, I want a clear dashboard to see key information", "acceptance_criteria": ["Loads quickly", "Shows relevant data"]}
            ],
            "mvp_scope": {
                "included_epics": ["E001", "E002", "E003"],
                "excluded_epics": ["E004", "E005"],
                "total_story_points": 110,
                "rationale": "Focus on core functionality to validate product-market fit",
                "release_criteria": ["All P0 epics complete", "Core flows working", "Security review passed"]
            },
            "risks": [
                {"id": "R001", "description": "Technical complexity", "severity": "medium", "probability": "medium", "impact": "Delays", "mitigation": "Early prototyping"},
                {"id": "R002", "description": "User adoption", "severity": "high", "probability": "medium", "impact": "Lower usage", "mitigation": "Beta testing"},
                {"id": "R003", "description": "Security vulnerabilities", "severity": "critical", "probability": "low", "impact": "Data breach", "mitigation": "Security audits"}
            ],
            "success_metrics": [
                {"id": "M001", "metric": "Monthly Active Users", "target": "1,000+", "timeframe": "Month 3", "measurement": "Analytics"},
                {"id": "M002", "metric": "User Retention", "target": "60%", "timeframe": "Day 30", "measurement": "Cohort analysis"},
                {"id": "M003", "metric": "System Uptime", "target": "99.9%", "timeframe": "Ongoing", "measurement": "Monitoring"},
                {"id": "M004", "metric": "User Satisfaction", "target": "NPS > 40", "timeframe": "Quarterly", "measurement": "Surveys"}
            ],
            "competitive_analysis": {
                "competitors": ["Existing solutions"],
                "differentiators": ["Better UX", "Modern architecture", "Focused features"]
            }
        }

    def _fallback_architecture_design(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback architecture design when API is not available."""
        return {
            "tech_stack": {
                "backend": "FastAPI (Python)",
                "frontend": "React",
                "database": "PostgreSQL"
            },
            "system_components": [
                {"name": "API Server", "description": "Main backend service", "type": "service"},
                {"name": "Web App", "description": "Frontend application", "type": "service"},
                {"name": "Database", "description": "Primary data store", "type": "storage"}
            ],
            "data_model": {
                "entities": ["User", "Resource", "Activity"],
                "relationships": "Users have many Resources, Resources have Activity logs"
            },
            "api_design": {
                "style": "REST",
                "versioning": "URL-based (/api/v1)",
                "authentication": "JWT Bearer tokens"
            },
            "security": {
                "auth": "JWT with refresh tokens",
                "encryption": "AES-256 at rest, TLS in transit"
            },
            "infrastructure": {
                "hosting": "Cloud (AWS/GCP/Azure)",
                "database": "Managed PostgreSQL",
                "caching": "Redis"
            }
        }


# Global client instance
claude_client = ClaudeClient()


class OrchestrationService:
    """
    Orchestration service that uses Claude AI to generate
    contextual product and architecture designs.
    """

    def __init__(self):
        self.claude = claude_client

    async def start_workflow(
        self,
        project_id: str,
        mode: WorkflowMode,
        input_data: Dict[str, Any],
    ):
        """Start a new workflow for a project."""
        logger.info(
            "Starting workflow",
            project_id=project_id,
            mode=mode.value,
        )

        phases = DISCOVERY_PHASES if mode == WorkflowMode.DISCOVERY else DIRECT_PHASES

        async with async_session_maker() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                logger.error("Project not found", project_id=project_id)
                return

            # Update to executing
            project.status = ProjectStatus.EXECUTING
            project.current_phase = phases[1]
            await session.commit()

            logger.info("Workflow started", project_id=project_id, phase=phases[1])

            if mode == WorkflowMode.DISCOVERY:
                # Generate product design using Claude
                logger.info("Generating product design with AI", project_id=project_id)
                product_design = await self.claude.generate_product_design(input_data)

                project.status = ProjectStatus.AWAITING_APPROVAL
                project.current_phase = "product_design"
                project.product_design = product_design
                await session.commit()
                logger.info("Product design generated, awaiting approval", project_id=project_id)
            else:
                project.status = ProjectStatus.COMPLETED
                project.current_phase = "summary"
                await session.commit()
                logger.info("Direct mode workflow completed", project_id=project_id)

    async def resume_workflow(self, project_id: str):
        """Resume a paused workflow after approval."""
        logger.info("Resuming workflow", project_id=project_id)

        async with async_session_maker() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                return

            current_phase = project.current_phase
            phases = DISCOVERY_PHASES if project.mode == WorkflowMode.DISCOVERY else DIRECT_PHASES

            try:
                current_idx = phases.index(current_phase)
                next_phase = phases[current_idx + 1] if current_idx + 1 < len(phases) else "summary"
            except (ValueError, IndexError):
                next_phase = "summary"

            if next_phase == "architecture_design":
                project.status = ProjectStatus.EXECUTING
                project.current_phase = next_phase
                await session.commit()

                # Get input data from project_overview
                input_data = project.project_overview or {}
                product_design = project.product_design or {}

                # Generate architecture design using Claude
                logger.info("Generating architecture design with AI", project_id=project_id)
                arch_design = await self.claude.generate_architecture_design(input_data, product_design)

                project.status = ProjectStatus.AWAITING_APPROVAL
                project.architecture_design = arch_design
                await session.commit()
                logger.info("Architecture design generated, awaiting approval", project_id=project_id)

            elif next_phase == "code_generation":
                # Code generation phase - prepare for scaffolding
                project.status = ProjectStatus.EXECUTING
                project.current_phase = next_phase
                await session.commit()
                logger.info("Starting code_generation phase", project_id=project_id)

                # Brief pause then move to scaffolding
                await asyncio.sleep(1)
                project.current_phase = "scaffolding"
                await session.commit()

                # Run actual scaffolding
                logger.info("Starting scaffolding phase", project_id=project_id)
                scaffolder = ScaffoldingService()

                try:
                    scaffold_result = await scaffolder.scaffold_project(
                        project_name=project.name,
                        product_design=project.product_design or {},
                        architecture_design=project.architecture_design or {},
                    )

                    # Store scaffolding result
                    project.execution_progress = {
                        "scaffolding": scaffold_result,
                        "completed_at": asyncio.get_event_loop().time()
                    }

                    logger.info(
                        "Scaffolding complete",
                        project_id=project_id,
                        path=scaffold_result.get("project_path"),
                        files=scaffold_result.get("created_files", 0)
                    )

                except Exception as e:
                    logger.error("Scaffolding failed", project_id=project_id, error=str(e))
                    project.execution_progress = {
                        "scaffolding": {"error": str(e)},
                    }

                # Move to completed
                project.status = ProjectStatus.COMPLETED
                project.current_phase = "summary"
                await session.commit()
                logger.info("Workflow completed!", project_id=project_id)

            elif next_phase in ["quality", "scaffolding"]:
                # If we somehow get here directly, run scaffolding
                project.status = ProjectStatus.EXECUTING
                project.current_phase = "scaffolding"
                await session.commit()

                scaffolder = ScaffoldingService()
                try:
                    scaffold_result = await scaffolder.scaffold_project(
                        project_name=project.name,
                        product_design=project.product_design or {},
                        architecture_design=project.architecture_design or {},
                    )
                    project.execution_progress = {"scaffolding": scaffold_result}
                except Exception as e:
                    logger.error("Scaffolding failed", error=str(e))
                    project.execution_progress = {"scaffolding": {"error": str(e)}}

                project.status = ProjectStatus.COMPLETED
                project.current_phase = "summary"
                await session.commit()
                logger.info("Workflow completed!", project_id=project_id)

            elif next_phase == "summary":
                project.status = ProjectStatus.COMPLETED
                project.current_phase = "summary"
                await session.commit()
                logger.info("Workflow completed!", project_id=project_id)
            else:
                project.status = ProjectStatus.EXECUTING
                project.current_phase = next_phase
                await session.commit()

    async def get_progress(self, project_id: str) -> Dict[str, Any]:
        """Get workflow progress."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                return {"error": "Project not found"}

            phases = DISCOVERY_PHASES if project.mode == WorkflowMode.DISCOVERY else DIRECT_PHASES

            return {
                "project_id": project_id,
                "status": project.status.value,
                "current_phase": project.current_phase,
                "phases": phases,
                "completed_phases": phases[:phases.index(project.current_phase)] if project.current_phase in phases else [],
                "has_product_design": project.product_design is not None,
                "has_architecture": project.architecture_design is not None,
            }

    async def recover_interrupted_workflows(self):
        """
        Recover workflows that were interrupted (e.g., due to server restart).
        Projects stuck in EXECUTING status are reset to the last approval checkpoint.
        """
        logger.info("Checking for interrupted workflows...")

        async with async_session_maker() as session:
            # Find all projects stuck in EXECUTING status
            result = await session.execute(
                select(Project).where(Project.status == ProjectStatus.EXECUTING)
            )
            stuck_projects = result.scalars().all()

            if not stuck_projects:
                logger.info("No interrupted workflows found")
                return

            logger.warning(f"Found {len(stuck_projects)} interrupted workflow(s)")

            for project in stuck_projects:
                logger.info(
                    f"Recovering project",
                    project_id=project.id,
                    current_phase=project.current_phase,
                    project_name=project.name
                )

                # Determine recovery point based on current phase
                current_phase = project.current_phase

                if current_phase in ["product_design"]:
                    # Reset to input phase, need to regenerate product design
                    project.status = ProjectStatus.CREATED
                    project.current_phase = "input"
                    project.product_design = None
                    logger.info(f"Reset to input phase (will regenerate product design)")

                elif current_phase in ["architecture_design"]:
                    # Reset to awaiting approval for product_design
                    if project.product_design:
                        project.status = ProjectStatus.AWAITING_APPROVAL
                        project.current_phase = "product_design"
                        logger.info(f"Reset to product_design approval (product design preserved)")
                    else:
                        project.status = ProjectStatus.CREATED
                        project.current_phase = "input"
                        logger.info(f"Reset to input phase (no product design found)")

                elif current_phase in ["code_generation", "quality", "scaffolding"]:
                    # Reset to awaiting approval for architecture_design
                    if project.architecture_design:
                        project.status = ProjectStatus.AWAITING_APPROVAL
                        project.current_phase = "architecture_design"
                        logger.info(f"Reset to architecture_design approval (designs preserved)")
                    elif project.product_design:
                        project.status = ProjectStatus.AWAITING_APPROVAL
                        project.current_phase = "product_design"
                        logger.info(f"Reset to product_design approval")
                    else:
                        project.status = ProjectStatus.CREATED
                        project.current_phase = "input"
                        logger.info(f"Reset to input phase")

                else:
                    # Unknown phase, reset to beginning
                    project.status = ProjectStatus.CREATED
                    project.current_phase = "input"
                    logger.warning(f"Unknown phase {current_phase}, reset to input")

                await session.commit()
                logger.info(f"Project {project.id} recovered successfully")
