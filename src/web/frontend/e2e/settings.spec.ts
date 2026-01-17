import { test, expect } from './fixtures';

test.describe('Settings Page', () => {
  test('should display settings page with integrations', async ({ page }) => {
    await page.goto('/settings');

    // Check page title
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();

    // Check integrations section
    await expect(page.getByText('Integrations')).toBeVisible();
    await expect(page.getByText('GitHub')).toBeVisible();
    await expect(page.getByText('GitLab')).toBeVisible();
    await expect(page.getByText('Jira')).toBeVisible();
  });

  test('should have connect buttons for each integration', async ({ page }) => {
    await page.goto('/settings');

    const connectButtons = page.getByRole('button', { name: /Connect/ });
    await expect(connectButtons).toHaveCount(3);
  });

  test('should display API keys section', async ({ page }) => {
    await page.goto('/settings');

    await expect(page.getByText('API Keys')).toBeVisible();
    await expect(page.getByLabel(/Anthropic API Key/)).toBeVisible();
  });

  test('should have a save button for API keys', async ({ page }) => {
    await page.goto('/settings');

    await expect(page.getByRole('button', { name: 'Save' })).toBeVisible();
  });

  test('should allow entering API key', async ({ page }) => {
    await page.goto('/settings');

    const apiKeyInput = page.getByLabel(/Anthropic API Key/);
    await apiKeyInput.fill('sk-ant-test-key');

    await expect(apiKeyInput).toHaveValue('sk-ant-test-key');
  });
});
