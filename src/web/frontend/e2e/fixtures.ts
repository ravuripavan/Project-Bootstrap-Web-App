import { test as base, expect } from '@playwright/test';

// Custom fixtures for testing
export const test = base.extend({
  // Auto-navigate to dashboard before each test
  dashboardPage: async ({ page }, use) => {
    await page.goto('/');
    await use(page);
  },
});

export { expect };

// Test data
export const mockProject = {
  name: 'test-project',
  overview: 'A test project for E2E testing. This is a healthcare appointment booking platform that allows patients to find doctors and schedule appointments.',
  targetUsers: 'Patients, doctors',
};

export const mockDirectProject = {
  name: 'direct-test-project',
  path: './projects/direct-test',
  type: 'web-app',
  stack: 'python',
};
