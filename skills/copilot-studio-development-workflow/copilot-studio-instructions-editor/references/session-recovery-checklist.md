# Session Recovery Checklist

When resuming Copilot Studio agent work after a gap (hours/days), follow this sequence before making ANY changes. Based on June 2026 multi-session recovery.

## Step 1: Pull Current Scores

Search recent sessions for last known scores:
```
session_search(query="agent scores evaluation SLP PT TDA OT", limit=5, sort="newest")
```

If no recent scores found, pull live via CDP (requires active Chrome):
```javascript
// D:/my agents copilot studio/pull_scores.cjs
// Connects to CDP, navigates eval page for each agent, reads Recent results
```

Expected scores as of June 2026:
| Agent | SR Target | Conv Target | Notes |
|-------|-----------|-------------|-------|
| OT | 97-99% | 100% | Stable — DO NOT TOUCH |
| PT | 94-97% | 90-100% | Caregiver topic gaps |
| SLP | 90-95% | 85-100% | Hedging/citation sensitive |
| TDA | 90-96% | 95-100% | Routing agent, different rules |

## Step 2: Check Instruction Files on Disk

```
search_files(pattern="instructions*.txt", path="D:/my agents copilot studio", target="files")
```

Canonical files:
| Agent | File | Expected Chars | Format |
|-------|------|---------------|--------|
| OT | `ot_instructions_v9_final.txt` | ~3,500 | Unconditional RF — DO NOT MODIFY |
| PT | `pt_instructions_consolidated.txt` | 3,957 | Conditional RF |
| SLP | `slp_instructions_consolidated.txt` | 3,626 | Conditional RF |
| TDA | `tda_instructions_consolidated.txt` | 2,589 | Routing (no RF) |

If files are missing, check backups: `pt_instructions_final.txt`, `slp_instructions_fixed.txt`, `tda_instructions_fixed.txt`.

## Step 3: Verify Chrome CDP

```bash
curl -s http://127.0.0.1:9223/json/version
```

If no response: Chrome not running with debug port. Kill and relaunch:
```bash
cmd //c "taskkill //F //IM chrome.exe"
# Wait 3s
cmd //c start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" \
  --remote-debugging-port=9223 \
  --user-data-dir="C:\Users\kevin\AppData\Local\Google\Chrome\User Data Debug"
```

**PITFALL**: After taskkill, the terminal is broken (exit 130). Use execute_code for subsequent commands. See pitfall 0e.

## Step 4: Compare Live vs Expected Instructions

Connect CDP → navigate to each agent Overview → read instruction length:
```javascript
const instrLength = await page.evaluate(() => {
    const el = document.querySelector('[role="textbox"], [contenteditable="true"]');
    return el?.innerText?.length || 0;
});
```

Compare against expected chars (±10%). If mismatch → wrong file was pasted previously.

## Step 5: Plan Injection Sequence

Priority order (fix worst-performing first):
1. **Worst agent** — pull latest scores, identify which has lowest
2. **Inject instructions** — use Playwright fill() auto-save pattern (pitfall 0b.1)
3. **Verify** — re-read instructions after inject
4. **Publish** — click Publish button
5. **Trigger eval** — SR first (faster feedback), then Conv
6. **Wait** — SR ~15-20 min, Conv ~5-10 min
7. **Repeat** for next agent

**CRITICAL**: One agent at a time. Test after each. Never inject all 3 without testing.

## Anti-Patterns

- Injecting all agents simultaneously without testing between each
- Changing instructions without knowing current scores
- Using clipboard injection (corrupts YAML) — use Playwright fill() only
- Retrying broken terminal 7+ times (see pitfall 0e)
- Skipping verification after inject (fill() can silently fail)
