"""
Workflow definitions for Discovery Mode and Direct Mode.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class WorkflowMode(Enum):
    DISCOVERY = "discovery"
    DIRECT = "direct"


@dataclass
class Phase:
    """Workflow phase definition."""
    name: str
    display_name: str
    description: str
    requires_approval: bool = False
    execution_model: str = "sequential"  # sequential, parallel, dependency_graph
    agents: List[str] = field(default_factory=list)
    activation_rules: Optional[dict] = None


@dataclass
class WorkflowDefinition:
    """Base workflow definition."""
    name: str
    mode: WorkflowMode
    phases: List[Phase]

    def get_phase(self, name: str) -> Optional[Phase]:
        for phase in self.phases:
            if phase.name == name:
                return phase
        return None


class DiscoveryModeWorkflow(WorkflowDefinition):
    """
    Discovery Mode: 7 phases with AI-driven design.
    User provides project overview, AI designs architecture.
    """

    def __init__(self):
        super().__init__(
            name="AI Discovery Workflow",
            mode=WorkflowMode.DISCOVERY,
            phases=[
                Phase(
                    name="input",
                    display_name="Input",
                    description="Receive and validate project overview",
                    agents=["input_validator"],
                ),
                Phase(
                    name="product_design",
                    display_name="Product Design",
                    description="Generate product design from overview",
                    requires_approval=True,
                    agents=["po_agent"],
                ),
                Phase(
                    name="requirements",
                    display_name="Requirements",
                    description="Generate detailed requirements, epics, and user stories",
                    execution_model="parallel",
                    agents=["requirement_agent"],
                ),
                Phase(
                    name="architecture_design",
                    display_name="Architecture Design",
                    description="Design system architecture",
                    requires_approval=True,
                    execution_model="parallel",
                    agents=[
                        "fullstack_architect",
                        "backend_architect",
                        "frontend_architect",
                        "database_architect",
                        "infrastructure_architect",
                        "security_architect",
                        "ml_architect",
                        "ai_architect",
                    ],
                    activation_rules={"use_activation_matrix": True},
                ),
                Phase(
                    name="code_generation",
                    display_name="Code Generation",
                    description="Generate code from architecture",
                    execution_model="parallel",
                    agents=[
                        "fullstack_developer",
                        "backend_developer",
                        "frontend_developer",
                        "aiml_developer",
                    ],
                    activation_rules={"use_activation_matrix": True},
                ),
                Phase(
                    name="quality",
                    display_name="Quality & DevOps",
                    description="Generate tests, CI/CD, and documentation",
                    execution_model="parallel",
                    agents=[
                        "testing_agent",
                        "cicd_agent",
                        "documentation_agent",
                    ],
                ),
                Phase(
                    name="scaffolding",
                    display_name="Scaffolding",
                    description="Create project files and setup integrations",
                    execution_model="dependency_graph",
                    agents=[
                        "filesystem_scaffolder",
                        "git_provisioner",
                        "workflow_generator",
                        "jira_provisioner",
                    ],
                ),
                Phase(
                    name="summary",
                    display_name="Summary",
                    description="Generate final summary and next steps",
                    agents=["summary_reporter"],
                ),
            ],
        )


class DirectModeWorkflow(WorkflowDefinition):
    """
    Direct Mode: 5 phases for quick scaffolding.
    User specifies exact stack, minimal AI involvement.
    """

    def __init__(self):
        super().__init__(
            name="Direct Scaffolding Workflow",
            mode=WorkflowMode.DIRECT,
            phases=[
                Phase(
                    name="input",
                    display_name="Input",
                    description="Receive and validate project specification",
                    agents=["spec_validator"],
                ),
                Phase(
                    name="architecture_design",
                    display_name="Architecture",
                    description="Quick architecture setup",
                    execution_model="parallel",
                    agents=[
                        "infrastructure_architect",
                        "security_architect",
                    ],
                ),
                Phase(
                    name="scaffolding",
                    display_name="Scaffolding",
                    description="Create project files and setup integrations",
                    execution_model="dependency_graph",
                    agents=[
                        "filesystem_scaffolder",
                        "git_provisioner",
                        "workflow_generator",
                        "jira_provisioner",
                    ],
                ),
                Phase(
                    name="summary",
                    display_name="Summary",
                    description="Generate final summary",
                    agents=["summary_reporter"],
                ),
            ],
        )
