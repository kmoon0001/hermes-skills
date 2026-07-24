# Popup Dismissal — Copilot Studio Automation

## Why This Exists

Copilot Studio shows "What's New" feature announcement modals, CB editor popups, and cookie consent banners that block the entire UI. Without dismissing these:
- API calls never fire (no token captured)
- Tabs are unclickable
- `document.body.innerText` returns empty
- SPA navigation silently redirects to Overview

## Dismissal Procedure

Do this BEFORE every navigation and after every panel opens:

```
1. Press Escape × 5 with 500ms delay between each
2. Click button[aria-label="Close"] if found
3. Click buttons whose trimmed textContent is in:
   ["Got it", "Skip", "Dismiss", "Close", "OK", "Confirm", "Next"]
4. After clicking "Open code editor", "New evaluation", or
   any "…" → "Edit" action, repeat steps 1-3
```

## Playwright Implementation

```javascript
// After page.goto() completes
for (let i = 0; i < 5; i++) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(300);
}
await page.evaluate(() => {
  for (const b of document.querySelectorAll('button')) {
    const t = (b.textContent || '').trim();
    if (['Got it', 'Skip', 'Dismiss', 'Close', 'OK', 'Confirm'].includes(t)) b.click();
  }
});
await page.waitForTimeout(2000);
// Now navigation will work
```

## Triggers

Popups fire on:
- First load of any Copilot Studio page
- Opening CB topic code editor (More → Open code editor)
- Opening evaluation run results
- Opening a test case editor
- Navigating between tabs (Topics, Knowledge, Evaluation)

## CDP Implementation

When using raw CDP (no Playwright):

```javascript
// Send Escape key via CDP
await cdp.send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape' });
await cdp.send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape' });
```
