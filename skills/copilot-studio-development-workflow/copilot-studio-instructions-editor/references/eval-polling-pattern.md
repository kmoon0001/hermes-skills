# Copilot Studio Evaluation Polling Pattern

Proven reliable approach for reading evaluation run results via Playwright.

## Pre-eval auth dialog

When triggering an eval via the "Evaluate" button, Copilot Studio may show a "Manage profile and connections" dialog asking to select an authenticated account. This dialog has a "Run" button. Use `page.mouse.click()` on the Run button's bounding rect center — `page.evaluate(() => btn.click())` may not work due to React event handling. After clicking Run, the eval starts and shows "Preparing test cases..."

## Why this pattern

The Copilot Studio evaluation page has an SPA data table that:
- Populates scores via JavaScript after page load
- Shows "Running" for in-progress runs, then "General quality" + score percentage when complete
- Earlier attempts to parse structured DOM elements (role="cell" rows, data-testid attributes) were fragile

The reliable approach: navigate to the evaluation page, wait for SPA data load, read `document.body.innerText`, and extract the run section by its identifier (timestamp-based name like `260613_1616`).

## Playwright script pattern

```javascript
const { chromium } = require('playwright-core');
const evalUrl = 'https://copilotstudio.microsoft.com/environments/.../bots/.../evaluation';

// headless:true works for polling — faster, no UI needed
const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', args:['--no-sandbox'] });
const ctx = await browser.newContext({ storageState: authPath, viewport: { width: 1800, height: 1300 } });
const page = await ctx.newPage();

await page.goto(evalUrl, { timeout: 60000, waitUntil: 'domcontentloaded' });
// MUST wait 60+ seconds for SPA to load evaluation data
await sleep(60000);

const body = await page.evaluate(() => document.body.innerText || '');

// Find the run by its timestamp identifier
const runId = '260613_1616';  // YYMMDD_HHMM format
const idx = body.indexOf(runId);
if (idx > -1) {
  const section = body.substring(idx, idx + 2000);
  // Parse: look for "Running" or a percentage ("95%") after "General quality"
  const isRunning = section.includes('Running');
  const scoreMatch = section.match(/(\d+)%/);
  const score = scoreMatch ? scoreMatch[1] : null;
  console.log('Running:', isRunning, 'Score:', score);
}
await browser.close();
```

## Run naming convention

Copilot Studio auto-names runs: `Evaluate {AgentName} {date}_{time}`.
Example: `Evaluate SLP_Specialist 260613_1616`
Date format: `YYMMDD` (June 13, 2026 = `260613`).
Time format: `HHMM` (4:16 PM = `1616`).

## Polling frequency

Conversation evals (20 cases): typically complete in 7–15 minutes.
Single Response evals (100 cases): typically complete in 3–8 minutes.

**Background eval detection (June 2026):** When the evaluation page says "Your evaluation is running in the background. This will not affect your agent's performance." — the eval is running on the server but the page may not show it in "Recent results." This message appears when the Test pane overlays or blocks the eval page content. Fix: wait for eval to complete, then navigate to the evaluation page fresh or toggle the Test pane off to reveal results.

Poll every 2–3 minutes. Do not poll faster — each poll launches a new headless browser that takes ~60s for page load.

## Comparing against baseline

Always compare the new run against the last known-good baseline run in the same data type.
Example history (from SLP, June 2026):
```
260613_1433:  100%  (guard-off baseline)
260613_1231:   95%  (prev guard-off)
260613_1616:   95%  (new caregiver topic ON, old guards OFF)
```

If score drops below baseline, immediately rollback the changes and re-publish.
