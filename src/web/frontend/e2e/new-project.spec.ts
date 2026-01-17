import { test, expect, mockProject, mockDirectProject } from './fixtures';

test.describe('New Project - Mode Selection', () => {
  test('should display mode selection step initially', async ({ page }) => {
    await page.goto('/new');

    // Check step indicator
    await expect(page.getByText('Create New Project')).toBeVisible();
    await expect(page.getByText('Choose how you want to create your project')).toBeVisible();

    // Check both mode cards are visible
    await expect(page.getByText('Discovery Mode')).toBeVisible();
    await expect(page.getByText('Direct Mode')).toBeVisible();

    // Check continue button
    await expect(page.getByRole('button', { name: /Continue/ })).toBeVisible();
  });

  test('should highlight selected mode card', async ({ page }) => {
    await page.goto('/new');

    // Click Discovery Mode
    const discoveryCard = page.locator('text=Discovery Mode').locator('..');
    await discoveryCard.click();

    // Verify it's visually selected (has the selection border class)
    await expect(discoveryCard).toHaveClass(/border-primary/);
  });

  test('should proceed to form when clicking Continue', async ({ page }) => {
    await page.goto('/new');

    // Select a mode and continue
    await page.getByText('Discovery Mode').click();
    await page.getByRole('button', { name: /Continue/ }).click();

    // Should show the form
    await expect(page.getByText('Project Name')).toBeVisible();
  });
});

test.describe('New Project - Discovery Mode Form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/new?mode=discovery');
    await page.getByRole('button', { name: /Continue/ }).click();
  });

  test('should display discovery mode form fields', async ({ page }) => {
    await expect(page.getByLabel(/Project Name/)).toBeVisible();
    await expect(page.getByLabel(/Describe Your Project/)).toBeVisible();
    await expect(page.getByLabel(/Target Users/)).toBeVisible();
  });

  test('should allow filling out the discovery form', async ({ page }) => {
    // Fill project name
    await page.getByLabel(/Project Name/).fill(mockProject.name);

    // Fill project overview
    await page.getByLabel(/Describe Your Project/).fill(mockProject.overview);

    // Fill target users
    await page.getByLabel(/Target Users/).fill(mockProject.targetUsers);

    // Verify values are filled
    await expect(page.getByLabel(/Project Name/)).toHaveValue(mockProject.name);
    await expect(page.getByLabel(/Describe Your Project/)).toHaveValue(mockProject.overview);
  });

  test('should have Create Project button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /Create Project/ })).toBeVisible();
  });

  test('should allow going back to mode selection', async ({ page }) => {
    await page.getByText('Back').click();

    // Should show mode selection again
    await expect(page.getByText('Choose how you want to create your project')).toBeVisible();
  });
});

test.describe('New Project - Direct Mode Form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/new?mode=direct');
    await page.getByRole('button', { name: /Continue/ }).click();
  });

  test('should display direct mode form fields', async ({ page }) => {
    await expect(page.getByLabel(/Project Name/)).toBeVisible();
    await expect(page.getByLabel(/Project Path/)).toBeVisible();
    await expect(page.getByText('Project Type')).toBeVisible();
    await expect(page.getByText('Language Stack')).toBeVisible();
  });

  test('should allow filling out the direct form', async ({ page }) => {
    // Fill project name
    await page.getByLabel(/Project Name/).fill(mockDirectProject.name);

    // Fill project path
    await page.getByLabel(/Project Path/).fill(mockDirectProject.path);

    // Select project type
    await page.locator('select').first().selectOption('web-app');

    // Select language stack
    await page.locator('select').last().selectOption('python');

    // Verify values
    await expect(page.getByLabel(/Project Name/)).toHaveValue(mockDirectProject.name);
    await expect(page.getByLabel(/Project Path/)).toHaveValue(mockDirectProject.path);
  });

  test('should have checkbox options for integrations', async ({ page }) => {
    await expect(page.getByText('Git Repository')).toBeVisible();
    await expect(page.getByText('CI/CD Workflow')).toBeVisible();
  });

  test('should toggle checkboxes', async ({ page }) => {
    const gitCheckbox = page.getByRole('checkbox').first();

    // Should be checked by default
    await expect(gitCheckbox).toBeChecked();

    // Uncheck it
    await gitCheckbox.uncheck();
    await expect(gitCheckbox).not.toBeChecked();

    // Check it again
    await gitCheckbox.check();
    await expect(gitCheckbox).toBeChecked();
  });
});
