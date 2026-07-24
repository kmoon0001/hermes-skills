# Test Pane Overlay Issue (June 17, 2026)

## Problem

When evaluating Copilot Studio agents via CDP, the evaluation page loads but result scores (e.g., "85%", "90%") are not clickable because the **test pane overlay** covers the right portion of the page where scores appear.

## Symptoms

- Evaluation page loads with ~18,000 chars of DOM text
- "Recent results" section is visible in raw text
- Clicking score percentages (e.g., "85%") does NOT navigate to run details
- Scores appear at x~1400, y~500-700 — covered by test pane
- `page.mouse.click()` on score coordinates navigates to wrong page (overview/agents/topics)

## Fix

**Close the test pane first** before interacting with evaluation results:

```javascript
// Click the Test button (flask icon) to close the test pane
// Test button is at x~1094, y~53
await page.mouse.click(1094, 53);
await sleep(5000);

// Now evaluation scores are clickable
// Find "85%" or "90%" text and click
```

## Alternative

Navigate from Overview → click Evaluation tab with test pane closed. The SPA retains pane state.

## Detection

If `page.url()` stays on `/evaluation` after clicking a score, the click hit the test pane overlay, not the eval result.
