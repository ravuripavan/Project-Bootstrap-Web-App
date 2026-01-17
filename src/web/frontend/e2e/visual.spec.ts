import { test, expect } from './fixtures';

test.describe('Visual Regression', () => {
  test('dashboard should match snapshot', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Take screenshot for visual comparison
    await expect(page).toHaveScreenshot('dashboard.png', {
      maxDiffPixels: 100,
    });
  });

  test('new project page should match snapshot', async ({ page }) => {
    await page.goto('/new');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('new-project.png', {
      maxDiffPixels: 100,
    });
  });

  test('settings page should match snapshot', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('settings.png', {
      maxDiffPixels: 100,
    });
  });
});

test.describe('UI Components', () => {
  test('buttons should have correct styles', async ({ page }) => {
    await page.goto('/new');
    await page.getByRole('button', { name: /Continue/ }).click();

    const createButton = page.getByRole('button', { name: /Create Project/ });
    await expect(createButton).toBeVisible();

    // Check button has gradient background (visual check)
    await expect(createButton).toHaveCSS('background-image', /gradient/);
  });

  test('cards should have glassmorphism effect', async ({ page }) => {
    await page.goto('/');

    // Find a glass card
    const glassCard = page.locator('.glass-card').first();
    if (await glassCard.isVisible()) {
      // Check for backdrop blur
      await expect(glassCard).toHaveCSS('backdrop-filter', /blur/);
    }
  });
});
