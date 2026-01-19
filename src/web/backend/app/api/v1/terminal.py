from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import platform
import subprocess
import os
import json
from pathlib import Path

from app.services.scaffolding_service import ScaffoldingService

router = APIRouter()


class TerminalCommandRequest(BaseModel):
    agent: str
    project_path: str
    project_name: str
    description: Optional[str] = None


class TerminalCommandResponse(BaseModel):
    command: str
    powershell_command: str
    bash_command: str
    agent: str
    agent_command: str


AGENT_COMMANDS = {
    "orchestration": "/agent:orchestration",
    "po": "/agent:po",
    "requirement": "/agent:requirement",
    "fullstack-architect": "/agent:fullstack-architect",
    "backend-architect": "/agent:backend-architect",
    "frontend-architect": "/agent:frontend-architect",
    "database-architect": "/agent:database-architect",
    "infrastructure-architect": "/agent:infrastructure-architect",
    "security-architect": "/agent:security-architect",
    "developer": "/agent:developer",
    "fullstack-developer": "/agent:fullstack-developer",
    "backend-developer": "/agent:backend-developer",
    "frontend-developer": "/agent:frontend-developer",
    "testing": "/agent:testing",
    "cicd": "/agent:cicd",
    "documentation": "/agent:documentation",
    "expert": "/agent:expert",
    "healthcare-expert": "/agent:healthcare-expert",
    "finance-expert": "/agent:finance-expert",
    "ecommerce-expert": "/agent:ecommerce-expert",
}


@router.post("/command", response_model=TerminalCommandResponse)
async def generate_terminal_command(request: TerminalCommandRequest):
    """Generate terminal commands to launch Claude with a specific agent."""
    agent_cmd = AGENT_COMMANDS.get(request.agent, f"/agent:{request.agent}")

    # Build the prompt for the agent
    prompt_parts = [agent_cmd]
    if request.description:
        prompt_parts.append(request.description)
    prompt_parts.append(f"for {request.project_name}")

    prompt = " ".join(prompt_parts)

    # Windows PowerShell command
    powershell_cmd = f'cd "{request.project_path}"; claude "{prompt}"'

    # Bash command (for Git Bash, WSL, Linux, macOS)
    bash_cmd = f'cd "{request.project_path}" && claude "{prompt}"'

    # Default command based on platform
    is_windows = platform.system() == "Windows"
    default_cmd = powershell_cmd if is_windows else bash_cmd

    return TerminalCommandResponse(
        command=default_cmd,
        powershell_command=powershell_cmd,
        bash_command=bash_cmd,
        agent=request.agent,
        agent_command=agent_cmd,
    )


@router.get("/agents")
async def list_agents():
    """List all available agents with their commands."""
    agents = [
        {
            "id": "orchestration",
            "name": "Orchestration",
            "command": "/agent:orchestration",
            "description": "Master coordinator - runs full bootstrap workflow",
            "category": "core",
        },
        {
            "id": "po",
            "name": "Product Owner",
            "command": "/agent:po",
            "description": "Product design - vision, personas, epics, MVP scope",
            "category": "core",
        },
        {
            "id": "requirement",
            "name": "Requirements",
            "command": "/agent:requirement",
            "description": "Detailed requirements - user stories, acceptance criteria",
            "category": "core",
        },
        {
            "id": "fullstack-architect",
            "name": "Full-Stack Architect",
            "command": "/agent:fullstack-architect",
            "description": "End-to-end system design and tech stack selection",
            "category": "architect",
        },
        {
            "id": "backend-architect",
            "name": "Backend Architect",
            "command": "/agent:backend-architect",
            "description": "API design, microservices, database architecture",
            "category": "architect",
        },
        {
            "id": "frontend-architect",
            "name": "Frontend Architect",
            "command": "/agent:frontend-architect",
            "description": "UI architecture, component structure, state management",
            "category": "architect",
        },
        {
            "id": "developer",
            "name": "Developer",
            "command": "/agent:developer",
            "description": "Production-ready code generation",
            "category": "developer",
        },
        {
            "id": "backend-developer",
            "name": "Backend Developer",
            "command": "/agent:backend-developer",
            "description": "API implementation, services, database operations",
            "category": "developer",
        },
        {
            "id": "frontend-developer",
            "name": "Frontend Developer",
            "command": "/agent:frontend-developer",
            "description": "UI components, state management, testing",
            "category": "developer",
        },
        {
            "id": "testing",
            "name": "Testing",
            "command": "/agent:testing",
            "description": "Test suites - unit, integration, edge cases",
            "category": "support",
        },
        {
            "id": "cicd",
            "name": "CI/CD",
            "command": "/agent:cicd",
            "description": "DevOps pipelines - GitHub Actions, GitLab CI",
            "category": "support",
        },
        {
            "id": "documentation",
            "name": "Documentation",
            "command": "/agent:documentation",
            "description": "README, API docs, architecture documentation",
            "category": "support",
        },
    ]
    return {"agents": agents}


class QuickScaffoldRequest(BaseModel):
    project_name: str
    project_path: str
    project_overview: str


class QuickScaffoldResponse(BaseModel):
    success: bool
    project_path: str
    files_created: int
    agents_count: int
    message: str
    git_branches: list[str]


@router.post("/scaffold", response_model=QuickScaffoldResponse)
async def quick_scaffold_project(request: QuickScaffoldRequest):
    """
    Quick scaffold a project with minimal input.
    Creates project structure with agents, docs, and git setup.
    """
    try:
        # Create scaffolding service with custom output directory
        output_dir = Path(request.project_path).parent
        service = ScaffoldingService(base_output_dir=str(output_dir))

        # Create minimal product design from overview
        product_design = {
            "vision": request.project_overview,
            "goals": [{"goal": "Build " + request.project_name}],
            "target_audience": "Users",
            "value_proposition": ["Efficient solution"],
            "epics": [
                {
                    "id": "E001",
                    "title": "Core Features",
                    "description": "Implement core functionality",
                    "priority": "P1",
                    "story_points": 13,
                }
            ],
            "personas": [
                {
                    "name": "Primary User",
                    "role": "End User",
                    "description": "Primary user of the system",
                    "goals": ["Complete tasks efficiently"],
                    "pain_points": ["Current solutions are slow"],
                }
            ],
        }

        # Create minimal architecture design
        architecture_design = {
            "tech_stack": {
                "backend": "FastAPI (Python)",
                "frontend": "React + TypeScript",
                "database": "PostgreSQL",
                "cache": "Redis",
            },
            "system_components": [
                {"name": "API", "description": "Backend REST API"},
                {"name": "Web UI", "description": "Frontend web application"},
                {"name": "Database", "description": "Data persistence layer"},
            ],
            "data_model": {},
            "api_design": {"style": "REST", "versioning": "URL path"},
            "security": {"authentication": "JWT", "authorization": "RBAC"},
        }

        # Get project name from path
        project_name = Path(request.project_path).name
        if not project_name:
            project_name = request.project_name

        # Scaffold the project
        result = await service.scaffold_project(
            project_name=project_name,
            product_design=product_design,
            architecture_design=architecture_design,
        )

        return QuickScaffoldResponse(
            success=True,
            project_path=result["project_path"],
            files_created=result["created_files"],
            agents_count=result["agents_count"],
            message=f"Project '{project_name}' scaffolded successfully with {result['agents_count']} agents",
            git_branches=result.get("git", {}).get("branches", []),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class LaunchTerminalRequest(BaseModel):
    agent: str
    project_path: str
    project_name: str
    description: Optional[str] = None


class LaunchTerminalResponse(BaseModel):
    success: bool
    message: str
    command: str


class AgentInfoResponse(BaseModel):
    agent_id: str
    name: str
    description: str
    model: Optional[str] = None
    workflow: list[str]
    tools: list[str]
    file_path: str
    content: Optional[str] = None


@router.post("/launch", response_model=LaunchTerminalResponse)
async def launch_terminal(request: LaunchTerminalRequest):
    """
    Open a terminal window and execute Claude with the specified agent.
    Works on Windows (opens new CMD/PowerShell window).
    """
    try:
        # Build a prompt that tells Claude to read and follow the agent workflow
        agent_file = f".claude/agents/{request.agent}.md"

        prompt_parts = [
            f"Read the agent definition at {agent_file} and follow its workflow.",
        ]
        if request.description:
            prompt_parts.append(f"Task: {request.description} for {request.project_name}.")

        prompt = " ".join(prompt_parts)

        # Verify path exists
        project_path = Path(request.project_path)
        if not project_path.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Project path does not exist: {request.project_path}"
            )

        system = platform.system()

        if system == "Windows":
            # Use Windows Terminal if available, fallback to cmd
            # The command: open new window, cd to path, run claude
            claude_command = f'claude "{prompt}"'

            # Try to use Windows Terminal (wt) first, fallback to cmd
            try:
                # Check if Windows Terminal is available
                result = subprocess.run(
                    ["where", "wt"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    # Use Windows Terminal
                    subprocess.Popen(
                        ["wt", "-d", str(project_path), "cmd", "/k", claude_command],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    raise FileNotFoundError("wt not found")
            except (FileNotFoundError, subprocess.SubprocessError):
                # Fallback to cmd
                full_command = f'cd /d "{project_path}" && {claude_command}'
                subprocess.Popen(
                    ["cmd", "/c", "start", "cmd", "/k", full_command],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )

            return LaunchTerminalResponse(
                success=True,
                message=f"Terminal opened with {request.agent} agent workflow",
                command=claude_command,
            )

        elif system == "Darwin":  # macOS
            claude_command = f'claude "{prompt}"'
            # Use osascript to open Terminal
            script = f'''
            tell application "Terminal"
                activate
                do script "cd '{project_path}' && {claude_command}"
            end tell
            '''
            subprocess.Popen(["osascript", "-e", script])

            return LaunchTerminalResponse(
                success=True,
                message=f"Terminal opened with {request.agent} agent workflow",
                command=claude_command,
            )

        elif system == "Linux":
            claude_command = f'claude "{prompt}"'
            # Try common terminal emulators
            terminals = [
                ["gnome-terminal", "--", "bash", "-c", f"cd '{project_path}' && {claude_command}; exec bash"],
                ["konsole", "-e", "bash", "-c", f"cd '{project_path}' && {claude_command}; exec bash"],
                ["xterm", "-e", f"cd '{project_path}' && {claude_command}; exec bash"],
            ]

            launched = False
            for term_cmd in terminals:
                try:
                    subprocess.Popen(term_cmd)
                    launched = True
                    break
                except FileNotFoundError:
                    continue

            if not launched:
                raise HTTPException(
                    status_code=500,
                    detail="No supported terminal emulator found (tried gnome-terminal, konsole, xterm)"
                )

            return LaunchTerminalResponse(
                success=True,
                message=f"Terminal opened with {request.agent} agent workflow",
                command=claude_command,
            )

        else:
            raise HTTPException(
                status_code=500,
                detail=f"Unsupported operating system: {system}"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


import re
from urllib.parse import unquote


@router.get("/agent/{agent_id}", response_model=AgentInfoResponse, tags=["agents"])
async def get_agent_info(agent_id: str, project_path: Optional[str] = None):
    """
    Get detailed information about an agent by reading its definition file.
    """
    try:
        # Decode URL-encoded path
        decoded_path = unquote(project_path) if project_path else None

        # Determine where to look for the agent file
        agent_file = None
        search_paths = []

        if decoded_path:
            # Try project-specific agent
            project_agent = Path(decoded_path) / ".claude" / "agents" / f"{agent_id}.md"
            search_paths.append(str(project_agent))
            if project_agent.exists():
                agent_file = project_agent

        if not agent_file:
            # Fallback to .claude/agents directory (relative to this file)
            # Go up from: app/api/v1/terminal.py -> v1 -> api -> app -> backend -> web -> src -> PROJECT ROOT
            project_root = Path(__file__).parent.parent.parent.parent.parent.parent.parent
            claude_agents = project_root / ".claude" / "agents" / f"{agent_id}.md"
            search_paths.append(str(claude_agents))
            if claude_agents.exists():
                agent_file = claude_agents

        if not agent_file:
            # Also try templates/agents as another fallback
            templates_agent = project_root / "templates" / "agents" / f"{agent_id}.md"
            search_paths.append(str(templates_agent))
            if templates_agent.exists():
                agent_file = templates_agent

        if not agent_file:
            raise HTTPException(
                status_code=404,
                detail=f"Agent '{agent_id}' not found. Searched: {', '.join(search_paths)}"
            )

        content = agent_file.read_text(encoding='utf-8')

        # Parse the agent definition file
        name = agent_id.replace("-", " ").title()
        description = ""
        model = None
        workflow = []
        tools = []

        # Extract name from first heading
        name_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if name_match:
            name = name_match.group(1).strip()

        # Extract description (first paragraph after heading)
        desc_match = re.search(r'^#[^\n]+\n+([^\n#]+)', content, re.MULTILINE)
        if desc_match:
            description = desc_match.group(1).strip()

        # Extract model if specified
        model_match = re.search(r'(?:model|Model)[:\s]+([^\n]+)', content, re.IGNORECASE)
        if model_match:
            model = model_match.group(1).strip()

        # Extract workflow steps (look for numbered lists or ## Workflow section)
        workflow_section = re.search(r'##\s*Workflow[^\n]*\n((?:[^\n#]+\n?)+)', content, re.IGNORECASE)
        if workflow_section:
            steps = re.findall(r'^\s*[\d\-\*]+[\.\)]\s*(.+)$', workflow_section.group(1), re.MULTILINE)
            workflow = [s.strip() for s in steps if s.strip()]

        if not workflow:
            # Fallback: look for any numbered list
            steps = re.findall(r'^\s*\d+[\.\)]\s*(.+)$', content, re.MULTILINE)
            workflow = [s.strip() for s in steps[:10] if s.strip()]  # Limit to first 10

        # Extract tools section
        tools_section = re.search(r'##\s*Tools[^\n]*\n((?:[^\n#]+\n?)+)', content, re.IGNORECASE)
        if tools_section:
            tool_items = re.findall(r'^\s*[\-\*]\s*(.+)$', tools_section.group(1), re.MULTILINE)
            tools = [t.strip() for t in tool_items if t.strip()]

        return AgentInfoResponse(
            agent_id=agent_id,
            name=name,
            description=description,
            model=model,
            workflow=workflow,
            tools=tools,
            file_path=str(agent_file),
            content=content[:2000] if len(content) > 2000 else content,  # Truncate if too long
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ProjectStatusResponse(BaseModel):
    project_name: str
    project_path: str
    current_phase: str
    current_wave: Optional[str] = None
    status: str
    last_updated: Optional[str] = None
    workflow_phases: list[dict] = []
    development_streams: list[dict] = []
    active_agents: list[dict] = []
    blockers: list[dict] = []
    raw_content: Optional[str] = None


@router.get("/project-status/{project_name}", response_model=ProjectStatusResponse)
async def get_project_status(project_name: str):
    """
    Read project status from the scaffolded project's status.md file.
    Searches in default and custom project paths.
    """
    try:
        # Search for the project in all paths
        status_file = None

        # Check default path first
        default_path = Path.home() / "bootstrapped-projects" / project_name
        default_status = default_path / "docs" / "project-status" / "status.md"
        if default_status.exists():
            status_file = default_status

        # Check custom paths if not found in default
        if status_file is None:
            custom_paths = load_custom_paths()
            for custom_path in custom_paths:
                potential_status = Path(custom_path) / project_name / "docs" / "project-status" / "status.md"
                if potential_status.exists():
                    status_file = potential_status
                    break

        if status_file is None:
            raise HTTPException(
                status_code=404,
                detail=f"Status file not found for project '{project_name}'"
            )

        content = status_file.read_text(encoding='utf-8')

        # Parse the status file
        current_phase = ""
        current_wave = ""
        status = ""
        last_updated = ""
        workflow_phases = []
        development_streams = []
        active_agents = []
        blockers = []

        # Parse Current State table - support both formats:
        # 1. **Current Phase** | value (old format)
        # 2. | **Current Phase** | value | (table format)
        state_match = re.search(
            r'\|\s*\*\*Current Phase\*\*\s*\|\s*([^|\n]+)',
            content
        ) or re.search(
            r'\*\*Current Phase\*\*\s*\|\s*([^\n|]+)',
            content
        )
        if state_match:
            current_phase = state_match.group(1).strip()

        # Also try to get Current Step if Current Wave not found
        wave_match = re.search(
            r'\|\s*\*\*Current (?:Wave|Step)\*\*\s*\|\s*([^|\n]+)',
            content
        ) or re.search(
            r'\*\*Current (?:Wave|Step)\*\*\s*\|\s*([^\n|]+)',
            content
        )
        if wave_match:
            current_wave = wave_match.group(1).strip()

        status_match = re.search(
            r'\|\s*\*\*Status\*\*\s*\|\s*([^|\n]+)',
            content
        ) or re.search(
            r'\*\*Status\*\*\s*\|\s*([^\n|]+)',
            content
        )
        if status_match:
            status = status_match.group(1).strip()

        # If no status found, try to derive from Phase Tracking table
        if not status:
            # Look for the current phase's status in Phase Tracking
            phase_status_match = re.search(
                r'\|\s*' + re.escape(current_phase) + r'\s*\|\s*\*\*([^*]+)\*\*',
                content
            )
            if phase_status_match:
                status = phase_status_match.group(1).strip()
            else:
                # Try to find any IN PROGRESS phase
                in_progress_match = re.search(
                    r'\|[^|]+\|\s*\*\*IN PROGRESS\*\*',
                    content
                )
                if in_progress_match:
                    status = "IN PROGRESS"

        updated_match = re.search(
            r'\|\s*\*\*Last Updated\*\*\s*\|\s*([^|\n]+)',
            content
        ) or re.search(
            r'\*\*Last Updated\*\*\s*\|\s*([^\n|]+)',
            content
        )
        if updated_match:
            last_updated = updated_match.group(1).strip()

        # Parse Workflow Phases/Progress table (match both headers)
        workflow_section = re.search(
            r'## Workflow (?:Phases|Progress)\s*\n+\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n?)+)',
            content
        )
        if workflow_section:
            rows = workflow_section.group(1).strip().split('\n')
            for row in rows:
                if '|' in row:
                    cols = [c.strip() for c in row.split('|')[1:-1]]
                    if len(cols) >= 4:
                        workflow_phases.append({
                            "phase": cols[0],
                            "step": cols[1],
                            "agent": cols[2],
                            "status": cols[3]
                        })

        # Also try Phase Tracking table format (Phase | Status | Started | Completed | Notes)
        if not workflow_phases:
            phase_tracking = re.search(
                r'## Phase Tracking\s*\n+\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n?)+)',
                content
            )
            if phase_tracking:
                rows = phase_tracking.group(1).strip().split('\n')
                for row in rows:
                    if '|' in row:
                        cols = [c.strip() for c in row.split('|')[1:-1]]
                        if len(cols) >= 2:
                            # Remove ** markers from status
                            phase_status = cols[1].replace('**', '').strip() if len(cols) > 1 else ""
                            workflow_phases.append({
                                "phase": cols[0],
                                "step": cols[0],  # Use phase name as step for display
                                "agent": "",
                                "status": phase_status
                            })

        # Parse Sub-Phase tracking tables (Phase 2 Sub-Phases, etc.)
        if not development_streams:
            subphase_tracking = re.search(
                r'### Phase \d+ Sub-Phases[^\n]*\n+\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n?)+)',
                content
            )
            if subphase_tracking:
                rows = subphase_tracking.group(1).strip().split('\n')
                for row in rows:
                    if '|' in row:
                        cols = [c.strip() for c in row.split('|')[1:-1]]
                        if len(cols) >= 3:
                            # Sub-Phase | Module | Status | ...
                            development_streams.append({
                                "stream": cols[0],
                                "module": cols[1],
                                "agent": "",
                                "progress": "",
                                "status": cols[2]
                            })

        # Also parse step tracking tables (Phase X Step Tracking)
        step_tracking = re.search(
            r'## Phase \d+ Step Tracking\s*\n+\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n?)+)',
            content
        )
        if step_tracking:
            rows = step_tracking.group(1).strip().split('\n')
            for row in rows:
                if '|' in row:
                    cols = [c.strip() for c in row.split('|')[1:-1]]
                    if len(cols) >= 3:
                        active_agents.append({
                            "agent": cols[1] if len(cols) > 1 else "",
                            "role": cols[0] if len(cols) > 0 else "",
                            "module": cols[3] if len(cols) > 3 else "",
                            "status": cols[2] if len(cols) > 2 else ""
                        })

        # Parse Development Streams table - support multiple header formats
        streams_section = re.search(
            r'## Development Streams\s*\n+\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n?)+)',
            content
        ) or re.search(
            r'### Parallel Development Streams\s*\n\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n)+)',
            content
        )
        if streams_section:
            rows = streams_section.group(1).strip().split('\n')
            for row in rows:
                if '|' in row:
                    cols = [c.strip() for c in row.split('|')[1:-1]]
                    if len(cols) >= 5:
                        # Handle both column orders:
                        # New: Stream | Module | Agent | Progress | Status
                        # Old: stream | module | agent | status | progress
                        development_streams.append({
                            "stream": cols[0],
                            "module": cols[1],
                            "agent": cols[2],
                            "progress": cols[3],
                            "status": cols[4]
                        })
                    elif len(cols) >= 4:
                        development_streams.append({
                            "stream": cols[0],
                            "module": cols[1],
                            "agent": cols[2],
                            "progress": "",
                            "status": cols[3]
                        })

        # Parse Active Agents table
        agents_section = re.search(
            r'## Active Agents\s*\n\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n)+)',
            content
        )
        if agents_section:
            rows = agents_section.group(1).strip().split('\n')
            for row in rows:
                cols = [c.strip() for c in row.split('|')[1:-1]]
                if len(cols) >= 4:
                    active_agents.append({
                        "agent": cols[0],
                        "role": cols[1],
                        "module": cols[2],
                        "status": cols[3]
                    })

        # Extract active agents from development streams (those with IN PROGRESS status)
        if not active_agents and development_streams:
            for stream in development_streams:
                if 'IN PROGRESS' in stream.get('status', '').upper() or 'PROGRESS' in stream.get('status', ''):
                    active_agents.append({
                        "agent": stream.get('agent', ''),
                        "role": "Developer",
                        "module": stream.get('module', ''),
                        "status": "Active"
                    })

        # Parse Blockers table
        blockers_section = re.search(
            r'## Blockers\s*\n\s*\|[^\n]+\n\s*\|[-|\s]+\n((?:\|[^\n]+\n)+)',
            content
        )
        if blockers_section:
            rows = blockers_section.group(1).strip().split('\n')
            for row in rows:
                cols = [c.strip() for c in row.split('|')[1:-1]]
                if len(cols) >= 3:
                    blockers.append({
                        "issue": cols[0],
                        "impact": cols[1],
                        "resolution": cols[2]
                    })

        # Derive project path from status file (status_file is at project/docs/project-status/status.md)
        project_path = status_file.parent.parent.parent

        return ProjectStatusResponse(
            project_name=project_name,
            project_path=str(project_path),
            current_phase=current_phase,
            current_wave=current_wave,
            status=status,
            last_updated=last_updated,
            workflow_phases=workflow_phases,
            development_streams=development_streams,
            active_agents=active_agents,
            blockers=blockers,
            raw_content=content[:5000] if len(content) > 5000 else content
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Path to store custom project paths
CUSTOM_PATHS_FILE = Path.home() / ".bootstrap-web-app" / "custom_paths.json"


def load_custom_paths() -> list[str]:
    """Load custom project paths from config file."""
    if not CUSTOM_PATHS_FILE.exists():
        return []
    try:
        with open(CUSTOM_PATHS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("paths", [])
    except Exception:
        return []


def save_custom_paths(paths: list[str]):
    """Save custom project paths to config file."""
    CUSTOM_PATHS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CUSTOM_PATHS_FILE, 'w') as f:
        json.dump({"paths": paths}, f, indent=2)


def scan_directory_for_projects(base_path: Path) -> list[dict]:
    """Scan a directory for projects (directories with .claude folder or status.md)."""
    projects = []
    if not base_path.exists() or not base_path.is_dir():
        return projects

    for item in base_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check for project indicators
            status_file = item / "docs" / "project-status" / "status.md"
            claude_dir = item / ".claude"
            has_status = status_file.exists()
            is_project = has_status or claude_dir.exists()

            if is_project:
                projects.append({
                    "name": item.name,
                    "path": str(item),
                    "has_status": has_status,
                    "source": str(base_path)
                })

    return projects


class CustomPathRequest(BaseModel):
    path: str


class CustomPathsResponse(BaseModel):
    paths: list[str]
    default_path: str


@router.get("/project-paths", response_model=CustomPathsResponse)
async def get_project_paths():
    """Get all configured project paths including default."""
    default_path = str(Path.home() / "bootstrapped-projects")
    custom_paths = load_custom_paths()
    return CustomPathsResponse(
        paths=custom_paths,
        default_path=default_path
    )


@router.post("/project-paths")
async def add_project_path(request: CustomPathRequest):
    """Add a custom project path."""
    path = request.path.strip()

    # Validate path exists
    if not Path(path).exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")

    if not Path(path).is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

    # Load existing paths and add new one
    paths = load_custom_paths()
    if path not in paths:
        paths.append(path)
        save_custom_paths(paths)

    return {"success": True, "paths": paths}


@router.delete("/project-paths")
async def remove_project_path(path: str):
    """Remove a custom project path."""
    paths = load_custom_paths()
    if path in paths:
        paths.remove(path)
        save_custom_paths(paths)
    return {"success": True, "paths": paths}


@router.get("/scaffolded-projects")
async def list_scaffolded_projects(include_custom: bool = True):
    """
    List all scaffolded projects from default and custom directories.
    """
    try:
        all_projects = []
        seen_paths = set()

        # Scan default directory
        default_path = Path.home() / "bootstrapped-projects"
        for project in scan_directory_for_projects(default_path):
            if project["path"] not in seen_paths:
                seen_paths.add(project["path"])
                all_projects.append(project)

        # Scan custom directories
        if include_custom:
            custom_paths = load_custom_paths()
            for custom_path in custom_paths:
                for project in scan_directory_for_projects(Path(custom_path)):
                    if project["path"] not in seen_paths:
                        seen_paths.add(project["path"])
                        all_projects.append(project)

        return {"projects": all_projects}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-path")
async def scan_path_for_projects(request: CustomPathRequest):
    """Scan a specific path for projects without adding it to saved paths."""
    path = request.path.strip()

    if not Path(path).exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")

    if not Path(path).is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

    projects = scan_directory_for_projects(Path(path))
    return {"projects": projects, "path": path}


# Agent Validation Endpoints

class ValidateAgentsRequest(BaseModel):
    project_path: str


@router.post("/validate-agents")
async def validate_project_agents(request: ValidateAgentsRequest):
    """
    Validate all agents in a project's .claude/agents/ directory.

    Checks for:
    - File readability
    - No literal \\n strings (common template error)
    - Valid frontmatter structure
    - Required frontmatter fields
    - Non-empty content

    Returns list of available agents that can be used with CLI.
    """
    path = request.project_path.strip()

    if not Path(path).exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")

    if not Path(path).is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

    service = ScaffoldingService()
    result = service.validate_project_agents(path)
    return result


@router.post("/fix-agents")
async def fix_project_agents(request: ValidateAgentsRequest):
    """
    Validate and auto-fix common agent errors in a project.

    Automatically fixes:
    - Literal \\n strings converted to actual newlines
    - Literal \\t strings converted to actual tabs

    Returns fix results and updated validation status.
    """
    path = request.project_path.strip()

    if not Path(path).exists():
        raise HTTPException(status_code=400, detail=f"Path does not exist: {path}")

    if not Path(path).is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {path}")

    service = ScaffoldingService()
    result = service.fix_project_agents(path)
    return result


@router.get("/validate-agents/{project_name}")
async def validate_scaffolded_project_agents(project_name: str):
    """
    Validate agents for a scaffolded project by name.

    Looks in default and custom project paths for the project.
    """
    # Search in default path first
    default_path = Path.home() / "bootstrapped-projects" / project_name
    if default_path.exists():
        service = ScaffoldingService()
        return service.validate_project_agents(str(default_path))

    # Search in custom paths
    custom_paths = load_custom_paths()
    for custom_path in custom_paths:
        project_path = Path(custom_path) / project_name
        if project_path.exists():
            service = ScaffoldingService()
            return service.validate_project_agents(str(project_path))

    raise HTTPException(status_code=404, detail=f"Project not found: {project_name}")
