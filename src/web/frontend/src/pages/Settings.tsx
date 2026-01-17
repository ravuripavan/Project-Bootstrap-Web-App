import { Card, Button, Input } from '@/components/ui';

export default function Settings() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>

      <Card>
        <h2 className="text-lg font-semibold mb-4">Integrations</h2>
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-lg">
            <div>
              <h3 className="font-medium">GitHub</h3>
              <p className="text-sm text-dark-400">Connect to create repositories</p>
            </div>
            <Button variant="secondary" size="sm">Connect</Button>
          </div>
          <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-lg">
            <div>
              <h3 className="font-medium">GitLab</h3>
              <p className="text-sm text-dark-400">Connect to create projects</p>
            </div>
            <Button variant="secondary" size="sm">Connect</Button>
          </div>
          <div className="flex items-center justify-between p-4 bg-dark-800/50 rounded-lg">
            <div>
              <h3 className="font-medium">Jira</h3>
              <p className="text-sm text-dark-400">Connect to create issues</p>
            </div>
            <Button variant="secondary" size="sm">Connect</Button>
          </div>
        </div>
      </Card>

      <Card>
        <h2 className="text-lg font-semibold mb-4">API Keys</h2>
        <div className="space-y-4">
          <Input
            label="Anthropic API Key"
            type="password"
            placeholder="sk-ant-..."
          />
          <Button>Save</Button>
        </div>
      </Card>
    </div>
  );
}
