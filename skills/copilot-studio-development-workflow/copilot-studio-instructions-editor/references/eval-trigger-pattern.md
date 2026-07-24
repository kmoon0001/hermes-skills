# Evaluation Triggering & Polling — Proven CDP Pattern (June 2026)

## Triggering a New Evaluation

The correct flow is: click test set card → Evaluate button → Run in dialog.
Do NOT use the "New evaluation" button — it requires CSV upload.

### Method 1: Direct URL (Most Reliable)

Navigate directly to configsDetails — avoids card click SPA issues:

```javascript
const testSetId = '0ce8037e-...'; // Get from prior URL or REST API
await p.goto('https://copilotstudio.microsoft.com/environments/' + env + '/bots/' + botId + '/evaluation/configsDetails/' + testSetId, { waitUntil: 'domcontentloaded', timeout: 30000 });
await sleep(15000);
// scrollIntoView + CDP click Evaluate (see below)
```

Known test set IDs (June 2026, env Default-03cc92c3):
- PT Conv: `0ce8037e-482e-4fa3-bff3-1c013fae16d0`
- TDA Conv: `73179638-d0ec-4359-816f-92ec74c2065d`
- SLP: varies — capture from URL after manual card click

### Method 2: Card Click (Fallback)

```javascript
await page.goto('.../evaluation', { waitUntil: 'domcontentloaded' });
await sleep(15000);
// Close Test pane first
await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Test');
    if (btn && btn.getBoundingClientRect().width > 0) btn.click();
});
await sleep(2000);
// Find card (20 test cases for Conv, 100 for SR)
const card = await page.evaluate(() => {
    const all = document.querySelectorAll('*');
    for (const el of all) {
        const t = el.textContent || '';
        const r = el.getBoundingClientRect();
        if (t.includes('20 test cases') && t.includes('Conversation') && r.width > 200 && r.width < 600 && r.height > 30 && r.height < 200) {
            el.scrollIntoView();
            return { x: r.x + r.width/2, y: r.y + r.height/2 };
        }
    }
    return null;
});
await sleep(1000);
// Click via CDP
const client = await page.context().newCDPSession(page);
await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: card.x, y: card.y, button: 'left', clickCount: 1 });
await sleep(50);
await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: card.x, y: card.y, button: 'left', clickCount: 1 });
await sleep(10000);
```

## Evaluate Button Requires scrollIntoView (June 18, 2026)

The Evaluate button on configsDetails page sits in a sticky footer at y≈1958, outside the viewport. CDP and Playwright clicks at that position silently do nothing — no dialog, no eval start, no error. **Fix:**

```javascript
// scrollIntoView first
await p.evaluate(() => {
    const btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate');
    if (btn) btn.scrollIntoView({ behavior: 'instant', block: 'center' });
});
await sleep(2000);
// Get updated coords (button moves from y≈1958 to y≈762)
const btn = await p.evaluate(() => {
    const b = Array.from(document.querySelectorAll('button')).find(b => b.textContent?.trim() === 'Evaluate' && !b.disabled);
    if (b) { const r = b.getBoundingClientRect(); return { x: r.x+r.width/2, y: r.y+r.height/2 }; }
});
// Click via CDP Input.dispatchMouseEvent
const client = await p.context().newCDPSession(p);
await client.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
await sleep(50);
await client.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: btn.x, y: btn.y, button: 'left', clickCount: 1 });
await sleep(10000);
// Should show "Preparing test cases..." or navigate to runsDetails
```

**No dialog appears** — the skill previously documented a "Manage profile and connections" dialog with a "Run" button. In practice (June 2026), clicking the Evaluate button directly starts the eval without a dialog. The page navigates to `/runsDetails/` or shows "Preparing test cases...".

## Polling for Results

Use a fresh page (no Test pane overlay):

```javascript
const pollPage = await ctx.newPage();
await pollPage.goto('.../evaluation', { waitUntil: 'domcontentloaded' });
await sleep(20000);
const text = await pollPage.evaluate(() => document.body?.innerText || '');
const ri = text.indexOf('Recent results');
const section = text.substring(ri, ri + 2000);
// Parse runs: look for YYMMDD_HHMM pattern + score percentage
await pollPage.close();
```

## Eval Run Naming

Runs follow timestamp format: `YYMMDD_HHMM` (e.g., `260618_2025` = June 18, 8:25 PM)

## Common Failure Modes

### Test Pane Hijack
If the eval page shows "Test your agent" instead of results, the Test pane is overlaying. Fix: click Test button to toggle OFF, or open `context.newPage()`.

### Eval Scores During Active Development Are Unreliable (June 18, 2026)
When instruction edits or publish operations are in progress, evaluation runs triggered during that window produce 0-30% scores. The agents themselves may be fully functional (verified via Test pane). **Rule:** Never diagnose agent quality from eval runs that overlap with edit/publish operations. Always verify via Test pane first.

### Simultaneous 0% Across All Agents = Platform Issue (June 18, 2026)
When PT, SLP, and TDA all dropped from 90-100% to 0% at the same time (~3:37-3:50 PM), the root cause was NOT per-agent config. **OT (untouched since yesterday) ALSO returned 0% when tested as a control** — confirming platform-wide evaluation service failure. The key diagnostic: run an UNMODIFIED agent as a control. If it also fails, the issue is platform-level.

**Diagnosis checklist:**
1. Check if break time coincides with edit/publish → unreliable scores
2. Check if ALL agents or only modified agents affected
3. **Run an UNMODIFIED agent as control** (e.g., OT if you only changed PT/SLP/TDA). If control also returns 0% → confirmed platform issue.
4. If only modified: re-publish cleanly and re-test
5. If ALL agents (including control): platform-level issue (model endpoint, eval service auth)
6. Verify via Test pane → if Test works but evals show "Error", eval service has different auth path than Test pane
7. Try REST API or pac CLI as alternative eval path
8. Check admin portal for service health advisories
9. Wait and retry (transient platform issues may resolve in hours)

### "Error" Status (Not Just Low Score)
When all test cases show "Error" with 3 messages each, the evaluation service gets an error response from the agent. This is a technical failure, not quality grading. Possible causes:
- Published version has broken topic or KB connection
- Evaluation service authentication expired
- Model endpoint returning errors for eval context
- Re-publishing may or may not fix — if it doesn't, it's likely platform-level

### Diagnostic Matrix

| Test Pane | Evals | Likely Cause |
|-----------|-------|-------------|
| ✅ Works | ✅ Works | Agent healthy |
| ✅ Works | ❌ Error 0% | Published version or eval service issue |
| ❌ Fails | ❌ Fails | Agent config broken |
| ✅ Works | Low score | Instruction/topic quality issue |

When Test pane works but evals return "Error" on ALL cases:
1. Re-publish the agent
2. Trigger fresh eval
3. If still 0% → platform issue, wait and retry
4. Check "Allow ungrounded responses" setting

## Rate Limiting

Only 1 eval per agent at a time. Second eval queues or fails.
Conv evals (20 cases): ~8-10 minutes
SR evals (100 cases): ~15-20 minutes
