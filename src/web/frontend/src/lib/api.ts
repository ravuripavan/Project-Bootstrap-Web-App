import axios from 'axios';

// Use full backend URL for development
const API_BASE_URL = import.meta.env.DEV
  ? 'http://localhost:8000/api/v1'
  : '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Project {
  id: string;
  status: string;
  mode: string;
  current_phase: string;
  project_name: string;
  created_at: string;
  updated_at?: string;
  completed_at?: string;
}

export interface ProjectDetail extends Project {
  project_overview?: Record<string, unknown>;
  project_spec?: Record<string, unknown>;
  product_design?: Record<string, unknown>;
  architecture_design?: Record<string, unknown>;
}

export interface ProjectOverview {
  project_name: string;
  project_overview: string;
  target_users?: string;
  key_features?: string;
  constraints?: string;
  project_type_hint?: string;
}

export interface ProjectSpec {
  project_name: string;
  project_path: string;
  project_type: string;
  language_stack: string;
  include_repo: boolean;
  include_ci: boolean;
  include_jira: boolean;
}

// API functions
export const projectsApi = {
  list: async (status?: string) => {
    const params = status ? { status_filter: status } : {};
    const response = await api.get<{ projects: Project[]; total: number }>('/projects', { params });
    return response.data;
  },

  get: async (id: string) => {
    const response = await api.get<ProjectDetail>(`/projects/${id}`);
    return response.data;
  },

  create: async (data: ProjectOverview | ProjectSpec) => {
    const response = await api.post<Project>('/projects', data);
    return response.data;
  },

  approve: async (id: string, feedback?: string) => {
    const response = await api.post<Project>(`/projects/${id}/approve`, { feedback });
    return response.data;
  },

  reject: async (id: string, feedback: string) => {
    const response = await api.post<Project>(`/projects/${id}/reject`, { feedback });
    return response.data;
  },

  cancel: async (id: string) => {
    await api.delete(`/projects/${id}`);
  },

  getProgress: async (id: string) => {
    const response = await api.get(`/projects/${id}/progress`);
    return response.data;
  },
};

// Terminal API functions
export interface TerminalCommandRequest {
  agent: string;
  project_path: string;
  project_name: string;
  description?: string;
}

export interface TerminalCommandResponse {
  command: string;
  powershell_command: string;
  bash_command: string;
  agent: string;
  agent_command: string;
}

export interface Agent {
  id: string;
  name: string;
  command: string;
  description: string;
  category: string;
}

export interface QuickScaffoldRequest {
  project_name: string;
  project_path: string;
  project_overview: string;
}

export interface QuickScaffoldResponse {
  success: boolean;
  project_path: string;
  files_created: number;
  agents_count: number;
  message: string;
  git_branches: string[];
}

export interface LaunchTerminalRequest {
  agent: string;
  project_path: string;
  project_name: string;
  description?: string;
}

export interface LaunchTerminalResponse {
  success: boolean;
  message: string;
  command: string;
}

export interface AgentInfo {
  agent_id: string;
  name: string;
  description: string;
  model?: string;
  workflow: string[];
  tools: string[];
  file_path: string;
  content?: string;
}

// Project Status Types
export interface WorkflowPhase {
  phase: string;
  step: string;
  agent: string;
  status: string;
}

export interface DevelopmentStream {
  stream: string;
  module: string;
  agent: string;
  status: string;
  progress: string;
}

export interface ActiveAgent {
  agent: string;
  role: string;
  module: string;
  status: string;
}

export interface Blocker {
  issue: string;
  impact: string;
  resolution: string;
}

export interface ProjectStatus {
  project_name: string;
  project_path: string;
  current_phase: string;
  current_wave?: string;
  status: string;
  last_updated?: string;
  workflow_phases: WorkflowPhase[];
  development_streams: DevelopmentStream[];
  active_agents: ActiveAgent[];
  blockers: Blocker[];
  raw_content?: string;
}

export interface ScaffoldedProject {
  name: string;
  path: string;
  has_status: boolean;
  source?: string;
}

export interface ProjectPathsResponse {
  paths: string[];
  default_path: string;
}

export interface ProjectAgentInfo {
  name: string;
  file: string;
  valid: boolean;
  has_frontmatter: boolean;
  errors?: string[];
  warnings?: string[];
}

export interface AvailableAgent {
  name: string;
  command: string;
  file: string;
  has_frontmatter: boolean;
}

export interface ProjectAgentsResponse {
  project_path: string;
  valid: boolean;
  summary: {
    total_agents: number;
    valid_agents: number;
    agents_with_errors: number;
    agents_with_warnings: number;
  };
  available_agents: AvailableAgent[];
  errors: string[];
  warnings: string[];
  agent_details: ProjectAgentInfo[];
}

export const terminalApi = {
  generateCommand: async (data: TerminalCommandRequest) => {
    const response = await api.post<TerminalCommandResponse>('/terminal/command', data);
    return response.data;
  },

  listAgents: async () => {
    const response = await api.get<{ agents: Agent[] }>('/terminal/agents');
    return response.data;
  },

  scaffoldProject: async (data: QuickScaffoldRequest) => {
    const response = await api.post<QuickScaffoldResponse>('/terminal/scaffold', data);
    return response.data;
  },

  launchTerminal: async (data: LaunchTerminalRequest) => {
    const response = await api.post<LaunchTerminalResponse>('/terminal/launch', data);
    return response.data;
  },

  getAgentInfo: async (agentId: string, projectPath?: string) => {
    const params = projectPath ? { project_path: projectPath } : {};
    const response = await api.get<AgentInfo>(`/terminal/agent/${agentId}`, { params });
    return response.data;
  },

  getProjectStatus: async (projectName: string) => {
    const response = await api.get<ProjectStatus>(`/terminal/project-status/${projectName}`);
    return response.data;
  },

  listScaffoldedProjects: async () => {
    const response = await api.get<{ projects: ScaffoldedProject[] }>('/terminal/scaffolded-projects');
    return response.data;
  },

  getProjectPaths: async () => {
    const response = await api.get<ProjectPathsResponse>('/terminal/project-paths');
    return response.data;
  },

  addProjectPath: async (path: string) => {
    const response = await api.post<{ success: boolean; paths: string[] }>('/terminal/project-paths', { path });
    return response.data;
  },

  removeProjectPath: async (path: string) => {
    const response = await api.delete<{ success: boolean; paths: string[] }>('/terminal/project-paths', {
      params: { path }
    });
    return response.data;
  },

  scanPath: async (path: string) => {
    const response = await api.post<{ projects: ScaffoldedProject[]; path: string }>('/terminal/scan-path', { path });
    return response.data;
  },

  getProjectAgents: async (projectName: string) => {
    const response = await api.get<ProjectAgentsResponse>(`/terminal/validate-agents/${projectName}`);
    return response.data;
  },
};

export default api;
