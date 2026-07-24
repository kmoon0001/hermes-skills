# Persistent Playwright Auth for Copilot Studio

## Setup (one-time)

```javascript
const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
  });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  await page.goto('https://copilotstudio.microsoft.com/', { timeout: 30000, waitUntil: 'domcontentloaded' });
  
  // User signs in manually in the browser window
  console.log('Sign in now in the browser window...');
  
  // Wait for sign-in (URL changes from login.microsoftonline.com to copilotstudio)
  for (let i = 0; i < 24; i++) {
    await page.waitForTimeout(5000);
    const url = page.url();
    if (url.includes('environments') || url.includes('home')) {
      await context.storageState({ path: '.playwright-auth/state.json' });
      console.log('Auth saved!');
      break;
    }
  }
  await browser.close();
})();
```

## Usage (every session)

```javascript
const browser = await chromium.launch({
  headless: false,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const context = await browser.newContext({
  storageState: '.playwright-auth/state.json'  // <-- this is the key
});
// No sign-in needed from here
```

## Token Capture via CDP Network.enable

The persistent session holds MSAL tokens encrypted in localStorage. To get a usable Bearer token for API calls, intercept network traffic:

```javascript
const cdp = await page.context().newCDPSession(page);
await cdp.send('Network.enable');

cdp.on('Network.requestWillBeSent', (params) => {
  const headers = params.request.headers;
  const url = params.request.url;
  if (headers.Authorization?.startsWith('Bearer ') && url.includes('api.powerplatform.com')) {
    fs.writeFileSync('pp_token.txt', headers.Authorization.replace('Bearer ', ''));
  }
});

// Navigate to trigger API calls — token captured automatically
await page.goto('https://copilotstudio.microsoft.com/environments/...');
```

Token is ~4500 chars, scoped to `api.powerplatform.com` (read-only), valid ~1 hour.
