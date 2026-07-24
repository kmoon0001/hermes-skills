# Eval Regression Investigation Pattern

## When eval drops massively (e.g., 95% → 12%)

### Step 1: Isolate the cause
1. Delete all recently added/modified topics via Dataverse API
2. Republish via PAC CLI
3. Re-run single-response eval
4. If score recovers → the new topics caused it
5. If score stays low → something else changed (model, instructions, knowledge sources)

### Step 2: If new topics caused it
- Check `data` field: must be empty shell (~121 chars), NOT full content
- Check trigger queries: may overlap with existing topics
- Check topic format: simple text-answer + EndDialog performs best
- Interactive topics (menus, cards, wizards) kill eval scores

### Step 3: If something else changed
- Check agent model (should be GPT-5 Chat for CS agents)
- Check agent instructions via Dataverse API or UI
- Check knowledge source status (should all be "Ready")
- Check if publish corrupted any topic content

## Power Platform Eval REST API

Can trigger evals programmatically without browser UI:

```
GET  test sets:  https://api.powerplatform.com/copilotstudio/environments/{ENV_ID}/bots/{BOT_ID}/api/makerevaluation/testsets?api-version=2024-10-01
POST run eval:   https://api.powerplatform.com/copilotstudio/environments/{ENV_ID}/bots/{BOT_ID}/api/makerevaluation/testsets/{TestSetId}/run?api-version=2024-10-01
GET  run status: https://api.powerplatform.com/copilotstudio/environments/{ENV_ID}/bots/{BOT_ID}/api/makerevaluation/testruns/{TestRunId}?api-version=2024-10-01
GET  all runs:   https://api.powerplatform.com/copilotstudio/environments/{ENV_ID}/bots/{BOT_ID}/api/makerevaluation/testruns?api-version=2024-10-01
```

**Auth**: Requires OAuth bearer token from MSAL (NOT browser cookies). The API is at `api.powerplatform.com` which is a different domain from the Dataverse org. Browser session cookies don't work due to CORS.

**Workaround**: Use the browser UI to trigger evals (Playwright CDP). The SPA is heavy but works with patience:
1. Navigate to evaluation page
2. Click "Show more" to reveal all test sets
3. Find single-response test set (100 cases)
4. Click the test set link (not the Evaluate button in results)
5. Click "Evaluate" button on detail page
6. Poll for completion (~15 min for 100 test cases)

## CDP Timeout Prevention

The Copilot Studio SPA is very heavy and causes CDP connection timeouts:
- Close all extra tabs before connecting (blob:, TokenFactory, omnibox)
- Use `chromium.connectOverCDP` with 120s timeout
- Keep only 1-2 pages open
- After heavy eval runs, Chrome may become unresponsive — restart fresh

## Eval Timing

- Single-response (100 cases): ~15 minutes
- Conversation (20 cases): ~5 minutes
- Only 1 eval can run at a time per agent
- Score appears on the eval page after all test cases complete
