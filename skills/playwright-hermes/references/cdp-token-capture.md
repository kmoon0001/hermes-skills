# CDP Network Token Capture for Power Platform API

## Why
MSAL encrypts tokens in localStorage — they can't be extracted as plaintext.
The only reliable way to get a Dataverse/Power Platform bearer token programmatically
is to intercept live API calls via CDP `Network.enable`.

## Capture Pattern

```javascript
const { chromium } = require('playwright-core');
const fs = require('fs');

const browser = await chromium.launch({
  headless: false,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const ctx = await browser.newContext({
  storageState: 'D:/my agents copilot studio/.playwright-auth/state.json'
});
const page = await ctx.newPage();
const cdp = await page.context().newCDPSession(page);
await cdp.send('Network.enable');

let pvaToken = null;

cdp.on('Network.requestWillBeSent', (params) => {
  const h = params.request.headers;
  if (h.Authorization?.startsWith('Bearer ') && params.request.url.includes('api.powerplatform')) {
    pvaToken = h.Authorization.replace('Bearer ', '');
    fs.writeFileSync('pp_token.txt', pvaToken);
  }
});

// Navigate to trigger API calls
await page.goto('https://copilotstudio.microsoft.com/...', {...});
await page.waitForTimeout(15000);

// Token (~4500 chars) is saved to pp_token.txt
```

## Token Types
- **Graph token** (~3362 chars) → `graph.microsoft.com` — NOT useful for Dataverse
- **PVA token** (~4534 chars) → `api.powerplatform.com` — THIS is the one for botcomponents API

## Using the Token
```javascript
const token = fs.readFileSync('pp_token.txt', 'utf8').trim();
const url = `https://default03cc92c3986c4cf4ae271478cf99d1.7f.environment.api.powerplatform.com/powervirtualagents/regional/api/environments/${env}/bots/${botId}/botcomponents?...&api-version=2023-03-01-preview`;
// GET/PATCH with Authorization: Bearer ${token}
```

## Persistent Auth Setup
1. Launch Chrome via Playwright: `headless: false`
2. `browser.newContext()` (no storageState first time)
3. Navigate to copilotstudio.microsoft.com
4. User signs in manually in the visible window
5. After sign-in detected (URL changes from login.microsoftonline.com):
   `await context.storageState({ path: 'state.json' })`
6. Future runs: `browser.newContext({ storageState: 'state.json' })` — no sign-in needed
