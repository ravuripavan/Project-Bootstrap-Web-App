from enum import Enum

class WorkflowMode(str, Enum):
    DISCOVERY = "discovery"
    DIRECT = "direct"

class ProjectStatus(str, Enum):
    PENDING = "pending"
    INPUT_RECEIVED = "input_received"
    DESIGNING = "designing"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProjectType(str, Enum):
    WEB_APP = "web-app"
    API = "api"
    LIBRARY = "library"
    CLI = "cli"
    MONOREPO = "monorepo"
    ML_PROJECT = "ml-project"
    AI_APP = "ai-app"
    FULL_PLATFORM = "full-platform"

class LanguageStack(str, Enum):
    PYTHON = "python"
    NODE = "node"
    JAVA = "java"
    GO = "go"
    RUST = "rust"
    DOTNET = "dotnet"
    MULTI = "multi"

class AgentCategory(str, Enum):
    ORCHESTRATION = "orchestration"
    DESIGN = "design"
    ARCHITECTURE = "architecture"
    DEVELOPMENT = "development"
    SUPPORT = "support"
    SCAFFOLDING = "scaffolding"
    DOMAIN_EXPERT = "domain_expert"

class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class PhaseStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"

class CIProvider(str, Enum):
    GITHUB_ACTIONS = "github-actions"
    GITLAB_CI = "gitlab-ci"
    AZURE_PIPELINES = "azure-pipelines"

class VCSProvider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"
