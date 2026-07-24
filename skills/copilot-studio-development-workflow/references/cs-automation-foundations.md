# Popup Dismissal & Persistent Auth

## Critical: Copilot Studio Popup Dismissal

Copilot Studio serves "What's New" feature announcement modals, cookie banners, and onboarding dialogs that block the entire SPA UI. They cause:
- `body.innerText` to return empty or partial content
- Tab clicks (`[role="tab"]`) to have no effect
- SPA navigation to silently fail

**Must dismiss ALL popups BEFORE any navigation or interaction.**

### Dismissal Sequence (run after every page load)

```javascript
// 1. Press Escape multiple times to close any modal dialogs
for (let i = 0; i < 5; i++) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
}

// 2. Click any dismiss/close/skip buttons
await page.evaluate(() => {
  // Dismiss buttons by text
  for (const btn of document.querySelectorAll('button')) {
    const t = (btn.textContent || '').trim();
    if (['Got it','Skip','Dismiss','Close','OK','Next','Accept'].includes(t)) {
      if (btn.getBoundingClientRect().width > 0) btn.click();
    }
  }
  // Close buttons by aria attributes
  for (const sel of ['button[aria-label="Close"]', 'button[title="Close"]']) {
    const el = document.querySelector(sel);
    if (el && el.getBoundingClientRect().width > 0) el.click();
  }
});

await page.waitForTimeout(2000);

// 3. Escape again after button clicks
for (let i = 0; i < 3; i++) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
}
```

**Verification:** After dismissal, `document.body.innerText` should contain actual page content (e.g., agent name, "Published", overview tabs), not empty or only "Skip to main content".

## Persistent Playwright Auth

Avoid Microsoft sign-in on every Playwright launch. Save browser context state once, reuse forever.

### Setup (run once)

```javascript
const browser = await chromium.launch({
  headless: false,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const context = await browser.newContext();
const page = await context.newPage();
await page.goto('https://copilotstudio.microsoft.com/');
// Sign in manually in the browser window
// Wait for sign-in to complete (check URL no longer contains 'login.microsoftonline.com')
await page.waitForTimeout(30000); // wait for user
await context.storageState({ path: 'D:/my agents copilot studio/.playwright-auth/state.json' });
```

### Use (every session)

```javascript
const context = await browser.newContext({
  storageState: 'D:/my agents copilot studio/.playwright-auth/state.json'
});
```

Token is good for ~24 hours. Re-run setup when auth expires.

## Token Capture for API Access

CDP `Network.enable` monitors network requests and captures Bearer tokens for API use:

```javascript
const cdp = await page.context().newCDPSession(page);
await cdp.send('Network.enable');

let apiToken = null;
cdp.on('Network.requestWillBeSent', (params) => {
  const h = params.request.headers;
  if (h.Authorization?.startsWith('Bearer ') && 
      params.request.url.includes('api.powerplatform.com')) {
    apiToken = h.Authorization.replace('Bearer ', '');
  }
});

// Navigate to trigger API calls
await page.goto('https://copilotstudio.microsoft.com/environments/.../bots/.../overview');
await page.waitForTimeout(15000);
// apiToken now has ~4500-char Bearer token for Power Platform API
```

The captured token is READ-ONLY and scoped to `api.powerplatform.com`. Works for evaluation API queries. Cannot POST/PATCH.
