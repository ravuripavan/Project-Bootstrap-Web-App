import { test, expect } from '@playwright/test';

test.describe('Project Bootstrap Web App Demo', () => {
  const FRONTEND_URL = 'http://localhost:5176';
  const BACKEND_URL = 'http://localhost:8003';

  test.beforeAll(async ({ request }) => {
    // Verify backend is healthy
    const health = await request.get(`${BACKEND_URL}/health`);
    expect(health.ok()).toBeTruthy();
    console.log('Backend is healthy');
  });

  test('Complete Discovery Mode Workflow', async ({ page }) => {
    // Step 1: Open Dashboard
    console.log('\n=== Step 1: Opening Dashboard ===');
    await page.goto(FRONTEND_URL);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'demo-screenshots/01-dashboard.png', fullPage: true });
    console.log('Dashboard loaded successfully');

    // Step 2: Click "New Project" in sidebar
    console.log('\n=== Step 2: Starting New Project ===');
    await page.click('text=New Project');
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'demo-screenshots/02-mode-selection.png', fullPage: true });
    console.log('Mode selection page loaded');

    // Step 3: Select Discovery Mode and click Continue
    console.log('\n=== Step 3: Selecting Discovery Mode ===');
    // Click on the Discovery Mode card
    await page.locator('text=Discovery Mode').first().click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'demo-screenshots/03-discovery-selected.png', fullPage: true });

    // Click Continue button
    await page.click('button:has-text("Continue")');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(500);
    await page.screenshot({ path: 'demo-screenshots/04-discovery-form.png', fullPage: true });
    console.log('Discovery mode form loaded');

    // Step 4: Fill in project details
    console.log('\n=== Step 4: Filling Project Details ===');

    // Fill project name - first input on the page
    await page.locator('input').first().fill('healthcare-platform');

    // Fill project overview - the textarea
    const projectOverview = `I want to build a comprehensive healthcare appointment booking platform that allows patients to easily find doctors based on specialty, location, and availability. The system should support online scheduling, automated appointment reminders via SMS and email, patient medical history management, and secure video consultations. Key features include real-time doctor availability, insurance verification, and integration with electronic health records (EHR) systems.`;
    await page.locator('textarea').fill(projectOverview);

    // Fill target users (optional) - second input
    await page.locator('input').nth(1).fill('Patients, doctors, clinic staff');

    await page.screenshot({ path: 'demo-screenshots/05-form-filled.png', fullPage: true });
    console.log('Project details filled');

    // Step 5: Submit the form
    console.log('\n=== Step 5: Creating Project ===');
    await page.click('button:has-text("Create Project")');

    // Wait for navigation and workflow to start
    await page.waitForURL('**/project/**', { timeout: 10000 });
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Wait for workflow
    await page.screenshot({ path: 'demo-screenshots/06-project-created.png', fullPage: true });
    console.log('Project created!');

    // Step 6: View the project status
    console.log('\n=== Step 6: Viewing Project Progress ===');
    await page.waitForTimeout(2000);
    await page.screenshot({ path: 'demo-screenshots/07-project-progress.png', fullPage: true });
    console.log('Project progress page');

    // Step 7: Check for approval panel
    console.log('\n=== Step 7: Checking Approval Status ===');

    // Look for approve button
    const approveBtn = page.locator('button:has-text("Approve")');
    if (await approveBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      console.log('Found approval button - approving phase');
      await page.screenshot({ path: 'demo-screenshots/08-approval-panel.png', fullPage: true });
      await approveBtn.click();
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'demo-screenshots/09-phase-approved.png', fullPage: true });
      console.log('Phase approved!');

      // Wait and check for architecture phase
      await page.waitForTimeout(3000);
      await page.screenshot({ path: 'demo-screenshots/10-architecture-phase.png', fullPage: true });
    } else {
      console.log('No approval button visible yet');
      await page.screenshot({ path: 'demo-screenshots/08-current-state.png', fullPage: true });
    }

    // Final screenshot
    await page.screenshot({ path: 'demo-screenshots/11-final-state.png', fullPage: true });
    console.log('\n=== UI Demo Complete ===');
  });

  test('API Demonstration', async ({ request }) => {
    console.log('\n========================================');
    console.log('     PROJECT BOOTSTRAP API DEMO');
    console.log('========================================\n');

    // 1. List projects
    console.log('1. Listing all projects...');
    const listResponse = await request.get(`${BACKEND_URL}/api/v1/projects`);
    expect(listResponse.ok()).toBeTruthy();
    const projects = await listResponse.json();
    console.log(`   Found ${projects.total} projects`);

    // 2. Create a new project via API
    console.log('\n2. Creating new project via API...');
    const createResponse = await request.post(`${BACKEND_URL}/api/v1/projects`, {
      data: {
        project_name: 'api-demo-project',
        project_overview: 'This is a demonstration project created via the API. It showcases the ability to programmatically create projects using the REST API endpoints. The project will go through the discovery workflow where AI agents design the product and architecture based on this description.',
        target_users: 'Developers and API consumers',
        key_features: 'REST API, Automated workflows, AI-powered design'
      }
    });
    expect(createResponse.ok()).toBeTruthy();
    const newProject = await createResponse.json();
    console.log(`   Created project: ${newProject.id}`);
    console.log(`   Status: ${newProject.status}`);
    console.log(`   Mode: ${newProject.mode}`);

    // 3. Wait for workflow to progress
    console.log('\n3. Waiting for workflow to progress...');
    await new Promise(resolve => setTimeout(resolve, 4000));

    // 4. Get project details
    console.log('\n4. Fetching project details...');
    const detailResponse = await request.get(`${BACKEND_URL}/api/v1/projects/${newProject.id}`);
    expect(detailResponse.ok()).toBeTruthy();
    const projectDetail = await detailResponse.json();
    console.log(`   Current phase: ${projectDetail.current_phase}`);
    console.log(`   Status: ${projectDetail.status}`);

    if (projectDetail.product_design) {
      console.log('\n   ===== Product Design Generated =====');
      console.log(`   Vision: ${projectDetail.product_design.vision}`);
      console.log(`   Goals: ${projectDetail.product_design.goals.join(', ')}`);
      console.log(`   Epics: ${projectDetail.product_design.epics.length} epics defined`);
      console.log(`   Risks: ${projectDetail.product_design.risks.length} risks identified`);
      console.log(`   Metrics: ${projectDetail.product_design.success_metrics.length} success metrics`);
    }

    // 5. Get workflow progress
    console.log('\n5. Getting workflow progress...');
    const progressResponse = await request.get(`${BACKEND_URL}/api/v1/projects/${newProject.id}/progress`);
    expect(progressResponse.ok()).toBeTruthy();
    const progress = await progressResponse.json();
    console.log(`   Project ID: ${progress.project_id}`);
    console.log(`   Status: ${progress.status}`);
    console.log(`   Current Phase: ${progress.current_phase}`);
    console.log(`   Has Product Design: ${progress.has_product_design}`);
    console.log(`   Has Architecture: ${progress.has_architecture}`);

    // 6. Approve phase if awaiting approval
    if (projectDetail.status === 'awaiting_approval') {
      console.log('\n6. Approving current phase...');
      const approveResponse = await request.post(`${BACKEND_URL}/api/v1/projects/${newProject.id}/approve`, {
        data: {
          feedback: 'Looks good! Proceeding with the design.'
        }
      });
      expect(approveResponse.ok()).toBeTruthy();
      const approvedProject = await approveResponse.json();
      console.log(`   Approved! New status: ${approvedProject.status}`);

      // 7. Wait and check for architecture design
      console.log('\n7. Waiting for architecture design phase...');
      await new Promise(resolve => setTimeout(resolve, 4000));

      const archResponse = await request.get(`${BACKEND_URL}/api/v1/projects/${newProject.id}`);
      const archDetail = await archResponse.json();
      console.log(`   Current phase: ${archDetail.current_phase}`);
      console.log(`   Status: ${archDetail.status}`);

      if (archDetail.architecture_design) {
        console.log('\n   ===== Architecture Design Generated =====');
        console.log(`   Tech Stack: ${JSON.stringify(archDetail.architecture_design.tech_stack)}`);
        console.log(`   Components: ${archDetail.architecture_design.system_components.length} components`);
        console.log(`   API Style: ${archDetail.architecture_design.api_design.style}`);
        console.log(`   Auth: ${archDetail.architecture_design.security.auth}`);
      }

      // 8. Approve architecture
      if (archDetail.status === 'awaiting_approval') {
        console.log('\n8. Approving architecture design...');
        const archApprove = await request.post(`${BACKEND_URL}/api/v1/projects/${newProject.id}/approve`, {
          data: { feedback: 'Architecture looks great!' }
        });
        expect(archApprove.ok()).toBeTruthy();
        console.log('   Architecture approved!');

        // Wait for next phase
        await new Promise(resolve => setTimeout(resolve, 3000));
        const finalResponse = await request.get(`${BACKEND_URL}/api/v1/projects/${newProject.id}`);
        const finalDetail = await finalResponse.json();
        console.log(`\n   Final Status: ${finalDetail.status}`);
        console.log(`   Final Phase: ${finalDetail.current_phase}`);
      }
    }

    console.log('\n========================================');
    console.log('     API DEMO COMPLETE');
    console.log('========================================\n');
  });
});
