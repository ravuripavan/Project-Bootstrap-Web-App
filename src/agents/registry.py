"""
Agent registry - loads and manages agent definitions.
"""
from pathlib import Path
from typing import Dict, Type, Optional, List
import yaml
import structlog

from src.agents.base import BaseAgent

logger = structlog.get_logger()


class AgentDefinition:
    """Parsed agent definition from .claude/agents/*.md"""

    def __init__(
        self,
        name: str,
        description: str,
        model: str = "sonnet",
        tools: List[str] = None,
        instructions: str = "",
    ):
        self.name = name
        self.description = description
        self.model = model
        self.tools = tools or []
        self.instructions = instructions

    def __repr__(self) -> str:
        return f"<AgentDefinition(name={self.name}, model={self.model})>"


class AgentRegistry:
    """
    Registry that loads agent definitions and manages implementations.

    Agents are defined in .claude/agents/*.md files with YAML frontmatter.
    """

    def __init__(self, agents_dir: Path = None):
        self.agents_dir = agents_dir or Path(".claude/agents")
        self._definitions: Dict[str, AgentDefinition] = {}
        self._implementations: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}

        if self.agents_dir.exists():
            self._load_definitions()

    def _load_definitions(self) -> None:
        """Load agent definitions from .claude/agents/*.md files."""
        logger.info("Loading agent definitions", path=str(self.agents_dir))

        for md_file in self.agents_dir.glob("*.md"):
            try:
                definition = self._parse_agent_md(md_file)
                if definition:
                    self._definitions[definition.name] = definition
                    logger.debug("Loaded agent", name=definition.name)
            except Exception as e:
                logger.error("Failed to load agent", file=str(md_file), error=str(e))

        logger.info("Loaded agents", count=len(self._definitions))

    def _parse_agent_md(self, path: Path) -> Optional[AgentDefinition]:
        """
        Parse agent markdown file with YAML frontmatter.

        Format:
        ---
        name: agent-name
        description: Brief description
        model: sonnet
        tools:
          - Read
          - Write
        ---

        # Agent Instructions
        ...
        """
        content = path.read_text(encoding="utf-8")

        # Split by --- markers
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        # Parse YAML frontmatter
        try:
            frontmatter = yaml.safe_load(parts[1])
            if not frontmatter or "name" not in frontmatter:
                return None

            return AgentDefinition(
                name=frontmatter.get("name"),
                description=frontmatter.get("description", ""),
                model=frontmatter.get("model", "sonnet"),
                tools=frontmatter.get("tools", []),
                instructions=parts[2].strip(),
            )
        except yaml.YAMLError as e:
            logger.error("Invalid YAML in agent file", file=str(path), error=str(e))
            return None

    def register_implementation(
        self,
        agent_id: str,
        implementation: Type[BaseAgent],
    ) -> None:
        """
        Register a concrete agent implementation.

        Args:
            agent_id: Agent identifier (matches definition name)
            implementation: BaseAgent subclass
        """
        self._implementations[agent_id] = implementation
        logger.debug("Registered implementation", agent_id=agent_id)

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an instantiated agent by ID.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent instance or None if not found
        """
        # Return cached instance if exists
        if agent_id in self._instances:
            return self._instances[agent_id]

        # Create new instance from implementation
        if agent_id in self._implementations:
            instance = self._implementations[agent_id]()
            self._instances[agent_id] = instance
            return instance

        return None

    def get_definition(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get agent definition by ID."""
        return self._definitions.get(agent_id)

    def get_all_definitions(self) -> List[AgentDefinition]:
        """Get all loaded agent definitions."""
        return list(self._definitions.values())

    def get_agents_by_category(self, category: str) -> List[str]:
        """Get agent IDs for a category."""
        # Map category to agent name patterns
        CATEGORY_PATTERNS = {
            "architecture": ["architect"],
            "development": ["developer"],
            "support": ["testing", "cicd", "documentation"],
            "design": ["po", "requirement"],
            "domain_expert": ["expert"],
        }

        patterns = CATEGORY_PATTERNS.get(category, [])
        agents = []

        for name in self._definitions.keys():
            for pattern in patterns:
                if pattern in name:
                    agents.append(name)
                    break

        return agents

    def has_agent(self, agent_id: str) -> bool:
        """Check if an agent is registered."""
        return agent_id in self._definitions or agent_id in self._implementations
