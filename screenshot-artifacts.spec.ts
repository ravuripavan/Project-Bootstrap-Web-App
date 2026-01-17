import { test } from '@playwright/test';

test('Screenshot enhanced artifacts', async ({ page }) => {
  // Go to a project with artifacts
  await page.goto('http://localhost:5176/project/proj_828d1cb0eb81');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  // Screenshot with Product Design expanded (default)
  await page.screenshot({ path: 'demo-screenshots/enhanced-product-design.png', fullPage: true });
  console.log('Product Design artifact screenshot taken');

  // Click on Architecture Design to expand it
  const archButton = page.locator('text=Architecture Design').first();
  await archButton.click();
  await page.waitForTimeout(500);

  // Screenshot with Architecture expanded
  await page.screenshot({ path: 'demo-screenshots/enhanced-architecture.png', fullPage: true });
  console.log('Architecture Design artifact screenshot taken');

  console.log('Done!');
});
