import { test, expect } from './fixtures';

test.describe('Dashboard', () => {
  test('should display the dashboard with create project options', async ({ page }) => {
    await page.goto('/');

    // Check page title
    await expect(page).toHaveTitle(/Project Bootstrap/);

    // Check hero section
    await expect(page.getByText('Create New Project')).toBeVisible();

    // Check mode selection cards
    await expect(page.getByText('Discovery Mode')).toBeVisible();
    await expect(page.getByText('Direct Mode')).toBeVisible();

    // Check sidebar navigation
    await expect(page.getByRole('link', { name: /Dashboard/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /New Project/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /Settings/ })).toBeVisible();
  });

  test('should navigate to new project page when clicking Discovery Mode', async ({ page }) => {
    await page.goto('/');

    // Click on Discovery Mode card
    await page.getByText('Discovery Mode').click();

    // Should navigate to new project page
    await expect(page).toHaveURL(/\/new\?mode=discovery/);
  });

  test('should navigate to new project page when clicking Direct Mode', async ({ page }) => {
    await page.goto('/');

    // Click on Direct Mode card
    await page.getByText('Direct Mode').click();

    // Should navigate to new project page
    await expect(page).toHaveURL(/\/new\?mode=direct/);
  });

  test('should show empty state when no projects exist', async ({ page }) => {
    await page.goto('/');

    // Check for empty state or projects list
    const projectsSection = page.getByText('Recent Projects');
    await expect(projectsSection).toBeVisible();
  });

  test('should have working navigation links', async ({ page }) => {
    await page.goto('/');

    // Navigate to Settings
    await page.getByRole('link', { name: /Settings/ }).click();
    await expect(page).toHaveURL('/settings');

    // Navigate back to Dashboard
    await page.getByRole('link', { name: /Dashboard/ }).click();
    await expect(page).toHaveURL('/');

    // Navigate to New Project
    await page.getByRole('link', { name: /New Project/ }).click();
    await expect(page).toHaveURL('/new');
  });
});
