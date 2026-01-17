/**
 * Project Bootstrap - Data Models
 * TypeScript interfaces for all core data structures
 */

// =============================================================================
// Enums
// =============================================================================

export enum ProjectType {
  WebApp = 'web-app',
  Api = 'api',
  Library = 'library',
  Cli = 'cli',
  Monorepo = 'monorepo',
}

export enum LanguageStack {
  Python = 'python',
  Node = 'node',
  Java = 'java',
  Go = 'go',
  Rust = 'rust',
  Dotnet = 'dotnet',
}

export enum CiProvider {
  GithubActions = 'github-actions',
  GitlabCi = 'gitlab-ci',
  AzurePipelines = 'azure-pipelines',
}

export enum VcsProvider {
  Github = 'github',
  Gitlab = 'gitlab',
  Bitbucket = 'bitbucket',
}

export enum JiraProjectType {
  Scrum = 'scrum',
  Kanban = 'kanban',
  Basic = 'basic',
}

export enum ProjectStatus {
  Pending = 'pending',
  InProgress = 'in_progress',
  Completed = 'completed',
  Failed = 'failed',
}

export enum AgentStatus {
  Success = 'success',
  Failure = 'failure',
  Warning = 'warning',
  Skipped = 'skipped',
}

// =============================================================================
// Configuration Types
// =============================================================================

export interface VcsConfig {
  visibility: 'public' | 'private';
  create_remote: boolean;
  default_branch?: string;
}

export interface JiraConfig {
  key_prefix: string;
  project_type: JiraProjectType;
}

// =============================================================================
// Core Input Types
// =============================================================================

/**
 * OrchestrationSpec - Raw input from the web app
 * This is the initial user input before normalization
 */
export interface OrchestrationSpec {
  project_name: string;
  project_path: string;
  project_type: ProjectType;
  language_stack: LanguageStack;
  include_repo: boolean;
  include_ci: boolean;
  include_jira: boolean;
  ci_provider?: CiProvider;
  vcs_provider?: VcsProvider;
  vcs_config?: VcsConfig;
  jira_config?: JiraConfig;
  framework?: string;
  description?: string;
}

/**
 * ProjectSpec - Normalized specification after validation
 * This is what agents receive for execution
 */
export interface ProjectSpec extends OrchestrationSpec {
  // Computed/derived fields added during normalization
  full_path: string;           // Resolved absolute path
  template_id?: string;        // Selected template identifier
  created_at: string;          // ISO timestamp
}

// =============================================================================
// Template Types
// =============================================================================

export interface TemplateFile {
  path: string;                // Relative path within project
  template: string;            // Template content or reference
  executable?: boolean;        // Set executable permission
}

export interface TemplateDirectory {
  path: string;
  gitkeep?: boolean;           // Create .gitkeep for empty dirs
}

export interface TemplateBundle {
  id: string;
  name: string;
  description: string;
  project_type: ProjectType;
  language_stack: LanguageStack;
  frameworks: string[];
  directories: TemplateDirectory[];
  files: TemplateFile[];
  dependencies?: Record<string, string>;
  dev_dependencies?: Record<string, string>;
  scripts?: Record<string, string>;
}

// =============================================================================
// Plan Types
// =============================================================================

export interface PlanStep {
  id: string;
  agent: string;
  description: string;
  depends_on: string[];
  when?: string;               // Conditional expression
  input: Record<string, unknown>;
  output_key: string;
}

export interface PlanPhase {
  name: string;
  execution_model?: 'sequential' | 'dependency_graph';
  steps: PlanStep[];
}

export interface ExecutionPlan {
  id: string;
  project_spec: ProjectSpec;
  template_bundle: TemplateBundle;
  phases: PlanPhase[];
  created_at: string;
}

// =============================================================================
// Execution Types
// =============================================================================

export interface AgentInput {
  project_spec: ProjectSpec;
  plan_step: PlanStep;
  context: ExecutionContext;
}

export interface AgentOutput {
  status: AgentStatus;
  output: Record<string, unknown>;
  errors?: string[];
  warnings?: string[];
  duration_ms: number;
}

export interface ExecutionContext {
  plan: ExecutionPlan;
  results: Record<string, AgentOutput>;  // step_id -> output
  dry_run: boolean;
}

// =============================================================================
// Agent-Specific Output Types
// =============================================================================

export interface FilesystemResult {
  directories_created: string[];
  files_created: string[];
  bytes_written: number;
}

export interface GitResult {
  local_repo_path: string;
  remote_url?: string;
  default_branch: string;
  initial_commit_sha?: string;
}

export interface WorkflowResult {
  workflows_generated: string[];
  ci_provider: CiProvider;
}

export interface JiraResult {
  project_key: string;
  project_url: string;
  epics_created: string[];
  issues_created: string[];
}

export interface SummaryResult {
  project_name: string;
  local_path: string;
  repo_url?: string;
  jira_url?: string;
  ci_configured: boolean;
  files_created: number;
  directories_created: number;
  next_steps: string[];
}

// =============================================================================
// Orchestration Result Types
// =============================================================================

export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warning' | 'error';
  agent?: string;
  phase?: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface OrchestrationResult {
  id: string;
  status: ProjectStatus;
  project_spec: ProjectSpec;
  plan: ExecutionPlan;
  results: {
    filesystem_result?: FilesystemResult;
    git_result?: GitResult;
    workflow_result?: WorkflowResult;
    jira_result?: JiraResult;
    summary: SummaryResult;
  };
  execution_log: LogEntry[];
  started_at: string;
  completed_at?: string;
  error?: string;
}

// =============================================================================
// API Types
// =============================================================================

export interface ApiError {
  error: string;
  message: string;
  request_id: string;
  details?: Record<string, unknown>;
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// =============================================================================
// WebSocket Types
// =============================================================================

export type WebSocketMessageType =
  | 'connected'
  | 'phase_started'
  | 'step_started'
  | 'step_completed'
  | 'phase_completed'
  | 'progress'
  | 'log'
  | 'completed'
  | 'error';

export interface WebSocketMessage {
  type: WebSocketMessageType;
  timestamp: string;
  data: {
    phase?: string;
    step?: string;
    agent?: string;
    status?: AgentStatus;
    message?: string;
    progress_percent?: number;
    result?: Record<string, unknown>;
    error?: string;
  };
}

// =============================================================================
// Integration Types
// =============================================================================

export interface IntegrationCredentials {
  provider: VcsProvider | 'jira';
  access_token: string;
  refresh_token?: string;
  expires_at?: string;
  scopes: string[];
  username?: string;
}

export interface IntegrationStatus {
  provider: string;
  connected: boolean;
  username?: string;
  scopes?: string[];
  expires_at?: string;
}

// =============================================================================
// Agent Registry Types
// =============================================================================

export interface AgentDefinition {
  id: string;
  name: string;
  role: string;
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
}

export interface AgentRegistry {
  agents: AgentDefinition[];
  capabilities: Record<string, string>;  // capability -> agent_id
}
