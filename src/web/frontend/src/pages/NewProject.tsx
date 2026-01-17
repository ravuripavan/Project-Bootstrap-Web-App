import { useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Rocket, Zap, ArrowRight, ArrowLeft, Sparkles } from 'lucide-react';
import { Card, Button, Input, Textarea, Badge, toast } from '@/components/ui';
import { projectsApi, ProjectOverview, ProjectSpec } from '@/lib/api';
import { cn } from '@/lib/utils';

type Mode = 'discovery' | 'direct';

export default function NewProject() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>((searchParams.get('mode') as Mode) || 'discovery');
  const [step, setStep] = useState(1);

  const [discoveryForm, setDiscoveryForm] = useState<Partial<ProjectOverview>>({
    project_name: '',
    project_overview: '',
  });

  const [directForm, setDirectForm] = useState<Partial<ProjectSpec>>({
    project_name: '',
    project_path: '',
    project_type: 'web-app',
    language_stack: 'python',
    include_repo: true,
    include_ci: true,
    include_jira: false,
  });

  const createProject = useMutation({
    mutationFn: (data: ProjectOverview | ProjectSpec) => projectsApi.create(data),
    onSuccess: (project) => {
      toast({ title: 'Project created!', variant: 'success' });
      navigate(`/project/${project.id}`);
    },
    onError: () => {
      toast({ title: 'Failed to create project', variant: 'error' });
    },
  });

  const handleSubmit = () => {
    if (mode === 'discovery') {
      createProject.mutate(discoveryForm as ProjectOverview);
    } else {
      createProject.mutate(directForm as ProjectSpec);
    }
  };

  return (
    <div className="max-w-3xl mx-auto">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        {/* Mode Selector */}
        {step === 1 && (
          <div className="space-y-6">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold mb-2">Create New Project</h1>
              <p className="text-dark-400">Choose how you want to create your project</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <ModeCard
                selected={mode === 'discovery'}
                onClick={() => setMode('discovery')}
                icon={<Rocket className="w-8 h-8" />}
                title="Discovery Mode"
                description="Describe your project and let AI design the architecture, tech stack, and structure."
                features={['AI-powered design', 'Review & approve', 'Domain experts']}
                gradient="from-primary-500 to-primary-600"
              />

              <ModeCard
                selected={mode === 'direct'}
                onClick={() => setMode('direct')}
                icon={<Zap className="w-8 h-8" />}
                title="Direct Mode"
                description="Specify your exact tech stack and get a project scaffolded immediately."
                features={['Fast setup', 'Full control', 'Instant results']}
                gradient="from-accent-500 to-accent-600"
              />
            </div>

            <div className="flex justify-end">
              <Button onClick={() => setStep(2)} glow>
                Continue
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* Form Step */}
        {step === 2 && (
          <div className="space-y-6">
            <button
              onClick={() => setStep(1)}
              className="flex items-center gap-2 text-dark-400 hover:text-dark-200 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>

            <Card className="p-8">
              <div className="flex items-center gap-3 mb-6">
                {mode === 'discovery' ? (
                  <Rocket className="w-6 h-6 text-primary-400" />
                ) : (
                  <Zap className="w-6 h-6 text-accent-400" />
                )}
                <h2 className="text-xl font-semibold capitalize">{mode} Mode</h2>
              </div>

              {mode === 'discovery' ? (
                <DiscoveryForm form={discoveryForm} setForm={setDiscoveryForm} />
              ) : (
                <DirectForm form={directForm} setForm={setDirectForm} />
              )}

              <div className="flex justify-end mt-8">
                <Button
                  onClick={handleSubmit}
                  isLoading={createProject.isPending}
                  glow
                >
                  <Sparkles className="w-4 h-4 mr-2" />
                  Create Project
                </Button>
              </div>
            </Card>
          </div>
        )}
      </motion.div>
    </div>
  );
}

function ModeCard({ selected, onClick, icon, title, description, features, gradient }: {
  selected: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  title: string;
  description: string;
  features: string[];
  gradient: string;
}) {
  return (
    <Card
      hover
      onClick={onClick}
      className={cn(
        'p-6 cursor-pointer transition-all',
        selected && 'border-primary-500/50 bg-primary-500/5'
      )}
    >
      <div className={cn(
        'w-16 h-16 rounded-xl bg-gradient-to-br flex items-center justify-center mb-4 text-white',
        gradient
      )}>
        {icon}
      </div>
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      <p className="text-sm text-dark-400 mb-4">{description}</p>
      <div className="flex flex-wrap gap-2">
        {features.map((f) => (
          <Badge key={f} variant="info" size="sm">{f}</Badge>
        ))}
      </div>
    </Card>
  );
}

function DiscoveryForm({ form, setForm }: {
  form: Partial<ProjectOverview>;
  setForm: (f: Partial<ProjectOverview>) => void;
}) {
  return (
    <div className="space-y-6">
      <Input
        label="Project Name"
        placeholder="my-awesome-project"
        value={form.project_name}
        onChange={(e) => setForm({ ...form, project_name: e.target.value })}
      />
      <Textarea
        label="Describe Your Project"
        placeholder="I want to build a healthcare appointment booking platform that allows patients to find doctors, schedule appointments..."
        value={form.project_overview}
        onChange={(e) => setForm({ ...form, project_overview: e.target.value })}
        className="min-h-[200px]"
      />
      <Input
        label="Target Users (optional)"
        placeholder="Patients, doctors, clinic staff"
        value={form.target_users || ''}
        onChange={(e) => setForm({ ...form, target_users: e.target.value })}
      />
    </div>
  );
}

function DirectForm({ form, setForm }: {
  form: Partial<ProjectSpec>;
  setForm: (f: Partial<ProjectSpec>) => void;
}) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Project Name"
          placeholder="my-project"
          value={form.project_name}
          onChange={(e) => setForm({ ...form, project_name: e.target.value })}
        />
        <Input
          label="Project Path"
          placeholder="./projects/my-project"
          value={form.project_path}
          onChange={(e) => setForm({ ...form, project_path: e.target.value })}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-dark-200 mb-2">Project Type</label>
          <select
            className="w-full bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 text-dark-100"
            value={form.project_type}
            onChange={(e) => setForm({ ...form, project_type: e.target.value })}
          >
            <option value="web-app">Web Application</option>
            <option value="api">API Service</option>
            <option value="cli">CLI Tool</option>
            <option value="library">Library</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-dark-200 mb-2">Language Stack</label>
          <select
            className="w-full bg-dark-800 border border-dark-600 rounded-lg px-4 py-2.5 text-dark-100"
            value={form.language_stack}
            onChange={(e) => setForm({ ...form, language_stack: e.target.value })}
          >
            <option value="python">Python</option>
            <option value="node">Node.js</option>
            <option value="go">Go</option>
            <option value="rust">Rust</option>
          </select>
        </div>
      </div>

      <div className="flex gap-6">
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.include_repo}
            onChange={(e) => setForm({ ...form, include_repo: e.target.checked })}
            className="w-4 h-4 rounded border-dark-600 bg-dark-800"
          />
          <span className="text-sm text-dark-200">Git Repository</span>
        </label>
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={form.include_ci}
            onChange={(e) => setForm({ ...form, include_ci: e.target.checked })}
            className="w-4 h-4 rounded border-dark-600 bg-dark-800"
          />
          <span className="text-sm text-dark-200">CI/CD Workflow</span>
        </label>
      </div>
    </div>
  );
}
