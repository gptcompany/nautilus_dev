const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  const targetUrl = 'http://localhost:3000/d/alpha-evolve-evolution/alpha-evolve-evolution?var-experiment=test_exp&from=now-2h&to=now';

  console.log('Navigating to:', targetUrl);

  try {
    await page.goto(targetUrl, { waitUntil: 'networkidle', timeout: 60000 });

    // Wait for dashboard to render
    console.log('Waiting for dashboard to render...');
    await page.waitForTimeout(5000);

    // Check current URL
    const currentUrl = page.url();
    console.log('Current URL:', currentUrl);

    // Take screenshot
    const screenshotPath = '/media/sam/1TB/nautilus_dev/.claude/visual-validation/grafana_dashboard_round_1.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log('Screenshot saved to:', screenshotPath);

  } catch (error) {
    console.error('Error:', error.message);

    // Take screenshot even on error
    const errorScreenshotPath = '/media/sam/1TB/nautilus_dev/.claude/visual-validation/grafana_error.png';
    await page.screenshot({ path: errorScreenshotPath, fullPage: true });
    console.log('Error screenshot saved to:', errorScreenshotPath);
  }

  await browser.close();
})();
