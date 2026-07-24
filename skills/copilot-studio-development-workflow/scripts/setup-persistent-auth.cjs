// Playwright Persistent Auth Setup for Copilot Studio
// Saves sign-in state to avoid fragile connectOverCDP / CDP port startup
//
// Usage: NODE_PATH="C:/Users/kevin/AppData/Roaming/npm/node_modules" node scripts/setup-persistent-auth.cjs
// Saved to: D:/my agents copilot studio/.playwright-auth/state.json
//
// After setup, use in any script:
//   const ctx = await browser.newContext({ storageState: 'D:/my agents copilot studio/.playwright-auth/state.json' });

const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('Opening Copilot Studio for sign-in...');
  console.log('SIGN IN NOW in the browser window that just opened.\n');

  await page.goto('https://copilotstudio.microsoft.com/', {
    timeout: 30000, waitUntil: 'domcontentloaded'
  });

  // Wait for sign-in (max 120s)
  for (let i = 0; i < 24; i++) {
    await page.waitForTimeout(5000);
    const url = page.url();
    const title = await page.title();
    process.stdout.write(`  [${(i + 1) * 5}s] ${url.substring(0, 60)}\r`);

    if (url.includes('environments') || url.includes('bots') || title.includes('Copilot Studio')) {
      console.log('\n\nSign-in detected! Saving auth state...');
      await context.storageState({
        path: 'D:/my agents copilot studio/.playwright-auth/state.json'
      });
      console.log('Auth saved to: D:/my agents copilot studio/.playwright-auth/state.json');
      console.log('Done. Use storageState in future scripts to skip sign-in.');
      await browser.close();
      process.exit(0);
    }
  }

  console.log('\nTimed out waiting for sign-in.');
  await browser.close();
  process.exit(1);
})().catch(e => { console.error(e.message); process.exit(1); });
