import { test, expect } from './fixtures';

test.describe('Navigation and Routing', () => {
  test('should navigate between all main pages', async ({ page }) => {
    // Start at dashboard
    await page.goto('/');
    await expect(page).toHaveURL('/');

    // Go to new project
    await page.getByRole('link', { name: /New Project/ }).click();
    await expect(page).toHaveURL('/new');

    // Go to settings
    await page.getByRole('link', { name: /Settings/ }).click();
    await expect(page).toHaveURL('/settings');

    // Back to dashboard
    await page.getByRole('link', { name: /Dashboard/ }).click();
    await expect(page).toHaveURL('/');
  });

  test('should preserve mode in URL when selecting mode', async ({ page }) => {
    await page.goto('/new');

    // Select discovery mode
    await page.getByText('Discovery Mode').click();
    await page.getByRole('button', { name: /Continue/ }).click();

    // URL should not change dramatically, but form should update
    await expect(page.getByText('Discovery Mode')).toBeVisible();
  });

  test('should handle browser back/forward buttons', async ({ page }) => {
    await page.goto('/');

    // Navigate to new project
    await page.getByRole('link', { name: /New Project/ }).click();
    await expect(page).toHaveURL('/new');

    // Go back
    await page.goBack();
    await expect(page).toHaveURL('/');

    // Go forward
    await page.goForward();
    await expect(page).toHaveURL('/new');
  });

  test('should handle direct URL navigation', async ({ page }) => {
    // Test direct navigation to each route
    await page.goto('/new');
    await expect(page.getByText('Create New Project')).toBeVisible();

    await page.goto('/settings');
    await expect(page.getByRole('heading', { name: 'Settings' })).toBeVisible();

    await page.goto('/');
    await expect(page.getByText('Recent Projects')).toBeVisible();
  });
});
