# Popup Dismissal & Monaco Editor Tricks

## Popup Dismissal (MANDATORY)

Copilot Studio fires modal popups ("What's New", feature announcements, cookie banners) that block the entire SPA UI. These cause `body.innerText` to return empty and tabs to be unclickable.

### When to dismiss:
- After ANY `page.goto()` to Copilot Studio
- After clicking sidebar tabs (Topics, System, etc.)
- After clicking "Open code editor" (CB editor has its OWN popup)

### Dismissal sequence:

```javascript
// Phase 1: Keyboard escape
for (let i = 0; i < 5; i++) {
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);
}

// Phase 2: Click dismiss buttons
await page.evaluate(() => {
  const dismissTexts = ['Got it', 'Skip', 'Dismiss', 'Close', 'OK', 'Next', 'Accept'];
  for (const btn of document.querySelectorAll('button')) {
    const t = (btn.textContent || '').trim();
    if (dismissTexts.includes(t) && btn.getBoundingClientRect().width > 0) {
      btn.click();
    }
  }
  // Also close aria-label buttons
  const close = document.querySelector('button[aria-label="Close"], button[title="Close"]');
  if (close && close.getBoundingClientRect().width > 0) close.click();
});

// Phase 3: Wait and re-check
await page.waitForTimeout(2000);
```

### After "Open code editor":
The CB topic editor fires ANOTHER popup. Dismiss with Escape × 3 before reading/writing YAML.

## Monaco Editor Selection Trick

The code editor text is nearly impossible to select via CDP `Runtime.evaluate`. Workaround:

```
1. Ctrl+A (selects page content outside editor)
2. Click inside .monaco-editor (puts focus in editor)
3. Ctrl+A again (NOW selects editor text — use navigator.clipboard.writeText to read)
```

```javascript
// Read YAML from editor
await page.keyboard.press('Control+a');           // select page
await page.locator('.monaco-editor').click();     // focus editor
await page.waitForTimeout(500);
await page.keyboard.press('Control+a');           // select editor text
const yaml = await page.evaluate(() => navigator.clipboard.readText());
const normalized = yaml.replace(/\u00a0/g, ' ');  // Monaco uses NBSP
```

## Persistent Playwright Auth

Save Copilot Studio session state once to avoid MFA/sign-in on every run:

```javascript
const browser = await chromium.launch({
  headless: false,
  executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe',
});
const context = await browser.newContext();
const page = await context.newPage();
await page.goto('https://copilotstudio.microsoft.com/', { timeout: 30000 });
// SIGN IN MANUALLY in the browser window
// Then save:
await context.storageState({ path: '.playwright-auth/state.json' });
```

Reuse in future sessions:
```javascript
const context = await browser.newContext({
  storageState: '.playwright-auth/state.json'
});
```
