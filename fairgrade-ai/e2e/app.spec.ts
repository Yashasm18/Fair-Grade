import { test, expect } from '@playwright/test';

test.describe('FairGrade AI — Login & Navigation', () => {
  test('should display the login screen by default', async ({ page }) => {
    await page.goto('/');
    
    // Should show Educator Portal login
    await expect(page.getByText('Educator Portal')).toBeVisible();
    await expect(page.getByText('Sign in with Google')).toBeVisible();
    await expect(page.getByText('Try the Demo (Guest Mode)')).toBeVisible();
  });

  test('should enter guest mode when clicking demo button', async ({ page }) => {
    await page.goto('/');
    
    // Click "Try the Demo" button
    await page.getByText('Try the Demo (Guest Mode)').click();
    
    // Should show evaluation UI elements
    await expect(page.getByRole('heading', { name: 'FairGrade AI', exact: true })).toBeVisible();
    await expect(page.locator('button').filter({ hasText: 'Evaluate' })).toBeVisible();
    await expect(page.locator('button').filter({ hasText: 'Analytics' })).toBeVisible();
  });

  test('should show demo banner in guest mode', async ({ page }) => {
    await page.goto('/');
    await page.getByText('Try the Demo (Guest Mode)').click();
    
    // Should show the demo launch banner
    await expect(page.getByText('New here?')).toBeVisible();
    await expect(page.getByText('Launch Demo')).toBeVisible();
  });

  test('should navigate between Evaluate and Analytics tabs', async ({ page }) => {
    await page.goto('/');
    await page.getByText('Try the Demo (Guest Mode)').click();
    
    // Click Analytics tab
    await page.locator('button').filter({ hasText: 'Analytics' }).click();
    await expect(page.getByText('Admin Analytics')).toBeVisible();
    
    // Click back to Evaluate tab
    await page.locator('button').filter({ hasText: 'Evaluate' }).click();
    await expect(page.getByText('Evaluation Setup')).toBeVisible();
  });
});

test.describe('FairGrade AI — Demo Mode', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByText('Try the Demo (Guest Mode)').click();
  });

  test('should activate demo mode and show results', async ({ page }) => {
    await page.getByText('Launch Demo').click();
    
    // Should show demo active banner
    await expect(page.getByText('Demo Mode Active')).toBeVisible();
    
    // Should show demo results
    await expect(page.getByText('Demo Results')).toBeVisible();
    
    // Should show all 3 demo result cards
    await expect(page.getByText(/demo_answer_biology/)).toBeVisible();
    await expect(page.getByText(/demo_answer_history/)).toBeVisible();
    await expect(page.getByText(/demo_answer_math/)).toBeVisible();
  });

  test('should show bias indicators in demo results', async ({ page }) => {
    await page.getByText('Launch Demo').click();
    
    // Should show bias levels
    await expect(page.getByText('Medium Risk').first()).toBeVisible();
    await expect(page.getByText('Low Risk')).toBeVisible();
    await expect(page.getByText('High Risk')).toBeVisible();
  });

  test('should show teacher verification buttons in demo results', async ({ page }) => {
    await page.getByText('Launch Demo').click();
    
    // Each result card should have Accept/Override buttons
    const acceptButtons = page.getByText('Accept AI Score');
    expect(await acceptButtons.count()).toBe(3);
    
    const overrideButtons = page.getByText('Override Score');
    expect(await overrideButtons.count()).toBe(3);
  });

  test('should exit demo mode', async ({ page }) => {
    await page.getByText('Launch Demo').click();
    await expect(page.getByText('Demo Mode Active')).toBeVisible();
    
    // Exit demo
    await page.getByText('Exit Demo').click();
    
    // Should show the demo launch banner again
    await expect(page.getByText('New here?')).toBeVisible();
  });

  test('should show export buttons in demo mode', async ({ page }) => {
    await page.getByText('Launch Demo').click();
    
    await expect(page.getByText('Export CSV')).toBeVisible();
    await expect(page.getByText('Export PDF')).toBeVisible();
  });
});

test.describe('FairGrade AI — Evaluation Setup', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.getByText('Try the Demo (Guest Mode)').click();
  });

  test('should have teacher score input and slider', async ({ page }) => {
    await expect(page.getByLabel('Teacher score out of 10')).toBeVisible();
    await expect(page.getByLabel('Teacher score slider')).toBeVisible();
  });

  test('should have question context textarea', async ({ page }) => {
    await expect(page.getByLabel('Question and model answer context')).toBeVisible();
  });

  test('should have file upload area', async ({ page }) => {
    await expect(page.getByText(/Drag & drop images/)).toBeVisible();
  });

  test('should disable run button when no files are uploaded', async ({ page }) => {
    // Set a valid score
    await page.getByLabel('Teacher score out of 10').fill('7');
    
    // The button should be disabled because no files are uploaded
    const runButton = page.getByLabel('Run agent evaluation pipeline');
    await expect(runButton).toBeDisabled();
  });

  test('should disable run button when score is empty', async ({ page }) => {
    const runButton = page.getByLabel('Run agent evaluation pipeline');
    await expect(runButton).toBeDisabled();
  });
});

test.describe('FairGrade AI — Dark Mode', () => {
  test('should toggle dark mode', async ({ page }) => {
    await page.goto('/');
    
    // Default is light mode
    const html = page.locator('html');
    await expect(html).toHaveAttribute('data-theme', 'light');
    
    // Toggle to dark mode
    await page.getByLabel(/Switch to dark mode/).click();
    await expect(html).toHaveAttribute('data-theme', 'dark');
    
    // Toggle back to light
    await page.getByLabel(/Switch to light mode/).click();
    await expect(html).toHaveAttribute('data-theme', 'light');
  });
});

test.describe('FairGrade AI — SEO & Accessibility', () => {
  test('should have proper page title', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveTitle(/FairGrade AI/);
  });

  test('should have meta description', async ({ page }) => {
    await page.goto('/');
    const meta = page.locator('meta[name="description"]');
    await expect(meta).toHaveAttribute('content', /FairGrade AI/);
  });

  test('should have a single h1', async ({ page }) => {
    await page.goto('/');
    const h1Count = await page.locator('h1').count();
    expect(h1Count).toBe(1);
  });

  test('should render footer with SDG badge', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Quality Education')).toBeVisible();
    await expect(page.getByText('Google Solution Challenge 2026')).toBeVisible();
  });
});
