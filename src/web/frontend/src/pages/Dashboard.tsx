import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus, Rocket, Zap, Clock, CheckCircle, AlertCircle,
  Bot, Users, Code, Layers, Shield, FileText, TestTube, Settings,
  ChevronRight, Activity, ChevronDown, ChevronUp, FolderPlus, Trash2, X, Folder
} from 'lucide-react';
import { Card, Badge, Progress, Spinner } from '@/components/ui';
import { projectsApi, terminalApi, Project, Agent, ProjectStatus, ScaffoldedProject } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import ScaffoldWorkflow from '@/components/ScaffoldWorkflow';

const statusConfig: Record<string, { color: string; icon: typeof Clock; label: string }> = {
  pending: { color: 'info', icon: Clock, label: 'Pending' },
  executing: { color: 'warning', icon: Zap, label: 'Running' },
  awaiting_approval: { color: 'purple', icon: AlertCircle, label: 'Waiting' },
  completed: { color: 'success', icon: CheckCircle, label: 'Complete' },
  failed: { color: 'error', icon: AlertCircle, label: 'Failed' },
};

const agentCategoryConfig: Record<string, { icon: typeof Bot; color: string; label: string }> = {
  core: { icon: Layers, color: 'primary', label: 'Core Agents' },
  architect: { icon: Settings, color: 'accent', label: 'Architect Agents' },
  developer: { icon: Code, color: 'success', label: 'Developer Agents' },
  support: { icon: Shield, color: 'warning', label: 'Support Agents' },
};

const phases = [
  { id: 'input', name: 'Input' },
  { id: 'product_design', name: 'Product Design' },
  { id: 'architecture_design', name: 'Architecture' },
  { id: 'code_generation', name: 'Code Generation' },
  { id: 'quality', name: 'Quality & DevOps' },
  { id: 'scaffolding', name: 'Scaffolding' },
  { id: 'summary', name: 'Summary' },
];

export default function Dashboard() {
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [selectedScaffoldedProject, setSelectedScaffoldedProject] = useState<string | null>(null);
  const [showProjectStatus, setShowProjectStatus] = useState(true);
  const [showAgents, setShowAgents] = useState(false);
  const [showRecentProjects, setShowRecentProjects] = useState(false);
  const [showPathManager, setShowPathManager] = useState(false);
  const [newPath, setNewPath] = useState('');
  const [pathError, setPathError] = useState<string | null>(null);

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
    refetchInterval: 5000, // Refresh every 5 seconds for live updates
  });

  const { data: agentsData, isLoading: agentsLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => terminalApi.listAgents(),
  });

  // Fetch scaffolded projects
  const { data: scaffoldedData } = useQuery({
    queryKey: ['scaffolded-projects'],
    queryFn: () => terminalApi.listScaffoldedProjects(),
    refetchInterval: 10000,
  });

  // Fetch project paths
  const { data: pathsData } = useQuery({
    queryKey: ['project-paths'],
    queryFn: () => terminalApi.getProjectPaths(),
  });

  // Add path mutation
  const addPathMutation = useMutation({
    mutationFn: (path: string) => terminalApi.addProjectPath(path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-paths'] });
      queryClient.invalidateQueries({ queryKey: ['scaffolded-projects'] });
      setNewPath('');
      setPathError(null);
    },
    onError: (error: any) => {
      setPathError(error.response?.data?.detail || 'Failed to add path');
    },
  });

  // Remove path mutation
  const removePathMutation = useMutation({
    mutationFn: (path: string) => terminalApi.removeProjectPath(path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['project-paths'] });
      queryClient.invalidateQueries({ queryKey: ['scaffolded-projects'] });
    },
  });

  // Fetch project status for selected scaffolded project
  const { data: projectStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['project-status', selectedScaffoldedProject],
    queryFn: () => terminalApi.getProjectStatus(selectedScaffoldedProject!),
    enabled: !!selectedScaffoldedProject,
    refetchInterval: 5000,
  });

  // Auto-select first scaffolded project with status
  useEffect(() => {
    if (scaffoldedData?.projects.length && !selectedScaffoldedProject) {
      const withStatus = scaffoldedData.projects.find(p => p.has_status);
      if (withStatus) {
        setSelectedScaffoldedProject(withStatus.name);
      }
    }
  }, [scaffoldedData?.projects, selectedScaffoldedProject]);

  // Auto-select first project or active project when data loads
  useEffect(() => {
    if (data?.projects.length && !selectedProjectId) {
      // Prefer active project, fallback to first
      const activeProject = data.projects.find(
        p => p.status === 'executing' || p.status === 'awaiting_approval'
      );
      setSelectedProjectId(activeProject?.id || data.projects[0]?.id || null);
    }
  }, [data?.projects, selectedProjectId]);

  // Get selected project from list
  const selectedProject = data?.projects.find(p => p.id === selectedProjectId);

  // Group agents by category
  const agentsByCategory = agentsData?.agents.reduce((acc, agent) => {
    const category = agent.category || 'core';
    if (!acc[category]) acc[category] = [];
    acc[category].push(agent);
    return acc;
  }, {} as Record<string, Agent[]>) || {};

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-card p-8 relative overflow-hidden"
      >
        <div className="absolute inset-0 animated-gradient opacity-10" />
        <div className="relative">
          <h1 className="text-3xl font-bold mb-2">
            <span className="gradient-text">Create New Project</span>
          </h1>
          <p className="text-dark-400 mb-6 max-w-xl">
            Let AI design your architecture or specify your exact stack.
            Get a production-ready project in minutes.
          </p>

          <div className="flex gap-4">
            <Link to="/new?mode=discovery">
              <Card hover glow className="p-6 w-64">
                <div className="w-12 h-12 rounded-xl bg-primary-500/20 flex items-center justify-center mb-4">
                  <Rocket className="w-6 h-6 text-primary-400" />
                </div>
                <h3 className="font-semibold text-lg mb-1">Discovery Mode</h3>
                <p className="text-sm text-dark-400">AI designs your architecture</p>
              </Card>
            </Link>

            <Link to="/new?mode=direct">
              <Card hover glow className="p-6 w-64">
                <div className="w-12 h-12 rounded-xl bg-accent-500/20 flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-accent-400" />
                </div>
                <h3 className="font-semibold text-lg mb-1">Direct Mode</h3>
                <p className="text-sm text-dark-400">You specify the stack</p>
              </Card>
            </Link>
          </div>
        </div>
      </motion.div>

      {/* Scaffold Workflow Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <ScaffoldWorkflow />
      </motion.div>

      {/* Scaffolded Project Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
      >
        <Card className="border-primary-500/30 bg-gradient-to-r from-primary-500/5 to-accent-500/5">
          {/* Header with Dropdown */}
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => setShowProjectStatus(!showProjectStatus)}
          >
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-lg bg-primary-500/20 flex items-center justify-center ${showProjectStatus ? 'animate-pulse' : ''}`}>
                <Activity className="w-4 h-4 text-primary-400" />
              </div>
              <div>
                <h2 className="text-sm font-semibold flex items-center gap-2">
                  Project Status
                  {showProjectStatus ? (
                    <ChevronUp className="w-4 h-4 text-dark-500" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-dark-500" />
                  )}
                </h2>
                <p className="text-xs text-dark-400">
                  {scaffoldedData?.projects.length || 0} projects from {(pathsData?.paths.length || 0) + 1} locations
                </p>
              </div>
            </div>

            {/* Scaffolded Project Dropdown and Settings */}
            <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
              <div className="relative">
                <select
                  value={selectedScaffoldedProject || ''}
                  onChange={(e) => setSelectedScaffoldedProject(e.target.value)}
                  className="appearance-none bg-dark-700 border border-dark-600 rounded-lg px-3 py-1.5 pr-8 text-dark-100 text-xs focus:outline-none focus:border-primary-500 cursor-pointer min-w-[150px]"
                >
                  <option value="">Select project...</option>
                  {scaffoldedData?.projects.map((project) => (
                    <option key={project.path} value={project.name}>
                      {project.name} {project.has_status ? '✓' : ''}
                    </option>
                  ))}
                </select>
                <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3 h-3 text-dark-400 pointer-events-none" />
              </div>
              <button
                onClick={() => setShowPathManager(!showPathManager)}
                className={`p-1.5 rounded-lg transition-colors ${showPathManager ? 'bg-primary-500/20 text-primary-400' : 'bg-dark-700 text-dark-400 hover:text-dark-200'}`}
                title="Manage project paths"
              >
                <FolderPlus className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Path Manager Panel */}
          <AnimatePresence>
            {showPathManager && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-4 p-4 bg-dark-800/50 rounded-lg border border-dark-600">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="text-sm font-semibold text-dark-200">Project Paths</h3>
                    <button
                      onClick={() => setShowPathManager(false)}
                      className="text-dark-500 hover:text-dark-300"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Add new path */}
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={newPath}
                      onChange={(e) => {
                        setNewPath(e.target.value);
                        setPathError(null);
                      }}
                      placeholder="Enter directory path (e.g., C:\Projects)"
                      className="flex-1 bg-dark-700 border border-dark-600 rounded-lg px-3 py-2 text-sm text-dark-100 placeholder-dark-500 focus:outline-none focus:border-primary-500"
                    />
                    <button
                      onClick={() => newPath && addPathMutation.mutate(newPath)}
                      disabled={!newPath || addPathMutation.isPending}
                      className="px-3 py-2 bg-primary-500/20 text-primary-400 rounded-lg text-sm font-medium hover:bg-primary-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                    >
                      {addPathMutation.isPending ? <Spinner size="sm" /> : <Plus className="w-4 h-4" />}
                      Add
                    </button>
                  </div>

                  {pathError && (
                    <p className="text-xs text-red-400 mb-2">{pathError}</p>
                  )}

                  {/* Paths list */}
                  <div className="space-y-2">
                    {/* Default path */}
                    <div className="flex items-center justify-between bg-dark-700/50 rounded-lg px-3 py-2">
                      <div className="flex items-center gap-2">
                        <Folder className="w-4 h-4 text-primary-400" />
                        <span className="text-sm text-dark-200">{pathsData?.default_path || '~/bootstrapped-projects'}</span>
                        <Badge variant="info" size="sm">Default</Badge>
                      </div>
                    </div>

                    {/* Custom paths */}
                    {pathsData?.paths.map((path) => (
                      <div key={path} className="flex items-center justify-between bg-dark-700/50 rounded-lg px-3 py-2">
                        <div className="flex items-center gap-2">
                          <Folder className="w-4 h-4 text-accent-400" />
                          <span className="text-sm text-dark-200">{path}</span>
                          <Badge variant="default" size="sm">Custom</Badge>
                        </div>
                        <button
                          onClick={() => removePathMutation.mutate(path)}
                          disabled={removePathMutation.isPending}
                          className="text-dark-500 hover:text-red-400 transition-colors"
                          title="Remove path"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}

                    {(!pathsData?.paths || pathsData.paths.length === 0) && (
                      <p className="text-xs text-dark-500 text-center py-2">No custom paths added yet</p>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {showProjectStatus && (
            <div className="mt-4">
              {!selectedScaffoldedProject ? (
                <div className="text-center py-6">
                  <p className="text-dark-400">Select a project to view status</p>
                </div>
              ) : statusLoading ? (
                <div className="flex justify-center py-8">
                  <Spinner />
                </div>
              ) : projectStatus ? (
                <>
                  {/* Status Overview */}
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                      <div className="bg-dark-800/50 rounded-lg p-4">
                        <p className="text-xs text-dark-500 uppercase mb-1">Current Phase</p>
                        <p className="font-semibold text-primary-400">{projectStatus.current_phase}</p>
                      </div>
                      <div className="bg-dark-800/50 rounded-lg p-4">
                        <p className="text-xs text-dark-500 uppercase mb-1">Status</p>
                        <Badge variant={projectStatus.status.includes('PROGRESS') ? 'warning' : 'info'}>
                          {projectStatus.status}
                        </Badge>
                      </div>
                      <div className="bg-dark-800/50 rounded-lg p-4">
                        <p className="text-xs text-dark-500 uppercase mb-1">Current Wave</p>
                        <p className="font-medium text-dark-200 text-sm">{projectStatus.current_wave || 'N/A'}</p>
                      </div>
                      <div className="bg-dark-800/50 rounded-lg p-4">
                        <p className="text-xs text-dark-500 uppercase mb-1">Last Updated</p>
                        <p className="font-medium text-dark-200">{projectStatus.last_updated || 'N/A'}</p>
                      </div>
                    </div>

                    {/* Development Streams */}
                    {projectStatus.development_streams.length > 0 && (
                      <div className="mb-4">
                        <h3 className="text-sm font-semibold text-dark-300 mb-2">Development Streams</h3>
                        <div className="space-y-2">
                          {projectStatus.development_streams.map((stream, i) => (
                            <div key={i} className="flex items-center justify-between bg-dark-800/50 rounded-lg p-3">
                              <div className="flex items-center gap-3">
                                <span className="text-xs font-mono text-dark-500">{stream.stream}</span>
                                <span className="text-sm text-dark-200">{stream.module}</span>
                                <Badge variant="default" size="sm">{stream.agent}</Badge>
                              </div>
                              <div className="flex items-center gap-3">
                                <span className="text-xs text-dark-400">{stream.progress}</span>
                                <Badge
                                  variant={stream.status.includes('Progress') ? 'warning' : stream.status.includes('Waiting') ? 'info' : 'default'}
                                  size="sm"
                                >
                                  {stream.status}
                                </Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Active Agents */}
                    {projectStatus.active_agents.length > 0 && (
                      <div className="mb-4">
                        <h3 className="text-sm font-semibold text-dark-300 mb-2">Active Agents</h3>
                        <div className="flex flex-wrap gap-2">
                          {projectStatus.active_agents.map((agent, i) => (
                            <div key={i} className="flex items-center gap-2 bg-dark-800/50 rounded-lg px-3 py-2">
                              <Bot className="w-4 h-4 text-primary-400" />
                              <span className="text-sm text-dark-200">{agent.agent}</span>
                              <span className="text-xs text-dark-500">({agent.module})</span>
                              <Badge
                                variant={agent.status === 'Active' || agent.status.includes('Progress') ? 'success' : 'default'}
                                size="sm"
                              >
                                {agent.status}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Workflow Phases Progress */}
                    {projectStatus.workflow_phases.length > 0 && (
                      <div className="mb-4">
                        <h3 className="text-sm font-semibold text-dark-300 mb-2">Workflow Progress</h3>
                        <div className="flex flex-wrap gap-1">
                          {projectStatus.workflow_phases.map((phase, i) => (
                            <div
                              key={i}
                              className={`px-2 py-1 rounded text-xs ${
                                phase.status.includes('COMPLETE') ? 'bg-emerald-500/20 text-emerald-400' :
                                phase.status.includes('PROGRESS') || phase.status.includes('STARTING') ? 'bg-primary-500/20 text-primary-400' :
                                'bg-dark-700 text-dark-500'
                              }`}
                              title={`${phase.step}: ${phase.agent} - ${phase.status}`}
                            >
                              {phase.step}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Blockers */}
                    {projectStatus.blockers.length > 0 && (
                      <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <AlertCircle className="w-4 h-4 text-amber-400" />
                          <span className="text-sm font-semibold text-amber-200">Blockers</span>
                        </div>
                        {projectStatus.blockers.map((blocker, i) => (
                          <div key={i} className="text-sm text-amber-100">
                            <span className="font-medium">{blocker.issue}</span>
                            <span className="text-amber-300"> → {blocker.resolution}</span>
                          </div>
                        ))}
                      </div>
                    )}
                </>
              ) : (
                <div className="text-center py-6">
                  <p className="text-dark-400">No status data available for this project</p>
                </div>
              )}
            </div>
          )}
        </Card>
      </motion.div>

      {/* Available Agents - Collapsible */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <Card className="border-dark-600">
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => setShowAgents(!showAgents)}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-accent-500/20 flex items-center justify-center">
                <Bot className="w-4 h-4 text-accent-400" />
              </div>
              <div>
                <h2 className="text-sm font-semibold flex items-center gap-2">
                  Available Agents
                  {showAgents ? (
                    <ChevronUp className="w-4 h-4 text-dark-500" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-dark-500" />
                  )}
                </h2>
                <p className="text-xs text-dark-400">{agentsData?.agents.length || 0} agents ready</p>
              </div>
            </div>
          </div>

          {showAgents && (
            <div className="mt-4">
              {agentsLoading ? (
                <div className="flex justify-center py-4">
                  <Spinner />
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {Object.entries(agentCategoryConfig).map(([category, config]) => {
                    const agents = agentsByCategory[category] || [];
                    if (agents.length === 0) return null;
                    const CategoryIcon = config.icon;

                    return (
                      <div key={category} className="bg-dark-800/30 rounded-lg p-2">
                        <div className="flex items-center gap-2 mb-2">
                          <div className={`w-6 h-6 rounded bg-${config.color}-500/20 flex items-center justify-center`}>
                            <CategoryIcon className={`w-3 h-3 text-${config.color}-400`} />
                          </div>
                          <span className="text-xs font-medium text-dark-300">{config.label}</span>
                          <span className="text-xs text-dark-500">({agents.length})</span>
                        </div>
                        <div className="space-y-1">
                          {agents.slice(0, 3).map((agent) => (
                            <div
                              key={agent.id}
                              className="text-xs text-dark-400 truncate pl-8"
                              title={agent.description}
                            >
                              {agent.name}
                            </div>
                          ))}
                          {agents.length > 3 && (
                            <div className="text-xs text-dark-500 pl-8">+{agents.length - 3} more</div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </Card>
      </motion.div>

      {/* Projects List - Collapsible */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.25 }}
      >
        <Card className="border-dark-600">
          <div
            className="flex items-center justify-between cursor-pointer"
            onClick={() => setShowRecentProjects(!showRecentProjects)}
          >
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-dark-700 flex items-center justify-center">
                <Rocket className="w-4 h-4 text-dark-400" />
              </div>
              <div>
                <h2 className="text-sm font-semibold flex items-center gap-2">
                  Recent Projects
                  {showRecentProjects ? (
                    <ChevronUp className="w-4 h-4 text-dark-500" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-dark-500" />
                  )}
                </h2>
                <p className="text-xs text-dark-400">{data?.projects.length || 0} projects</p>
              </div>
            </div>
            <Link to="/new" onClick={(e) => e.stopPropagation()}>
              <button className="flex items-center gap-1 text-primary-400 hover:text-primary-300 transition-colors text-xs">
                <Plus className="w-3 h-3" />
                New
              </button>
            </Link>
          </div>

          {showRecentProjects && (
            <div className="mt-4">
              {isLoading ? (
                <div className="flex justify-center py-4">
                  <Spinner />
                </div>
              ) : data?.projects.length === 0 ? (
                <p className="text-dark-400 text-sm text-center py-4">No projects yet</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {data?.projects.map((project, i) => (
                    <ProjectCard key={project.id} project={project} index={i} />
                  ))}
                </div>
              )}
            </div>
          )}
        </Card>
      </motion.div>
    </div>
  );
}

function ProjectCard({ project, index }: { project: Project; index: number }) {
  const config = statusConfig[project.status] || statusConfig.pending;
  const StatusIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Link to={`/project/${project.id}`}>
        <Card hover className="h-full">
          <div className="flex items-start justify-between mb-4">
            <h3 className="font-semibold text-lg truncate">{project.project_name}</h3>
            <Badge variant={config.color as any}>{config.label}</Badge>
          </div>

          <div className="flex items-center gap-2 text-sm text-dark-400 mb-4">
            <StatusIcon className="w-4 h-4" />
            <span className="capitalize">{project.current_phase || 'Starting'}</span>
          </div>

          {project.status === 'executing' && (
            <Progress value={50} variant="gradient" className="mb-4" />
          )}

          <div className="flex items-center justify-between text-xs text-dark-500">
            <span className="capitalize">{project.mode} mode</span>
            <span>{formatDate(project.created_at)}</span>
          </div>
        </Card>
      </Link>
    </motion.div>
  );
}
