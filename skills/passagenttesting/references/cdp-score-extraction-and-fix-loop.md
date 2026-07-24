# CDP Score Extraction & Iterative Fix Loop

## Score Extraction via CDP (When REST API Unavailable)

### Prerequisites
- Chrome running on port 9223 with Copilot Studio auth
- An existing tab already on a Copilot Studio page (fresh tabs using `Page.navigate` often fail to render the SPA)
- Node.js `ws` module

### Quick Scripts (in `scripts/`)

```bash
# Read evaluation scores from a page that already has the Recent results grid loaded
node scripts/get_scores.cjs <PAGE_ID> "OT" 15

# Read a wide swath of page text (useful after clicking into a run)
node scripts/read_full.cjs <PAGE_ID> "Fail"
```

### Workflow

1. **Open a tab** to `/evaluation` directly via `curl -X PUT http://127.0.0.1:9223/json/new?...`
2. **Wait 25-30s** for the SPA to hydrate. CDP `Page.navigate` often renders only 50-200 chars initially.
3. **Click the "Evaluation" tab** if the page shows the test/overview panel instead of the evaluation grid. Find the tab button by searching all elements for text "Evaluation" and calling `.click()`.
4. **Read scores** with `get_scores.cjs`.
5. **To see failures:** Click the run name button (not the row center) in the Recent results grid. Wait 10s for the run details page. Read with `read_full.cjs`.
6. **To see specific fail tab:** After the run details loads, click the "Fail (N)" tab button.

### Pitfalls
- **CDP connection saturation:** Opening >15 tabs causes 500 errors on new WebSocket connections. Close unused tabs.
- **SPA fails to render:** If `document.body.innerText` shows only the nav header (50-200 chars), the SPA didn't hydrate. Try navigating from an existing CS tab instead of creating a fresh one.
- **Run-name click:** In the Fluent UI grid, clicking the row center does NOT navigate to run details. Click the actual run-name text/button (leftmost cell).
- **Page redirects:** Evaluating `/evaluation` directly skips the Overview redirect. But the tab may land on the Test panel instead of the evaluation grid. Click the "Evaluation" nav tab first.

## Iterative Fix Loop Structure

The core pattern for the multi-agent fix loop — repeat for each agent.

### Loop Sequence

```
AGENT = next agent needing fixes
SCORE_TARGET = 95% for both SR and Conv

while agent_score < SCORE_TARGET:
  1. GAP ANALYSIS:
     - Read latest evaluation run failures
     - Classify each failure into root cause categories
     - Identify pattern: instruction-level vs topic-level vs knowledge vs grading

  2. CREATE FIX CHECKLIST:
     - Numbered items, scoped to THIS AGENT only
     - Each fix addresses ONE root cause category
     - Include the specific file/component to change (instructions, topic YAML, KB)

  3. APPLY FIXES:
     - One fix at a time (instructions first, then topics, then KB)
     - Publish after each batch
     - Verify publish status

  4. TRIGGER EVALUATION:
     - Correct sequence: "New evaluation" → "Run" (NOT clicking "Evaluate" on individual test set cards)
     - Wait for completion (10-15 min for 100 SR, ~5 min for 20 Conv)

  5. REVIEW RESULTS:
     - Record score before/after
     - Check if failures shifted to DIFFERENT topics (regression cascade signal)
     - If score improved but not at target → log what worked, re-triage residual failures
     - If score dropped → roll back the change and try a different approach
     - If score stayed flat → the root cause was wrong, re-classify

  6. DECISION:
     - Score >= 95% for BOTH SR and Conv → mark agent DONE, move to next agent
     - Score < 95% → continue loop for same agent
     - Three consecutive cycles with no improvement → document blocker, move on
```

### Cross-Agent Handling
- Fix ONE agent at a time. Never spread fixes across multiple agents in a single pass.
- When moving to the next agent, do NOT assume the same fix pattern applies. Each agent has unique instruction/topic/routing issues.
- Exception: SharePoint KB changes and environment-wide settings (ungrounded responses) affect ALL agents simultaneously and should be fixed first.

### Regression Cascade Detection
After each fix + evaluation pass, check TWO things:
1. Did the failure COUNT decrease? (good sign)
2. Did the failing TOPICS change? (regression cascade signal)

If the same number of tests fail but different topics are failing, the fix was correct but incomplete — the same root cause exists in OTHER topics too. For example:
- Fixing 800-char limit in Topic A → Topic A passes, but Topic B (same 800-char limit) now fails
- Fix: batch-apply the same fix to ALL topics with that root cause

## Evaluation Trigger Button Sequence (CDP)

Correct approach to trigger a new evaluation run via CDP:

```javascript
// Method A: Click "Evaluate" on the test set card (most reliable)
// Find the test set card by data type, then click its Evaluate button
await page.evaluate(() => {
  const all = document.querySelectorAll('*');
  for (const el of all) {
    const txt = el.textContent.toLowerCase();
    // For Conv: "20 test case" + "conversation"
    // For SR: "100 test case" + "single response"
    if (txt.indexOf('20 test case') >= 0 && txt.indexOf('conversation') >= 0 && txt.indexOf('last modified') >= 0) {
      const btns = el.querySelectorAll('button');
      for (const b of btns) {
        if (b.textContent.trim().toLowerCase() === 'evaluate') { b.click(); return; }
      }
    }
  }
});
// Method B: "New evaluation" button opens a TEST SET CREATOR, not a run dialog.
// Avoid using it to run existing test sets.

// 2. Wait 3-5s for dialog to open

// 3. Click "Run" button in the dialog
await page.evaluate(() => {
  for (const b of document.querySelectorAll('button')) {
    if (b.textContent.trim().toLowerCase() === 'run' && b.offsetParent !== null) {
      b.click(); return;
    }
  }
});
```

### Rate Limit
Only ONE evaluation can run at a time across ALL agents. If "Run" is disabled, wait for the current eval to finish. The "New evaluation" button being enabled does NOT mean you can run — check if "Your evaluation is running in the background" text appears on the page.
