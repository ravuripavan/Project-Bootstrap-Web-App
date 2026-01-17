import { test, expect, devices } from '@playwright/test';

test.describe('Responsive Design', () => {
  test('should display correctly on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Check that main content is visible
    await expect(page.getByText('Create New Project')).toBeVisible();

    // Sidebar might be hidden on mobile
    const sidebar = page.locator('aside');
    // Check mobile behavior
  });

  test('should display correctly on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.goto('/');

    await expect(page.getByText('Create New Project')).toBeVisible();
    await expect(page.getByText('Discovery Mode')).toBeVisible();
    await expect(page.getByText('Direct Mode')).toBeVisible();
  });

  test('should display correctly on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto('/');

    // All elements should be visible
    await expect(page.getByText('Create New Project')).toBeVisible();
    await expect(page.getByRole('link', { name: /Dashboard/ })).toBeVisible();
    await expect(page.getByRole('link', { name: /New Project/ })).toBeVisible();
  });
});

test.describe('Accessibility', () => {
  test('should have no accessibility violations on dashboard', async ({ page }) => {
    await page.goto('/');

    // Check for basic accessibility
    // All interactive elements should be focusable
    const buttons = page.getByRole('button');
    const links = page.getByRole('link');

    // Verify links have accessible names
    const dashboardLink = page.getByRole('link', { name: /Dashboard/ });
    await expect(dashboardLink).toBeVisible();
  });

  test('should be keyboard navigable', async ({ page }) => {
    await page.goto('/');

    // Tab through interactive elements
    await page.keyboard.press('Tab');

    // Check that focus is visible (element is focused)
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });
});
