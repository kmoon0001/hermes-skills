# Copilot Studio Browser Automation Pitfalls (June 2026)

## Test Pane Textarea Placeholder (June 2026)

The test pane textarea has placeholder text `"Ask a question or describe what you need"` (NOT `"Type your message"`). Scripts searching for `textarea[placeholder*="Type your message"]` fail silently. Use `textarea[placeholder*="Ask"]` or `querySelector('textarea[placeholder*="question"]')` instead. Use CDP `Input.dispatchMouseEvent` for clicking — same Playwright vs CDP issue as Edit buttons.

## CDP Session Management

### NEVER Close All Pages
Closing all pages via `for (const p of pages) await p.close()` kills MSAL auth. Next page shows "Pick an account."

**Fix:** Keep page[0] alive always. Open new pages BEFORE closing old ones.

### Page Index Shifting
When pages are closed, indices shift. `pages()[0]` might be a different page. Always re-query after close.

### Auth Expiry vs Page State
Auth lives in the Chrome process, not individual pages. Pages inherit auth as long as Chrome is running. But closing all pages may trigger Chrome session cleanup.

## Test Pane Overlay

### Symptom
Eval scores invisible. Page text shows "Test your agent" content instead of evaluation results.

### Fix
Click "Test" toggle button in top-right toolbar to close the overlay. Or open fresh page.

### Evidence
Vision analysis: Test pane covered 40% of eval page, hiding score percentages in the Results column.

## Environment/Bot Confusion

### Symptom
URL shows PT eval in Default environment, but DOM shows Pacific Coast Case Historian results from a different environment.

### Fix
After navigation, verify `text.includes('PT_Specialist')`. If not, force-navigate with full URL.

### Root Cause
SPA caches navigation state aggressively. Old bot's DOM persists across navigations.

## Eval Page Loading

### SPA Load Time
Eval pages take 10-20 seconds to load test data. Use polling loop:
```javascript
for (let i = 0; i < 30; i++) {
    await sleep(3000);
    const text = await page.evaluate(() => document.body?.innerText || '');
    if (text.includes('Recent results')) break;
}
```

### "Recent results" Section
Contains eval history. Each entry: name, test set, date, score. Scores are in `General quality\nEnd of interactive chart.\n{score}%` pattern.

### Clicking Eval Results
Find the score text (e.g., "90%") with `children.length === 0` and `y > 400` (in results area, not nav). Click its parent row. URLs change to `/evaluation/runsDetails/{testSetId}/{runId}`.

## Edit Button Reliability

### Overview Page vs Settings Page
- **Overview**: Edit buttons at y=146 (Description), y=789-904 (Instructions), y=2385+ (Suggested prompts). Instructions Edit frequently fails to activate editor.
- **Settings page** (`/settings/agent/instructions`): Edit buttons more reliable but page may redirect to Overview.

### PT-Specific
PT editor opens as `role="textbox"` (not contenteditable). Use `document.querySelectorAll('[role="textbox"]')` to find it.

### SLP/OT-Specific
Editors open as `contenteditable="true"`. Use `document.querySelectorAll('[contenteditable="true"]')`.

### Brute Force
If specific Edit button fails, iterate all Edit buttons with Cancel between attempts:
```javascript
for (let i = 0; i < 4; i++) {
    await page.evaluate(idx => { /* click Edit #idx */ }, i);
    await sleep(4000);
    const ok = await page.evaluate(() => document.querySelectorAll('[contenteditable="true"]').length > 0);
    if (ok) break;
    await page.evaluate(() => { /* click Cancel */ });
    await sleep(2000);
}
```
