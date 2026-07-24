# Multi-Agent Conversational Boosting Check & Fix

When auditing multiple Copilot Studio agents for the CB refusal problem, follow
this pattern. All navigation uses CDP `Input.dispatchMouseEvent` (proven reliable
against FluentUI backdrops). Clipboard paste + space/backspace wakes the save
tracker.

## Quick Check: CB ON/OFF + Refusal Status

Read the System topics DataGrid without opening the topic editor:

```javascript
const cbRow = await page.evaluate(() => {
  const rows = document.querySelectorAll('[role="row"]');
  for (const row of rows) {
    if (row.textContent?.includes('Conversational boosting')) {
      const text = row.textContent;
      // Distinguish "On" status from "On Error", "On Talk", etc.
      const isOn = text.includes('On') && 
        !text.includes('On Error') && !text.includes('On Talk') && 
        !text.includes('On Sign') && !text.includes('On Conversation');
      return { text: text.substring(0, 150), isOn };
    }
  }
  return null;
});
// If CB is OFF → no fix needed
// If CB is ON → open topic editor and check activity text
```

## Agent-Specific Activity Text

Each agent's CB redirect should use agent-specific language (no commas, no
question marks, no contractions, all on one line):

| Agent | Activity text |
|-------|--------------|
| OT | `I can help with OT documentation compliance including evaluation audits daily note reviews progress note checks recertification analysis discharge summaries and denial risk assessment. Could you provide more detail about what you would like me to evaluate?` |
| TDA | `I can help with therapy documentation audits including compliance reviews denial risk analysis progress note checks evaluation audits and discharge summary reviews. Could you provide more detail about what you would like me to audit?` |
| PT | (same pattern with PT-specific capabilities) |
| SLP | (same pattern with SLP-specific capabilities) |

## Full Fix Flow (per agent)

1. Check CB status via grid row text
2. If OFF → skip
3. If ON → click CB link, More > Open code editor
4. Read current YAML, extract old activity via splice positions
5. Replace just the activity text (preserve all other YAML)
6. Clipboard paste + space/backspace wake
7. Save + Publish

The CB YAML uses `SearchAndSummarizeContent` action kind (NOT `CreateGenerativeAnswers`).
The action kind `CreateGenerativeAnswers` was removed in newer Copilot Studio versions
and causes: `Unknown element at path BeginDialog.Actions.Actions[0]`.

## NBSP Normalization

Monaco's `.view-lines` textContent uses `\u00a0` (non-breaking spaces) instead of
regular spaces. Always normalize before string-matching:

```javascript
function norm(text) { return text?.replace(/\u00a0/g, ' ') || ''; }
```
