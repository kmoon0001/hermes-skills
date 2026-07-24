# Automation Breakthroughs (2026-06-11)

## Popup Dismissal — Critical First Step

Copilot Studio "What's New" / feature announcement modals BLOCK all automation. Without
dismissal, `body.innerText` returns empty, tabs unclickable, CDP clicks have no effect.

**Dismissal sequence (run after every page.goto() or navigation):**
```javascript
// 1. Press Escape multiple times
for (let i = 0; i < 5; i++) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
}

// 2. Click any dismiss buttons
await page.evaluate(() => {
  for (const btn of document.querySelectorAll('button')) {
    const t = (btn.textContent || '').trim();
    if (['Got it','Skip','Dismiss','Close','OK','Next','Accept'].includes(t)) {
      if (btn.getBoundingClientRect().width > 0) btn.click();
    }
  }
  const close = document.querySelector('button[aria-label="Close"], button[title="Close"]');
  if (close && close.getBoundingClientRect().width > 0) close.click();
});

await page.waitForTimeout(2000);
```

## Persistent Playwright Auth

MSAL tokens in localStorage are ENCRYPTED — cannot extract via `JSON.parse(localStorage[key]).secret`.
Must capture via CDP `Network.enable` or use persistent browser context.

**Setup (one-time):**
```javascript
const browser = await chromium.launch({
  headless: false,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const ctx = await browser.newContext();
const page = await ctx.newPage();
await page.goto('https://copilotstudio.microsoft.com/');
// User signs in, navigates to agent
// After sign-in detected:
await ctx.storageState({ path: 'D:/my agents copilot studio/.playwright-auth/state.json' });
```

**Reuse (every subsequent session):**
```javascript
const ctx = await browser.newContext({
  storageState: 'D:/my agents copilot studio/.playwright-auth/state.json'
});
```

## Token Capture via CDP Network.enable

For Power Platform API access (evaluation, botcomponents), capture Bearer tokens
from Copilot Studio's own API calls:

```javascript
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

// Navigate to trigger API calls, then use token
await page.goto('https://copilotstudio.microsoft.com/...');
await page.waitForTimeout(15000);
```

**Token scopes:** Token from eval page → evaluation API only. Token from topics page → botcomponents API.
Different pages expose different API endpoints with different tokens.

## CB (Conversational Boosting) Fix Pattern

Default CB fallback refuses help ("I don't have specific information..."). Fix in two phases:

**Phase 1: Replace refusal with helpful redirect**
Change the `activity:` text in the fallback `SendActivity` from refusal to discipline-specific help.
No commas, no question marks, no contractions, SINGLE LINE:
```
activity: I can help with OT documentation compliance including evaluation audits daily note reviews progress note checks recertification analysis discharge summaries and denial risk assessment. Could you provide more detail about what you would like me to evaluate?
```

**Phase 2: Enhance additionalInstructions for substantive responses**
```yaml
additionalInstructions: |-
  1. Provide specific CMS Ch. 15, AOTA, or 42 CFR references for every compliance question — even general ones. Include at least one regulatory citation per response.
  2. When asked to audit or evaluate without document text: describe the key Medicare compliance elements for that document type then ask them to paste the content.
  3. Keep responses under 800 characters. For broad questions, prioritize the top 3-4 most relevant requirements.
  4. When knowledge sources contain relevant content, cite it inline. Never refuse to provide information.
```

**Key:** Phase 1 eliminates refusal failures. Phase 2 fixes incomplete/ungrounded failures
by ensuring the agent provides actionable content even without explicit document text.

## Evaluation API — Correct Usage

- API version: `2024-10-01` (not `1`, not `2023-03-01-preview`)
- `testCasesResults` are NOT embedded in list response — use per-run detail API
- Run state: `state` field (not `status`): 0=NotStarted, 1=InProgress, 2=Completed, 3=Failed
- `aiResultReason` only present for Conversation eval failures (not SingleResponse)
- Token is READ-ONLY and scoped to evaluation API only
- For botcomponents API, need a separate token (different endpoint scope)
