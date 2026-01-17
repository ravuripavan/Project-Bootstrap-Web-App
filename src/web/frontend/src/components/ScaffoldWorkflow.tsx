import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Play,
  Lightbulb,
  FileText,
  Layout,
  Code,
  TestTube,
  Settings,
  BookOpen,
  Copy,
  Check,
  Terminal,
  ArrowRight,
  Sparkles,
  FolderOpen,
  ChevronDown,
  ChevronUp,
  Rocket,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Loader2,
  X,
  Square,
  CheckCircle2,
  Circle,
} from 'lucide-react';
import { Card, Button, Badge, Input, Textarea, toast } from '@/components/ui';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/Dialog';
import { terminalApi, AgentInfo } from '@/lib/api';

interface WorkflowPhase {
  id: string;
  name: string;
  description: string;
  icon: React.ElementType;
  agent: string;
  agentCommand: string;
  color: string;
  details: string[];
}

type SessionStatus = 'running' | 'completed' | 'stopped';

interface AgentSession {
  id: string;
  phase: WorkflowPhase;
  command: string;
  timestamp: string;
  projectPath: string;
  projectName: string;
  agentInfo?: AgentInfo;
  status: SessionStatus;
}

const SESSIONS_STORAGE_KEY = 'scaffold-agent-sessions';

// Helper to serialize sessions (icons can't be stored)
const serializeSessions = (sessions: AgentSession[]): string => {
  return JSON.stringify(sessions.map(s => ({
    ...s,
    phase: { ...s.phase, icon: s.phase.id }, // Store ID instead of icon
  })));
};

// Helper to deserialize sessions
const deserializeSessions = (json: string): AgentSession[] => {
  try {
    const parsed = JSON.parse(json);
    return parsed.map((s: any) => {
      const phase = workflowPhases.find(p => p.id === s.phase.id) || workflowPhases[0];
      return {
        ...s,
        phase: { ...s.phase, icon: phase.icon },
        status: s.status || 'running', // Default to running for old sessions
      };
    });
  } catch {
    return [];
  }
};

const workflowPhases: WorkflowPhase[] = [
  {
    id: 'discovery',
    name: 'Discovery',
    description: 'Product design from user overview',
    icon: Lightbulb,
    agent: 'po',
    agentCommand: '/agent:po',
    color: 'from-yellow-500 to-orange-500',
    details: [
      'Vision & problem statement',
      'User personas',
      'High-level epics',
      'MVP scope definition',
    ],
  },
  {
    id: 'requirements',
    name: 'Requirements',
    description: 'Generate detailed requirements',
    icon: FileText,
    agent: 'requirement',
    agentCommand: '/agent:requirement',
    color: 'from-blue-500 to-cyan-500',
    details: [
      'Detailed epics with story points',
      'User stories (INVEST format)',
      'Acceptance criteria',
      'Sprint recommendations',
    ],
  },
  {
    id: 'architecture',
    name: 'Architecture',
    description: 'System design & tech stack',
    icon: Layout,
    agent: 'fullstack-architect',
    agentCommand: '/agent:fullstack-architect',
    color: 'from-purple-500 to-pink-500',
    details: [
      'Architecture diagrams',
      'Technology stack selection',
      'Component breakdown',
      'API design',
    ],
  },
  {
    id: 'implementation',
    name: 'Implementation',
    description: 'Code generation',
    icon: Code,
    agent: 'developer',
    agentCommand: '/agent:developer',
    color: 'from-green-500 to-emerald-500',
    details: [
      'Production-ready code',
      'Best practices applied',
      'Error handling',
      'Database models',
    ],
  },
  {
    id: 'testing',
    name: 'Testing',
    description: 'Test suites & QA',
    icon: TestTube,
    agent: 'testing',
    agentCommand: '/agent:testing',
    color: 'from-red-500 to-rose-500',
    details: [
      'Unit tests',
      'Integration tests',
      'Edge case coverage',
      'Test fixtures',
    ],
  },
  {
    id: 'cicd',
    name: 'CI/CD',
    description: 'DevOps pipelines',
    icon: Settings,
    agent: 'cicd',
    agentCommand: '/agent:cicd',
    color: 'from-indigo-500 to-violet-500',
    details: [
      'GitHub Actions / GitLab CI',
      'Build & deploy pipelines',
      'Environment configs',
      'Docker setup',
    ],
  },
  {
    id: 'documentation',
    name: 'Documentation',
    description: 'README & API docs',
    icon: BookOpen,
    agent: 'documentation',
    agentCommand: '/agent:documentation',
    color: 'from-teal-500 to-cyan-500',
    details: [
      'README.md',
      'API documentation',
      'Architecture docs',
      'Setup guides',
    ],
  },
];

export default function ScaffoldWorkflow() {
  const [selectedPhase, setSelectedPhase] = useState<WorkflowPhase | null>(null);
  const [copied, setCopied] = useState<'powershell' | 'bash' | null>(null);
  const [projectName, setProjectName] = useState('');
  const [projectPath, setProjectPath] = useState('');
  const [projectOverview, setProjectOverview] = useState('');
  const [showConfig, setShowConfig] = useState(true);
  const [isScaffolding, setIsScaffolding] = useState(false);
  const [scaffoldResult, setScaffoldResult] = useState<{
    success: boolean;
    message: string;
    path?: string;
    filesCreated?: number;
    agentsCount?: number;
  } | null>(null);

  const getCommands = (phase: WorkflowPhase) => {
    const path = projectPath || 'C:\\path\\to\\your\\project';
    const name = projectName || 'project';
    const agentFile = `.claude/agents/${phase.agent}.md`;
    const prompt = `Read the agent definition at ${agentFile} and follow its workflow. Task: ${phase.description} for ${name}.`;

    return {
      powershell: `cd "${path}"; claude "${prompt}"`,
      bash: `cd "${path.replace(/\\/g, '/')}" && claude "${prompt}"`,
    };
  };

  const copyToClipboard = async (text: string, type: 'powershell' | 'bash') => {
    await navigator.clipboard.writeText(text);
    setCopied(type);
    setTimeout(() => setCopied(null), 2000);
  };

  const openTerminal = (phase: WorkflowPhase) => {
    setSelectedPhase(phase);
  };

  const [isLaunching, setIsLaunching] = useState(false);
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [isLoadingAgentInfo, setIsLoadingAgentInfo] = useState<string | null>(null); // session ID being loaded
  const [agentInfoErrors, setAgentInfoErrors] = useState<Record<string, string>>({});

  // Load sessions from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(SESSIONS_STORAGE_KEY);
    if (stored) {
      setSessions(deserializeSessions(stored));
    }
  }, []);

  // Save sessions to localStorage when they change
  useEffect(() => {
    if (sessions.length > 0) {
      localStorage.setItem(SESSIONS_STORAGE_KEY, serializeSessions(sessions));
    } else {
      localStorage.removeItem(SESSIONS_STORAGE_KEY);
    }
  }, [sessions]);

  const clearSession = (sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId));
    setAgentInfoErrors(prev => {
      const next = { ...prev };
      delete next[sessionId];
      return next;
    });
  };

  const clearAllSessions = () => {
    setSessions([]);
    setAgentInfoErrors({});
  };

  const updateSessionStatus = (sessionId: string, newStatus: SessionStatus) => {
    setSessions(prev => {
      const updated = prev.map(s => {
        if (s.id === sessionId) {
          return { ...s, status: newStatus };
        }
        return s;
      });
      localStorage.setItem(SESSIONS_STORAGE_KEY, serializeSessions(updated));
      return [...updated]; // Force new array reference
    });
    const statusMessages: Record<SessionStatus, string> = {
      running: 'Session marked as running',
      completed: 'Session marked as completed',
      stopped: 'Session marked as stopped',
    };
    toast({ title: statusMessages[newStatus], variant: 'success' });
  };

  const [isRelaunching, setIsRelaunching] = useState<string | null>(null);

  const relaunchSession = async (session: AgentSession) => {
    setIsRelaunching(session.id);
    try {
      const result = await terminalApi.launchTerminal({
        agent: session.phase.agent,
        project_path: session.projectPath,
        project_name: session.projectName,
        description: session.phase.description,
      });

      // Update session status to running and update timestamp
      setSessions(prev => {
        const updated = prev.map(s =>
          s.id === session.id
            ? { ...s, status: 'running' as SessionStatus, timestamp: new Date().toISOString(), command: result.command }
            : s
        );
        localStorage.setItem(SESSIONS_STORAGE_KEY, serializeSessions(updated));
        return updated;
      });

      toast({ title: 'Terminal relaunched successfully', variant: 'success' });
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to relaunch terminal';
      toast({ title: errorMsg, variant: 'error' });
    } finally {
      setIsRelaunching(null);
    }
  };

  const handleLaunchTerminal = async (phase: WorkflowPhase) => {
    if (!projectPath.trim()) {
      toast({ title: 'Please enter a project path first', variant: 'error' });
      return;
    }

    setIsLaunching(true);
    try {
      const result = await terminalApi.launchTerminal({
        agent: phase.agent,
        project_path: projectPath,
        project_name: projectName || 'project',
        description: phase.description,
      });

      // Create a unique session ID
      const sessionId = `${phase.id}-${Date.now()}`;

      // Create new session
      const newSession: AgentSession = {
        id: sessionId,
        phase,
        command: result.command,
        timestamp: new Date().toISOString(),
        projectPath,
        projectName: projectName || 'project',
        status: 'running',
      };

      // Add to sessions (at the beginning)
      setSessions(prev => [newSession, ...prev]);

      toast({ title: result.message, variant: 'success' });
      setSelectedPhase(null); // Close dialog after launch

      // Fetch agent info in background
      fetchAgentInfo(sessionId, phase.agent, projectPath);
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to launch terminal';
      toast({ title: errorMsg, variant: 'error' });
    } finally {
      setIsLaunching(false);
    }
  };

  const fetchAgentInfo = async (sessionId: string, agentId: string, path: string, showToast = false) => {
    setIsLoadingAgentInfo(sessionId);
    setAgentInfoErrors(prev => {
      const next = { ...prev };
      delete next[sessionId];
      return next;
    });
    try {
      const info = await terminalApi.getAgentInfo(agentId, path);
      setSessions(prev => {
        // Create completely new array and objects to ensure React detects change
        const updated = prev.map(s => {
          if (s.id === sessionId) {
            // Create new session object with updated agentInfo, preserving all existing fields
            return {
              ...s, // Preserve all existing fields including status
              agentInfo: { ...info }, // Spread to create new object
            };
          }
          return { ...s }; // Create new object reference for all
        });
        // Force localStorage update
        localStorage.setItem(SESSIONS_STORAGE_KEY, serializeSessions(updated));
        return updated;
      });
      if (showToast) {
        toast({ title: 'Agent info refreshed', variant: 'success' });
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to load agent info';
      setAgentInfoErrors(prev => ({ ...prev, [sessionId]: errorMsg }));
      if (showToast) {
        toast({ title: errorMsg, variant: 'error' });
      }
    } finally {
      setIsLoadingAgentInfo(null);
    }
  };

  const handleRefreshAgentInfo = (session: AgentSession) => {
    fetchAgentInfo(session.id, session.phase.agent, session.projectPath, true);
  };

  // Auto-fetch agent info for sessions loaded from localStorage that don't have it
  useEffect(() => {
    sessions.forEach(session => {
      if (!session.agentInfo && session.phase.agent && session.projectPath && isLoadingAgentInfo !== session.id) {
        fetchAgentInfo(session.id, session.phase.agent, session.projectPath);
      }
    });
  }, [sessions.length]); // Only run when sessions count changes (initial load)

  const handleScaffoldProject = async () => {
    if (!projectName.trim() || !projectPath.trim() || !projectOverview.trim()) {
      toast({ title: 'Please fill in all fields', variant: 'error' });
      return;
    }

    setIsScaffolding(true);
    setScaffoldResult(null);

    try {
      const result = await terminalApi.scaffoldProject({
        project_name: projectName,
        project_path: projectPath,
        project_overview: projectOverview,
      });

      setScaffoldResult({
        success: true,
        message: result.message,
        path: result.project_path,
        filesCreated: result.files_created,
        agentsCount: result.agents_count,
      });

      toast({ title: 'Project scaffolded successfully!', variant: 'success' });
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || 'Failed to scaffold project';
      setScaffoldResult({
        success: false,
        message: errorMsg,
      });
      toast({ title: errorMsg, variant: 'error' });
    } finally {
      setIsScaffolding(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header with Config Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary-400" />
            Scaffold Workflow
          </h2>
          <p className="text-sm text-dark-400 mt-1">
            Trigger each phase individually using Claude agents
          </p>
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowConfig(!showConfig)}
          className="text-dark-400"
        >
          {showConfig ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          {showConfig ? 'Hide' : 'Show'} Config
        </Button>
      </div>

      {/* Project Configuration */}
      {showConfig && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          <Card className="p-5 bg-dark-800/50 border-dark-600">
            <div className="flex items-center gap-2 mb-4">
              <FolderOpen className="w-4 h-4 text-primary-400" />
              <span className="text-sm font-medium">Project Configuration</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <Input
                label="Project Name"
                placeholder="my-awesome-project"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
              />
              <Input
                label="Project Path"
                placeholder="C:\Users\you\projects\my-project"
                value={projectPath}
                onChange={(e) => setProjectPath(e.target.value)}
              />
            </div>

            <div className="mb-4">
              <Textarea
                label="Project Overview"
                placeholder="Describe your project... e.g., A healthcare appointment booking platform that allows patients to find doctors, schedule appointments, and manage their medical records."
                value={projectOverview}
                onChange={(e) => setProjectOverview(e.target.value)}
                className="min-h-[120px]"
              />
            </div>

            <div className="flex items-center justify-between">
              <p className="text-xs text-dark-500">
                Enter project details and click scaffold to create a ready-to-develop project
              </p>
              <Button
                onClick={handleScaffoldProject}
                isLoading={isScaffolding}
                glow
                disabled={!projectName.trim() || !projectPath.trim() || !projectOverview.trim()}
              >
                <Rocket className="w-4 h-4 mr-2" />
                Scaffold Project
              </Button>
            </div>

            {/* Scaffold Result */}
            {scaffoldResult && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`mt-4 p-4 rounded-lg ${
                  scaffoldResult.success
                    ? 'bg-green-500/10 border border-green-500/30'
                    : 'bg-red-500/10 border border-red-500/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  {scaffoldResult.success ? (
                    <CheckCircle className="w-5 h-5 text-green-400 mt-0.5" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-400 mt-0.5" />
                  )}
                  <div className="flex-1">
                    <p className={`font-medium ${scaffoldResult.success ? 'text-green-400' : 'text-red-400'}`}>
                      {scaffoldResult.success ? 'Project Scaffolded!' : 'Scaffolding Failed'}
                    </p>
                    <p className="text-sm text-dark-300 mt-1">{scaffoldResult.message}</p>
                    {scaffoldResult.success && scaffoldResult.path && (
                      <div className="mt-3 space-y-2">
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-dark-400">Path:</span>
                          <code className="bg-dark-700 px-2 py-0.5 rounded text-primary-400">
                            {scaffoldResult.path}
                          </code>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-dark-400">
                          <span>Files: {scaffoldResult.filesCreated}</span>
                          <span>Agents: {scaffoldResult.agentsCount}</span>
                        </div>
                        <p className="text-xs text-dark-500 mt-2">
                          Open the project folder and run <code className="bg-dark-700 px-1 rounded">claude</code> to start developing!
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </Card>
        </motion.div>
      )}

      {/* Active Agent Sessions */}
      {sessions.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Terminal className="w-5 h-5 text-green-400" />
              Active Sessions ({sessions.length})
            </h3>
            {sessions.length > 1 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllSessions}
                className="text-dark-400 hover:text-red-400"
              >
                Clear All
              </Button>
            )}
          </div>

          {sessions.map((session) => {
            const PhaseIcon = session.phase.icon;
            const isLoading = isLoadingAgentInfo === session.id;
            const error = agentInfoErrors[session.id];
            // Include agentInfo and status in key to force re-render on update
            const sessionKey = `${session.id}-${session.agentInfo ? 'loaded' : 'pending'}-${session.status}`;

            const statusConfig = {
              running: { variant: 'success' as const, label: 'Running', color: 'from-green-500/10 to-emerald-500/10 border-green-500/30' },
              completed: { variant: 'info' as const, label: 'Completed', color: 'from-blue-500/10 to-cyan-500/10 border-blue-500/30' },
              stopped: { variant: 'warning' as const, label: 'Stopped', color: 'from-yellow-500/10 to-orange-500/10 border-yellow-500/30' },
            };
            const currentStatus = statusConfig[session.status || 'running'];

            return (
              <motion.div
                key={sessionKey}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className={`p-5 bg-gradient-to-r ${currentStatus.color}`}>
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${session.phase.color} flex items-center justify-center`}>
                        <PhaseIcon className="w-6 h-6 text-white" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-semibold text-lg">
                            {(session.agentInfo?.name || session.phase.name).replace(/\s*Agent\s*$/i, '')} Agent
                          </h3>
                          <Badge variant={currentStatus.variant} size="sm">{currentStatus.label}</Badge>
                          {session.agentInfo?.model && (
                            <Badge variant="default" size="sm">{session.agentInfo.model}</Badge>
                          )}
                        </div>
                        <p className="text-sm text-dark-400">
                          {session.agentInfo?.description || session.phase.description}
                        </p>
                        <p className="text-xs text-dark-500 mt-1">
                          Agent: <code className="text-primary-400">{session.phase.agent}</code> | Project: <span className="text-primary-400">{session.projectName}</span>
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {/* Relaunch button - show for stopped/completed sessions */}
                      {(session.status === 'stopped' || session.status === 'completed') && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => relaunchSession(session)}
                          disabled={isRelaunching === session.id}
                          className="text-primary-400 hover:text-primary-300"
                          title="Relaunch terminal"
                        >
                          {isRelaunching === session.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Play className="w-4 h-4" />
                          )}
                        </Button>
                      )}
                      {/* Status controls */}
                      {session.status !== 'completed' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            updateSessionStatus(session.id, 'completed');
                          }}
                          className="text-green-400 hover:text-green-300"
                          title="Mark as completed"
                        >
                          <CheckCircle2 className="w-4 h-4" />
                        </Button>
                      )}
                      {session.status === 'running' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            updateSessionStatus(session.id, 'stopped');
                          }}
                          className="text-yellow-400 hover:text-yellow-300"
                          title="Mark as stopped"
                        >
                          <Square className="w-4 h-4" />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleRefreshAgentInfo(session)}
                        disabled={isLoading}
                        className="text-dark-400 hover:text-dark-200"
                        title="Refresh agent info"
                      >
                        {isLoading ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <RefreshCw className="w-4 h-4" />
                        )}
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => clearSession(session.id)}
                        className="text-dark-400 hover:text-red-400"
                        title="Remove session"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Error message */}
                  {error && (
                    <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                      <div className="flex items-center gap-2 text-sm text-red-400">
                        <AlertCircle className="w-4 h-4" />
                        <span>{error}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRefreshAgentInfo(session)}
                          className="ml-auto text-red-400 hover:text-red-300"
                        >
                          Retry
                        </Button>
                      </div>
                    </div>
                  )}

                  {/* What the agent is doing - from API or fallback to static */}
                  <div className="mb-4">
                    <p className="text-sm font-medium text-dark-300 mb-2">
                      {isLoading ? 'Loading workflow...' : 'This agent will:'}
                    </p>
                    {isLoading ? (
                      <div className="flex items-center gap-2 text-sm text-dark-400">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Fetching agent workflow details...</span>
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                        {(session.agentInfo?.workflow?.length
                          ? session.agentInfo.workflow
                          : session.phase.details
                        ).map((detail, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm text-dark-400">
                            <CheckCircle className="w-4 h-4 text-green-400 flex-shrink-0" />
                            {detail}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Tools used by this agent */}
                  {session.agentInfo?.tools && session.agentInfo.tools.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-dark-300 mb-2">Tools:</p>
                      <div className="flex flex-wrap gap-2">
                        {session.agentInfo.tools.map((tool, i) => (
                          <Badge key={i} variant="default" size="sm">{tool}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Command that was executed */}
                  <div className="bg-dark-900/50 rounded-lg p-3 mb-3">
                    <p className="text-xs text-dark-500 mb-1">Executed command:</p>
                    <code className="text-xs text-green-400 break-all">{session.command}</code>
                  </div>

                  {/* Agent file location */}
                  <div className="flex items-center justify-between text-sm flex-wrap gap-2">
                    <div className="flex items-center gap-2 text-dark-400">
                      <FileText className="w-4 h-4" />
                      <span>Agent definition:</span>
                      <code className="bg-dark-700 px-2 py-0.5 rounded text-primary-400 text-xs">
                        {session.agentInfo?.file_path || `.claude/agents/${session.phase.agent}.md`}
                      </code>
                    </div>
                    <span className="text-xs text-dark-500">
                      Launched {new Date(session.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </Card>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Phase Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {workflowPhases.map((phase, index) => (
          <PhaseCard
            key={phase.id}
            phase={phase}
            index={index}
            onTrigger={() => openTerminal(phase)}
          />
        ))}
      </div>

      {/* Full Orchestration Button */}
      <Card className="p-4 bg-gradient-to-r from-primary-500/10 to-accent-500/10 border-primary-500/30">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary-500 to-accent-500 flex items-center justify-center">
              <Play className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="font-medium">Full Orchestration</h3>
              <p className="text-sm text-dark-400">Run all phases in sequence with the orchestration agent</p>
            </div>
          </div>
          <Button
            onClick={() => openTerminal({
              id: 'orchestration',
              name: 'Full Orchestration',
              description: 'Bootstrap complete project',
              icon: Play,
              agent: 'orchestration',
              agentCommand: '/agent:orchestration',
              color: 'from-primary-500 to-accent-500',
              details: ['All phases executed in order', 'Automatic dependency handling', 'User approval checkpoints'],
            })}
            glow
          >
            <Play className="w-4 h-4 mr-2" />
            Start Orchestration
          </Button>
        </div>
      </Card>

      {/* Terminal Command Dialog */}
      <Dialog open={!!selectedPhase} onOpenChange={(open) => !open && setSelectedPhase(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Terminal className="w-5 h-5 text-primary-400" />
              Launch {selectedPhase?.name} Phase
            </DialogTitle>
            <DialogDescription>
              Run this command in your terminal to start Claude with the {selectedPhase?.agent} agent
            </DialogDescription>
          </DialogHeader>

          {selectedPhase && (
            <div className="space-y-4">
              {/* Agent Info */}
              <div className="flex items-center gap-3 p-3 bg-dark-700/50 rounded-lg">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${selectedPhase.color} flex items-center justify-center`}>
                  <selectedPhase.icon className="w-5 h-5 text-white" />
                </div>
                <div>
                  <p className="font-medium">{selectedPhase.name}</p>
                  <p className="text-sm text-dark-400">{selectedPhase.description}</p>
                </div>
                <Badge variant="info" className="ml-auto">{selectedPhase.agentCommand}</Badge>
              </div>

              {/* What this phase does */}
              <div>
                <p className="text-sm font-medium text-dark-300 mb-2">This phase will:</p>
                <ul className="space-y-1">
                  {selectedPhase.details.map((detail, i) => (
                    <li key={i} className="text-sm text-dark-400 flex items-center gap-2">
                      <ArrowRight className="w-3 h-3 text-primary-400" />
                      {detail}
                    </li>
                  ))}
                </ul>
              </div>

              {/* PowerShell Command */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-dark-300">PowerShell / CMD</span>
                  <Badge variant="info" size="sm">Windows</Badge>
                </div>
                <div className="relative">
                  <div className="bg-dark-900 rounded-lg p-4 font-mono text-sm overflow-x-auto">
                    <pre className="text-blue-400 whitespace-pre-wrap break-all">
                      {getCommands(selectedPhase).powershell}
                    </pre>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={() => copyToClipboard(getCommands(selectedPhase).powershell, 'powershell')}
                  >
                    {copied === 'powershell' ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>

              {/* Bash Command */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-dark-300">Bash / Terminal</span>
                  <Badge variant="success" size="sm">macOS / Linux / Git Bash</Badge>
                </div>
                <div className="relative">
                  <div className="bg-dark-900 rounded-lg p-4 font-mono text-sm overflow-x-auto">
                    <pre className="text-green-400 whitespace-pre-wrap break-all">
                      {getCommands(selectedPhase).bash}
                    </pre>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={() => copyToClipboard(getCommands(selectedPhase).bash, 'bash')}
                  >
                    {copied === 'bash' ? (
                      <Check className="w-4 h-4 text-green-400" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
              </div>

              {/* Agent Info */}
              <div className="p-3 bg-primary-500/10 border border-primary-500/30 rounded-lg">
                <p className="text-sm text-dark-300">
                  <strong>Agent file:</strong>
                  <code className="ml-2 bg-dark-700 px-2 py-0.5 rounded text-primary-400">
                    .claude/agents/{selectedPhase.agent}.md
                  </code>
                </p>
              </div>

              {/* Instructions */}
              <div className="text-sm text-dark-400 space-y-2 bg-dark-700/30 p-3 rounded-lg">
                <p className="font-medium text-dark-300">How it works:</p>
                <ol className="list-decimal list-inside space-y-1">
                  <li>Click <strong>Launch Terminal</strong> to open Claude with the agent workflow</li>
                  <li>Claude will read the agent definition and start the workflow</li>
                  <li>Follow Claude's guidance to complete the phase</li>
                </ol>
                <p className="text-xs text-dark-500 mt-2">
                  The agent definitions are in your project's .claude/agents/ folder
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-3 pt-2">
                <Button variant="secondary" onClick={() => setSelectedPhase(null)}>
                  Close
                </Button>
                <Button
                  glow
                  onClick={() => handleLaunchTerminal(selectedPhase)}
                  isLoading={isLaunching}
                  disabled={!projectPath.trim()}
                >
                  <Play className="w-4 h-4 mr-2" />
                  Launch Terminal
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

function PhaseCard({
  phase,
  index,
  onTrigger,
}: {
  phase: WorkflowPhase;
  index: number;
  onTrigger: () => void;
}) {
  const Icon = phase.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card hover className="h-full flex flex-col">
        <div className="flex items-start justify-between mb-3">
          <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${phase.color} flex items-center justify-center`}>
            <Icon className="w-5 h-5 text-white" />
          </div>
          <Badge variant="default" size="sm">{phase.agentCommand}</Badge>
        </div>

        <h3 className="font-semibold mb-1">{phase.name}</h3>
        <p className="text-sm text-dark-400 mb-3 flex-grow">{phase.description}</p>

        <div className="space-y-1 mb-4">
          {phase.details.slice(0, 2).map((detail, i) => (
            <p key={i} className="text-xs text-dark-500 flex items-center gap-1">
              <span className="w-1 h-1 rounded-full bg-dark-500" />
              {detail}
            </p>
          ))}
        </div>

        <Button
          variant="secondary"
          size="sm"
          className="w-full"
          onClick={onTrigger}
        >
          <Terminal className="w-4 h-4 mr-2" />
          Launch Phase
        </Button>
      </Card>
    </motion.div>
  );
}
