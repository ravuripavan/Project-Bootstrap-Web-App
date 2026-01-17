"""
Filesystem scaffolder agent - creates project directory structure.
"""
from pathlib import Path
from typing import Dict, Any, List
import shutil

from src.agents.base import BaseAgent, AgentInput, AgentOutput


class FilesystemScaffolderAgent(BaseAgent):
    """
    Creates project directory structure and files.
    """

    agent_id = "filesystem_scaffolder"
    agent_name = "Filesystem Scaffolder"
    category = "scaffolding"

    def get_activation_rules(self) -> Dict[str, Any]:
        return {"project_types": ["all"]}

    async def execute(self, input_data: AgentInput) -> AgentOutput:
        """Create project directory structure."""
        self._start_timer()

        context = input_data.context
        project_path = Path(context.get("project_path", "."))
        project_type = context.get("project_type", "web-app")
        language_stack = context.get("language_stack", "python")

        try:
            # Create base directory
            project_path.mkdir(parents=True, exist_ok=True)

            # Get directory structure based on project type
            structure = self._get_directory_structure(project_type, language_stack)

            # Create directories and files
            created_files = []
            for item in structure:
                path = project_path / item["path"]

                if item["type"] == "directory":
                    path.mkdir(parents=True, exist_ok=True)
                elif item["type"] == "file":
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(item.get("content", ""))
                    created_files.append(str(path))

            return AgentOutput.success(
                output={
                    "project_path": str(project_path),
                    "created_files": created_files,
                    "structure": structure,
                },
                artifacts=[{"type": "directory", "path": str(project_path)}],
                messages=[f"Created project structure at {project_path}"],
                duration_ms=self._get_duration_ms(),
            )

        except Exception as e:
            return AgentOutput.failure(
                errors=[f"Failed to create directory structure: {str(e)}"],
                duration_ms=self._get_duration_ms(),
            )

    def _get_directory_structure(
        self,
        project_type: str,
        language_stack: str,
    ) -> List[Dict[str, Any]]:
        """Get directory structure for project type."""

        # Common directories
        common = [
            {"path": "docs", "type": "directory"},
            {"path": "tests", "type": "directory"},
            {"path": ".github/workflows", "type": "directory"},
            {"path": "README.md", "type": "file", "content": "# Project\n"},
            {"path": ".gitignore", "type": "file", "content": self._get_gitignore(language_stack)},
        ]

        # Language-specific
        if language_stack == "python":
            common.extend([
                {"path": "src", "type": "directory"},
                {"path": "src/__init__.py", "type": "file", "content": ""},
                {"path": "pyproject.toml", "type": "file", "content": self._get_pyproject()},
                {"path": "requirements.txt", "type": "file", "content": ""},
            ])
        elif language_stack == "node":
            common.extend([
                {"path": "src", "type": "directory"},
                {"path": "package.json", "type": "file", "content": "{}"},
            ])

        return common

    def _get_gitignore(self, language_stack: str) -> str:
        """Get .gitignore content."""
        common = """
# IDE
.idea/
.vscode/
*.swp

# Environment
.env
.env.local

# OS
.DS_Store
Thumbs.db
"""

        if language_stack == "python":
            return common + """
# Python
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
"""
        elif language_stack == "node":
            return common + """
# Node
node_modules/
npm-debug.log
yarn-error.log
.next/
dist/
build/
"""
        return common

    def _get_pyproject(self) -> str:
        """Get pyproject.toml template."""
        return """[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]
"""
