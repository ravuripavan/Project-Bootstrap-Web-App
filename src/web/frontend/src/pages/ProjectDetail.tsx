import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircle, Clock, Zap, AlertCircle, ChevronRight, ChevronDown,
  Target, Users, Layers, Shield, Database, Server, Code, GitBranch,
  AlertTriangle, TrendingUp, Cpu, Globe, Lightbulb, Award, ArrowRight,
  UserCheck, UserX, BookOpen, ListChecks, BarChart3, Swords, FolderOpen, Copy
} from 'lucide-react';
import { Card, Badge, Progress, Button, Spinner, toast } from '@/components/ui';
import { projectsApi } from '@/lib/api';
import { cn, formatDate } from '@/lib/utils';

const phases = [
  { id: 'input', name: 'Input', icon: Clock },
  { id: 'product_design', name: 'Product Design', icon: Zap },
  { id: 'architecture_design', name: 'Architecture', icon: Zap },
  { id: 'code_generation', name: 'Code Generation', icon: Zap },
  { id: 'quality', name: 'Quality & DevOps', icon: Zap },
  { id: 'scaffolding', name: 'Scaffolding', icon: Zap },
  { id: 'summary', name: 'Summary', icon: CheckCircle },
];

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const [expandedArtifact, setExpandedArtifact] = useState<string | null>('product_design');

  const { data: project, isLoading, refetch } = useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.get(id!),
    refetchInterval: (query) => {
      const data = query.state.data;
      return data?.status === 'executing' || data?.status === 'awaiting_approval' ? 3000 : false;
    },
  });

  const handleApprove = async () => {
    await projectsApi.approve(id!);
    toast({ title: 'Phase approved!', variant: 'success' });
    refetch();
  };

  const toggleArtifact = (artifact: string) => {
    setExpandedArtifact(expandedArtifact === artifact ? null : artifact);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner size="lg" />
      </div>
    );
  }

  if (!project) {
    return <div>Project not found</div>;
  }

  const currentPhaseIndex = phases.findIndex(p => p.id === project.current_phase);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold mb-2">{project.project_name}</h1>
              <div className="flex items-center gap-4 text-sm text-dark-400">
                <span className="capitalize">{project.mode} Mode</span>
                <span>Created {formatDate(project.created_at)}</span>
              </div>
            </div>
            <Badge
              variant={project.status === 'completed' ? 'success' : project.status === 'executing' ? 'warning' : 'info'}
              size="md"
            >
              {project.status.replace('_', ' ')}
            </Badge>
          </div>
        </Card>
      </motion.div>

      {/* Workflow Progress */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
        <Card>
          <h2 className="text-lg font-semibold mb-6">Workflow Progress</h2>
          <div className="space-y-4">
            {phases.map((phase, i) => {
              const isComplete = i < currentPhaseIndex || project.status === 'completed';
              const isCurrent = phase.id === project.current_phase;
              const isPending = i > currentPhaseIndex;

              return (
                <div key={phase.id} className="flex items-center gap-4">
                  <div className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center',
                    isComplete && 'bg-emerald-500/20 text-emerald-400',
                    isCurrent && 'bg-primary-500/20 text-primary-400 animate-pulse',
                    isPending && 'bg-dark-700 text-dark-500'
                  )}>
                    {isComplete ? <CheckCircle className="w-5 h-5" /> : isCurrent ? <Zap className="w-5 h-5" /> : <Clock className="w-5 h-5" />}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className={cn('font-medium', isComplete && 'text-emerald-400', isCurrent && 'text-primary-400', isPending && 'text-dark-500')}>
                        {phase.name}
                      </span>
                      {isComplete && <Badge variant="success" size="sm">Complete</Badge>}
                      {isCurrent && <Badge variant="info" size="sm">In Progress</Badge>}
                    </div>
                    {isCurrent && <Progress value={50} variant="gradient" className="mt-2" size="sm" />}
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      </motion.div>

      {/* Scaffolded Location - show when completed */}
      {project.status === 'completed' && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <Card className="border-emerald-500/30 bg-emerald-500/5">
            <div className="flex items-center gap-3 mb-4">
              <FolderOpen className="w-6 h-6 text-emerald-400" />
              <h2 className="text-lg font-semibold">Project Scaffolded</h2>
            </div>
            <div className="space-y-4">
              <div>
                <p className="text-sm text-dark-400 mb-2">Location on disk:</p>
                <div className="flex items-center gap-2 bg-dark-800 rounded-lg p-3">
                  <code className="text-emerald-400 flex-1 text-sm">
                    C:\Users\ravur\bootstrapped-projects\{project.project_name}
                  </code>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(`C:\\Users\\ravur\\bootstrapped-projects\\${project.project_name}`);
                      toast({ title: 'Path copied!', variant: 'success' });
                    }}
                    className="p-2 hover:bg-dark-700 rounded transition-colors"
                    title="Copy path"
                  >
                    <Copy className="w-4 h-4 text-dark-400" />
                  </button>
                </div>
              </div>
              <div>
                <p className="text-sm text-dark-400 mb-2">Git branches:</p>
                <div className="flex items-center gap-2">
                  <Badge variant="default" size="sm">main</Badge>
                  <Badge variant="success" size="sm">dev (current)</Badge>
                  <Badge variant="default" size="sm">test</Badge>
                </div>
              </div>
              <div className="pt-2 border-t border-dark-700">
                <p className="text-sm text-dark-300">
                  Open in Claude Code CLI and run <code className="text-primary-400 bg-dark-800 px-2 py-0.5 rounded">/agent:orchestration start</code> to begin development.
                </p>
              </div>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Approval Panel */}
      {project.status === 'awaiting_approval' && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card className="border-primary-500/30 bg-primary-500/5">
            <div className="flex items-center gap-3 mb-4">
              <AlertCircle className="w-6 h-6 text-primary-400" />
              <h2 className="text-lg font-semibold">Review Required</h2>
            </div>
            <p className="text-dark-400 mb-6">
              The {project.current_phase?.replace('_', ' ')} phase is complete and ready for your review.
            </p>
            <div className="flex gap-4">
              <Button onClick={handleApprove} glow>
                Approve & Continue
                <ChevronRight className="w-4 h-4 ml-2" />
              </Button>
              <Button variant="secondary">Request Changes</Button>
            </div>
          </Card>
        </motion.div>
      )}

      {/* Generated Artifacts */}
      {(project.product_design || project.architecture_design) && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <Card>
            <h2 className="text-lg font-semibold mb-4">Generated Artifacts</h2>
            <div className="space-y-4">
              {project.product_design && (
                <ProductDesignArtifact
                  data={project.product_design}
                  expanded={expandedArtifact === 'product_design'}
                  onToggle={() => toggleArtifact('product_design')}
                />
              )}
              {project.architecture_design && (
                <ArchitectureDesignArtifact
                  data={project.architecture_design}
                  expanded={expandedArtifact === 'architecture_design'}
                  onToggle={() => toggleArtifact('architecture_design')}
                />
              )}
            </div>
          </Card>
        </motion.div>
      )}

      {/* Project Overview */}
      {project.project_overview && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }}>
          <Card>
            <h2 className="text-lg font-semibold mb-4">Project Overview</h2>
            <p className="text-dark-300 whitespace-pre-wrap">
              {typeof project.project_overview === 'object' ? project.project_overview.project_overview : project.project_overview}
            </p>
          </Card>
        </motion.div>
      )}
    </div>
  );
}

// User Journey Diagram Component
function UserJourneyDiagram({ stages }: { stages: any[] }) {
  const emotionColors: Record<string, string> = {
    'Curious': 'text-blue-400',
    'Interested': 'text-cyan-400',
    'Hopeful': 'text-green-400',
    'Engaged': 'text-emerald-400',
    'Productive': 'text-primary-400',
    'Satisfied': 'text-yellow-400',
  };

  return (
    <div className="bg-dark-900 rounded-xl p-6 overflow-x-auto">
      <div className="flex items-center gap-2 min-w-max">
        {stages.map((stage, i) => (
          <div key={stage.stage} className="flex items-center">
            <div className="flex flex-col items-center">
              {/* Stage Circle */}
              <div className={cn(
                'w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold',
                'bg-gradient-to-br from-primary-500/30 to-accent-500/30 border-2 border-primary-500/50'
              )}>
                {i + 1}
              </div>
              {/* Stage Name */}
              <div className="mt-2 text-center">
                <p className="font-semibold text-dark-100 text-sm">{stage.stage}</p>
                <p className={cn('text-xs', emotionColors[stage.emotions] || 'text-dark-400')}>
                  {stage.emotions}
                </p>
              </div>
              {/* Touchpoints */}
              <div className="mt-2 flex flex-col gap-1">
                {stage.touchpoints.slice(0, 2).map((tp: string) => (
                  <span key={tp} className="text-xs text-dark-500 bg-dark-800 px-2 py-0.5 rounded">
                    {tp}
                  </span>
                ))}
                {stage.touchpoints.length > 2 && (
                  <span className="text-xs text-dark-500">+{stage.touchpoints.length - 2} more</span>
                )}
              </div>
            </div>
            {/* Arrow */}
            {i < stages.length - 1 && (
              <ArrowRight className="w-8 h-8 text-primary-500/50 mx-2 flex-shrink-0" />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// Product Design Artifact Component
function ProductDesignArtifact({ data, expanded, onToggle }: { data: any; expanded: boolean; onToggle: () => void }) {
  return (
    <div className="border border-dark-600 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between bg-gradient-to-r from-primary-500/10 to-accent-500/10 hover:from-primary-500/20 hover:to-accent-500/20 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-500/20 flex items-center justify-center">
            <Target className="w-5 h-5 text-primary-400" />
          </div>
          <div className="text-left">
            <h3 className="font-semibold">Product Design</h3>
            <p className="text-sm text-dark-400">Vision, personas, user journey, epics & MVP scope</p>
          </div>
        </div>
        {expanded ? <ChevronDown className="w-5 h-5 text-dark-400" /> : <ChevronRight className="w-5 h-5 text-dark-400" />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4 space-y-6 border-t border-dark-600">
              {/* Vision & Problem Statement */}
              <Section icon={<Lightbulb className="w-4 h-4" />} title="Vision">
                <p className="text-dark-300 leading-relaxed">{data.vision}</p>
                {data.problem_statement && (
                  <div className="mt-3 p-3 bg-dark-800 rounded-lg border-l-4 border-accent-500">
                    <p className="text-sm text-dark-400 font-medium mb-1">Problem Statement</p>
                    <p className="text-dark-300 text-sm">{data.problem_statement}</p>
                  </div>
                )}
              </Section>

              {/* Value Proposition */}
              {data.value_proposition && (
                <Section icon={<Award className="w-4 h-4" />} title="Value Proposition">
                  <div className="grid grid-cols-2 gap-3">
                    {data.value_proposition.map((value: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 bg-dark-800 rounded-lg p-3">
                        <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5 flex-shrink-0" />
                        <span className="text-dark-200 text-sm">{value}</span>
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {/* Goals */}
              <Section icon={<Target className="w-4 h-4" />} title="Goals">
                <div className="space-y-2">
                  {(Array.isArray(data.goals) ? data.goals : []).map((goal: any, i: number) => (
                    <div key={i} className="flex items-center justify-between bg-dark-800 rounded-lg p-3">
                      <div className="flex items-center gap-3">
                        {typeof goal === 'object' ? (
                          <>
                            <Badge variant={goal.type === 'timeline' ? 'info' : goal.type === 'growth' ? 'success' : goal.type === 'reliability' ? 'warning' : 'default'} size="sm">
                              {goal.type}
                            </Badge>
                            <span className="text-dark-200">{goal.goal}</span>
                          </>
                        ) : (
                          <span className="text-dark-200">{goal}</span>
                        )}
                      </div>
                      {typeof goal === 'object' && goal.priority && (
                        <Badge variant={goal.priority === 'critical' ? 'error' : goal.priority === 'high' ? 'warning' : 'default'} size="sm">
                          {goal.priority}
                        </Badge>
                      )}
                    </div>
                  ))}
                </div>
              </Section>

              {/* User Journey Diagram */}
              {data.user_journey?.stages && (
                <Section icon={<ArrowRight className="w-4 h-4" />} title="User Journey">
                  <UserJourneyDiagram stages={data.user_journey.stages} />
                </Section>
              )}

              {/* Personas */}
              <Section icon={<Users className="w-4 h-4" />} title="Personas">
                <div className="grid gap-4">
                  {data.personas?.map((persona: any, i: number) => (
                    <div key={i} className="bg-dark-800 rounded-xl p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold text-dark-100">{persona.name}</h4>
                          <div className="flex items-center gap-2 mt-1">
                            {persona.role && <Badge variant="info" size="sm">{persona.role}</Badge>}
                            {persona.age && <span className="text-xs text-dark-500">Age: {persona.age}</span>}
                            {persona.tech_comfort && (
                              <Badge variant={persona.tech_comfort === 'High' ? 'success' : 'warning'} size="sm">
                                Tech: {persona.tech_comfort}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-dark-300 mb-3">{persona.description}</p>
                      {persona.goals && (
                        <div className="mb-2">
                          <div className="flex items-center gap-1 text-xs text-dark-500 mb-1">
                            <UserCheck className="w-3 h-3" /> Goals
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {persona.goals.map((g: string) => (
                              <span key={g} className="text-xs bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">{g}</span>
                            ))}
                          </div>
                        </div>
                      )}
                      {persona.pain_points && (
                        <div>
                          <div className="flex items-center gap-1 text-xs text-dark-500 mb-1">
                            <UserX className="w-3 h-3" /> Pain Points
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {persona.pain_points.map((p: string) => (
                              <span key={p} className="text-xs bg-red-500/20 text-red-400 px-2 py-0.5 rounded">{p}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </Section>

              {/* Epics */}
              <Section icon={<Layers className="w-4 h-4" />} title="Epics">
                <div className="space-y-2">
                  {data.epics?.map((epic: any) => (
                    <div key={epic.id} className="bg-dark-800 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-mono text-dark-500 bg-dark-700 px-2 py-0.5 rounded">{epic.id}</span>
                          <span className="text-dark-100 font-medium">{epic.title}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {epic.story_points && (
                            <span className="text-xs text-dark-400">{epic.story_points} pts</span>
                          )}
                          <Badge variant={epic.priority === 'P0' ? 'error' : epic.priority === 'P1' ? 'warning' : 'default'} size="sm">
                            {epic.priority}
                          </Badge>
                        </div>
                      </div>
                      {epic.description && (
                        <p className="text-sm text-dark-400 mt-1">{epic.description}</p>
                      )}
                    </div>
                  ))}
                </div>
              </Section>

              {/* User Stories */}
              {data.user_stories && data.user_stories.length > 0 && (
                <Section icon={<BookOpen className="w-4 h-4" />} title="User Stories">
                  <div className="space-y-3">
                    {data.user_stories.map((story: any) => (
                      <div key={story.id} className="bg-dark-800 rounded-lg p-3">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-mono text-dark-500">{story.id}</span>
                          <span className="text-xs text-primary-400">Epic: {story.epic}</span>
                        </div>
                        <p className="text-dark-200 text-sm mb-2">{story.story}</p>
                        {story.acceptance_criteria && (
                          <div className="flex flex-wrap gap-1">
                            {story.acceptance_criteria.map((ac: string) => (
                              <span key={ac} className="text-xs bg-dark-700 text-dark-300 px-2 py-0.5 rounded">
                                ✓ {ac}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </Section>
              )}

              {/* MVP Scope */}
              <Section icon={<GitBranch className="w-4 h-4" />} title="MVP Scope">
                <div className="bg-dark-800 rounded-lg p-4">
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <p className="text-sm text-dark-400 mb-2">Included Epics</p>
                      <div className="flex flex-wrap gap-2">
                        {data.mvp_scope?.included_epics?.map((epicId: string) => (
                          <Badge key={epicId} variant="success" size="sm">{epicId}</Badge>
                        ))}
                      </div>
                    </div>
                    {data.mvp_scope?.excluded_epics && (
                      <div>
                        <p className="text-sm text-dark-400 mb-2">Post-MVP</p>
                        <div className="flex flex-wrap gap-2">
                          {data.mvp_scope.excluded_epics.map((epicId: string) => (
                            <Badge key={epicId} variant="default" size="sm">{epicId}</Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  {data.mvp_scope?.total_story_points && (
                    <p className="text-sm text-primary-400 mb-3">Total Story Points: {data.mvp_scope.total_story_points}</p>
                  )}
                  <p className="text-sm text-dark-300 mb-3">
                    <span className="text-dark-500">Rationale:</span> {data.mvp_scope?.rationale}
                  </p>
                  {data.mvp_scope?.release_criteria && (
                    <div className="mt-3 pt-3 border-t border-dark-700">
                      <p className="text-xs text-dark-500 mb-2">Release Criteria</p>
                      <div className="grid grid-cols-2 gap-2">
                        {data.mvp_scope.release_criteria.map((criteria: string, i: number) => (
                          <div key={i} className="flex items-center gap-2 text-xs text-dark-300">
                            <ListChecks className="w-3 h-3 text-emerald-400" />
                            {criteria}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </Section>

              {/* Risks */}
              <Section icon={<AlertTriangle className="w-4 h-4" />} title="Risks">
                <div className="space-y-2">
                  {data.risks?.map((risk: any) => (
                    <div key={risk.id} className="bg-dark-800 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-dark-100 font-medium">{risk.description}</span>
                        <div className="flex items-center gap-2">
                          {risk.probability && (
                            <span className="text-xs text-dark-500">P: {risk.probability}</span>
                          )}
                          <Badge variant={risk.severity === 'critical' ? 'error' : risk.severity === 'high' ? 'error' : risk.severity === 'medium' ? 'warning' : 'default'} size="sm">
                            {risk.severity}
                          </Badge>
                        </div>
                      </div>
                      {risk.impact && (
                        <p className="text-xs text-red-400 mb-1">Impact: {risk.impact}</p>
                      )}
                      <p className="text-sm text-dark-400">
                        <span className="text-dark-500">Mitigation:</span> {risk.mitigation}
                      </p>
                    </div>
                  ))}
                </div>
              </Section>

              {/* Success Metrics */}
              <Section icon={<BarChart3 className="w-4 h-4" />} title="Success Metrics">
                <div className="grid grid-cols-2 gap-3">
                  {data.success_metrics?.map((metric: any) => (
                    <div key={metric.id} className="bg-dark-800 rounded-lg p-3">
                      <p className="font-medium text-dark-100 text-sm">{metric.metric}</p>
                      <p className="text-emerald-400 font-semibold">{metric.target}</p>
                      {metric.timeframe && (
                        <p className="text-xs text-dark-500 mt-1">{metric.timeframe}</p>
                      )}
                      {metric.measurement && (
                        <p className="text-xs text-dark-400">via {metric.measurement}</p>
                      )}
                    </div>
                  ))}
                </div>
              </Section>

              {/* Competitive Analysis */}
              {data.competitive_analysis && (
                <Section icon={<Swords className="w-4 h-4" />} title="Competitive Analysis">
                  <div className="bg-dark-800 rounded-lg p-4">
                    <p className="text-sm text-dark-400 mb-2">Key Differentiators</p>
                    <div className="space-y-2">
                      {data.competitive_analysis.differentiators?.map((diff: string, i: number) => (
                        <div key={i} className="flex items-center gap-2">
                          <CheckCircle className="w-4 h-4 text-emerald-400" />
                          <span className="text-dark-200 text-sm">{diff}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </Section>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Architecture Design Artifact Component
function ArchitectureDesignArtifact({ data, expanded, onToggle }: { data: any; expanded: boolean; onToggle: () => void }) {
  return (
    <div className="border border-dark-600 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full p-4 flex items-center justify-between bg-gradient-to-r from-accent-500/10 to-emerald-500/10 hover:from-accent-500/20 hover:to-emerald-500/20 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-accent-500/20 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-accent-400" />
          </div>
          <div className="text-left">
            <h3 className="font-semibold">Architecture Design</h3>
            <p className="text-sm text-dark-400">Tech stack, components & infrastructure</p>
          </div>
        </div>
        {expanded ? <ChevronDown className="w-5 h-5 text-dark-400" /> : <ChevronRight className="w-5 h-5 text-dark-400" />}
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-4 space-y-6 border-t border-dark-600">
              <Section icon={<Code className="w-4 h-4" />} title="Tech Stack">
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(data.tech_stack || {}).map(([key, value]) => (
                    <div key={key} className="bg-dark-800 rounded-lg p-3 text-center">
                      <p className="text-xs text-dark-500 uppercase mb-1">{key}</p>
                      <p className="font-semibold text-dark-100">{value as string}</p>
                    </div>
                  ))}
                </div>
              </Section>

              <Section icon={<Server className="w-4 h-4" />} title="System Components">
                <div className="space-y-2">
                  {data.system_components?.map((component: any, i: number) => (
                    <div key={i} className="flex items-center gap-3 bg-dark-800 rounded-lg p-3">
                      <div className="w-8 h-8 rounded bg-accent-500/20 flex items-center justify-center">
                        <Server className="w-4 h-4 text-accent-400" />
                      </div>
                      <div>
                        <p className="font-medium text-dark-100">{component.name}</p>
                        <p className="text-sm text-dark-400">{component.description}</p>
                      </div>
                      {component.type && <Badge variant="default" size="sm" className="ml-auto">{component.type}</Badge>}
                    </div>
                  ))}
                </div>
              </Section>

              <Section icon={<Database className="w-4 h-4" />} title="Data Model">
                <div className="bg-dark-800 rounded-lg p-4">
                  <p className="text-sm text-dark-400 mb-2">Entities:</p>
                  <div className="flex flex-wrap gap-2 mb-3">
                    {data.data_model?.entities?.map((entity: string) => (
                      <Badge key={entity} variant="info" size="sm">{entity}</Badge>
                    ))}
                  </div>
                  <p className="text-sm text-dark-300">
                    <span className="text-dark-500">Relationships:</span> {data.data_model?.relationships}
                  </p>
                </div>
              </Section>

              <Section icon={<Globe className="w-4 h-4" />} title="API Design">
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-dark-800 rounded-lg p-3">
                    <p className="text-xs text-dark-500 mb-1">Style</p>
                    <p className="font-medium text-dark-100">{data.api_design?.style}</p>
                  </div>
                  <div className="bg-dark-800 rounded-lg p-3">
                    <p className="text-xs text-dark-500 mb-1">Versioning</p>
                    <p className="font-medium text-dark-100">{data.api_design?.versioning}</p>
                  </div>
                  <div className="bg-dark-800 rounded-lg p-3">
                    <p className="text-xs text-dark-500 mb-1">Auth</p>
                    <p className="font-medium text-dark-100">{data.api_design?.authentication}</p>
                  </div>
                </div>
              </Section>

              <Section icon={<Shield className="w-4 h-4" />} title="Security">
                <div className="grid grid-cols-2 gap-3">
                  {Object.entries(data.security || {}).map(([key, value]) => (
                    <div key={key} className="bg-dark-800 rounded-lg p-3">
                      <p className="text-xs text-dark-500 uppercase mb-1">{key}</p>
                      <p className="text-dark-200">{value as string}</p>
                    </div>
                  ))}
                </div>
              </Section>

              <Section icon={<Cpu className="w-4 h-4" />} title="Infrastructure">
                <div className="grid grid-cols-3 gap-3">
                  {Object.entries(data.infrastructure || {}).map(([key, value]) => (
                    <div key={key} className="bg-dark-800 rounded-lg p-3">
                      <p className="text-xs text-dark-500 uppercase mb-1">{key}</p>
                      <p className="font-medium text-dark-100">{value as string}</p>
                    </div>
                  ))}
                </div>
              </Section>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Reusable Section Component
function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-primary-400">{icon}</span>
        <h4 className="font-medium text-dark-200">{title}</h4>
      </div>
      {children}
    </div>
  );
}
