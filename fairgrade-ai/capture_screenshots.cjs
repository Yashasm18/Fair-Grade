const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    // Use dark mode if the app uses it
    colorScheme: 'dark'
  });
  const page = await context.newPage();

  console.log('Navigating to app...');
  // We use the deployed URL or local. Let's use local if running local, else we can change it.
  // Assuming the user runs this in local development, let's keep localhost:5173
  await page.goto('https://team-vektor-fairgrade.vercel.app/', { waitUntil: 'networkidle' });
  
  // Wait a bit for animations/renders
  await page.waitForTimeout(2000);

  // Click Guest Mode to bypass Login
  console.log('Clicking Guest Mode...');
  await page.click('text="Try the Demo (Guest Mode)"');
  await page.waitForTimeout(1000);

  // 1. Upload & Evaluate
  console.log('Taking upload screenshot...');
  await page.screenshot({ path: 'src/assets/screenshot_upload.png' });
  
  // Click Launch Demo to populate results
  console.log('Launching Demo for Bias Analysis...');
  await page.click('text="Launch Demo"');
  await page.waitForTimeout(2000);

  // 2. Bias Analysis
  console.log('Taking bias screenshot...');
  await page.screenshot({ path: 'src/assets/screenshot_bias.png' });

  // 3. Analytics
  console.log('Navigating to Analytics...');
  await page.click('[aria-label="Analytics tab"]');
  await page.waitForTimeout(1000);
  console.log('Taking analytics screenshot...');
  await page.screenshot({ path: 'src/assets/screenshot_analytics.png' });

  await browser.close();
  console.log('Screenshots captured!');
})();
