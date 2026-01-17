import { test, expect } from '@playwright/test';

test('Screenshot enhanced Product Design via UI', async ({ page }) => {
  // Navigate to dashboard
  await page.goto('http://localhost:5176');
  await page.waitForLoadState('networkidle');

  // Click New Project
  await page.click('text=New Project');
  await page.waitForLoadState('networkidle');

  // Select Discovery Mode and Continue
  await page.locator('text=Discovery Mode').first().click();
  await page.waitForTimeout(300);
  await page.click('button:has-text("Continue")');
  await page.waitForLoadState('networkidle');

  // Fill form
  await page.locator('input').first().fill('task-manager-pro');
  await page.locator('textarea').fill('A modern task management application for teams that enables real-time collaboration, Kanban boards, sprint planning, and time tracking. The app should support integrations with Slack, GitHub, and calendar apps.');
  await page.locator('input').nth(1).fill('Project managers, developers, remote teams');

  // Submit
  await page.click('button:has-text("Create Project")');
  await page.waitForURL('**/project/**', { timeout: 10000 });
  await page.waitForLoadState('networkidle');

  // Wait for workflow to progress
  console.log('Waiting for product design...');
  await page.waitForTimeout(4000);
  await page.reload();
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  // Screenshot 1: Top of page - Vision and Value Proposition
  await page.screenshot({ path: 'demo-screenshots/enhanced-01-vision.png', fullPage: true });
  console.log('Screenshot 1: Vision & Value Proposition');

  // Click to expand Product Design if not already expanded
  const productDesignHeader = page.locator('text=Product Design').first();
  if (await productDesignHeader.isVisible()) {
    await productDesignHeader.click();
    await page.waitForTimeout(500);
  }

  // Scroll to see User Journey
  await page.evaluate(() => window.scrollTo(0, 600));
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'demo-screenshots/enhanced-02-journey.png' });
  console.log('Screenshot 2: User Journey Diagram');

  // Scroll to see Personas
  await page.evaluate(() => window.scrollTo(0, 1200));
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'demo-screenshots/enhanced-03-personas.png' });
  console.log('Screenshot 3: Personas');

  // Scroll to see Epics
  await page.evaluate(() => window.scrollTo(0, 2000));
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'demo-screenshots/enhanced-04-epics.png' });
  console.log('Screenshot 4: Epics & User Stories');

  // Scroll to see MVP Scope
  await page.evaluate(() => window.scrollTo(0, 2800));
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'demo-screenshots/enhanced-05-mvp.png' });
  console.log('Screenshot 5: MVP Scope');

  // Scroll to see Risks and Metrics
  await page.evaluate(() => window.scrollTo(0, 3400));
  await page.waitForTimeout(500);
  await page.screenshot({ path: 'demo-screenshots/enhanced-06-risks-metrics.png' });
  console.log('Screenshot 6: Risks & Success Metrics');

  console.log('All screenshots taken!');
});
