import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Plus, Rocket, Zap, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, Badge, Progress, Spinner } from '@/components/ui';
import { projectsApi, Project } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import ScaffoldWorkflow from '@/components/ScaffoldWorkflow';

const statusConfig: Record<string, { color: string; icon: typeof Clock; label: string }> = {
  pending: { color: 'info', icon: Clock, label: 'Pending' },
  executing: { color: 'warning', icon: Zap, label: 'Running' },
  awaiting_approval: { color: 'purple', icon: AlertCircle, label: 'Waiting' },
  completed: { color: 'success', icon: CheckCircle, label: 'Complete' },
  failed: { color: 'error', icon: AlertCircle, label: 'Failed' },
};

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  });

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

      {/* Projects List */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Recent Projects</h2>
          <Link to="/new">
            <button className="flex items-center gap-2 text-primary-400 hover:text-primary-300 transition-colors">
              <Plus className="w-4 h-4" />
              <span className="text-sm font-medium">New Project</span>
            </button>
          </Link>
        </div>

        {isLoading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" />
          </div>
        ) : data?.projects.length === 0 ? (
          <Card className="text-center py-12">
            <p className="text-dark-400">No projects yet. Create your first one!</p>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data?.projects.map((project, i) => (
              <ProjectCard key={project.id} project={project} index={i} />
            ))}
          </div>
        )}
      </div>
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
