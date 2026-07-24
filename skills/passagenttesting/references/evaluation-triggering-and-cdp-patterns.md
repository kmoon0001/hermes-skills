# Evaluation Triggering & CDP Connection Patterns (Jun 2026)

## Triggering Evaluations via the Browser UI

The Copilot Studio evaluation page has a non-obvious button hierarchy:

### Correct Button Sequence
1. Navigate to `.../bots/{botId}/evaluation`
2. Click **"New evaluation"** (top of page toolbar, NOT the "Evaluate" buttons on cards)
3. In the dialog that opens, click **"Run"**
4. Wait ~15 min for 100 SR cases, ~5 min for 20 Conv cases

### Common Pitfall — Wrong "Evaluate" Button
There are THREE different "Evaluate" buttons on the same page, all with identical text:
- **"New evaluation"** — correct entry point (click this)
- **"Evaluate" on test set cards** — opens test set details, NOT a new run
- **"Evaluate" on recent-result rows** — re-runs the old test set against the OLD agent version, NOT the current published agent

Clicking the wrong Evaluate button silently does nothing useful. The run appears to start but the scores never update.

### Progress Monitoring
After clicking Run, the URL transitions from `/evaluation` to `/evaluation/run` or includes a run ID. Look for this URL change to confirm the run was accepted. The SPA may not show a visible progress bar through CDP.

## CDP Connection Saturation

### Symptom
After opening ~15-20 tabs in the same Chrome CDP session, new WebSocket connections fail with:
```
Error: Unexpected server response: 500
```

### Root Cause
Chrome caps the number of concurrent DevTools WebSocket connections. Each `curl -X PUT "http://127.0.0.1:9223/json/new?...` creates a new tab AND a new WebSocket slot. The limit is reached when tabs are NOT closed between operations.

### Prevention
- Reuse existing tabs instead of creating new ones for each navigation
- Close unused tabs: `curl -s -X DELETE "http://127.0.0.1:9223/json/close/{pageId}"`
- Keep 3-4 tabs max (one per agent + one blank)
- If saturation occurs, restart Chrome with the debug profile

### Detection
Run `curl -s http://127.0.0.1:9223/json | python3 -c "import sys,json; print(len(json.load(sys.stdin)))"` — if >15, you're approaching the limit.

## SPA /topics URL Redirect

The Copilot Studio SPA redirects direct URL navigation to `/topics` (or `/environments/{envId}/bots/{botId}/topics`) back to `/overview`. 

To reach the topics list:
1. Load `/overview` first
2. Wait 10-15s for SPA to fully render
3. Find the "Topics" tab in the nav bar and click it via MouseEvent (not .click())
4. Wait 5-10s for topics list to render

The tab click may sometimes navigate to `/tools` instead of topics (observed on SLP_Specialist, Jun 14 2026). If this happens, re-navigate to `/overview` and retry.
