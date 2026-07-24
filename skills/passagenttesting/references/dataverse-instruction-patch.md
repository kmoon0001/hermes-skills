# Dataverse API Instruction PATCH Pattern (June 2026)

## Problem

CDP Monaco editor injection fails to persist because:
1. `textarea.value` setter doesn't sync to Monaco's internal model
2. React dirty-state requires real user keystrokes (CompositionEvent enables Save but content doesn't persist)
3. Finding Monaco's iframe and calling `editor.executeEdits()` requires navigating React fiber trees

## Solution: Dataverse API PATCH for Agent Instructions (componenttype 15)

Agent instructions are stored as YAML in the `data` field of `botcomponent` records with `componenttype eq 15`. The Dataverse Web API can PATCH this directly — no React, no Monaco, no dirty-state.

### Proven Workflow

```javascript
// 1. Navigate to Dataverse (auths via browser session)
await page.goto('https://org3353a370.crm.dynamics.com/main.aspx');
await sleep(8000);

// 2. Read current instructions
const filter = "_parentbotid_value eq '" + botId + "' and componenttype eq 15";
const url = '/api/data/v9.2/botcomponents?$select=botcomponentid,data&$filter=' + encodeURIComponent(filter) + '&$top=1';
const resp = await fetch(url, {
  credentials: 'include',
  headers: { 'Accept': 'application/json' }
});
const json = await resp.json();
const comp = json.value[0];
const rawData = comp.data; // This is YAML, not JSON

// 3. Modify via string replacement (exact string matching)
let newData = rawData.replace(
  'Use for full document audits only (evaluation, daily note, progress note, recertification, discharge):',
  'Use for ALL document-related questions (evaluation, daily note, progress note, recertification, discharge, caregiver competency, compliance check, audit request):'
);

// 4. PATCH
const patchResp = await fetch('/api/data/v9.2/botcomponents(' + comp.botcomponentid + ')', {
  method: 'PATCH',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ data: newData })
});
// Status 204 = success

// 5. Republish via SPA
```

### What You Can PATCH via Dataverse

| Field | Type | Use |
|-------|------|-----|
| `data` | YAML string | Instructions, model config, capabilities |
| `statecode` | 0/1 | Activate (0) or deactivate (1) topics |
| `description` | String | KB descriptions, topic descriptions |

### Key Evidence

**June 16, 2026 — SLP Instructions Fix:**
- Changed RESPONSE FORMAT from conditional ("full document audits only") to unconditional ("ALL document-related questions")
- Changed best-effort language from vague ("checklist, score/risk framework, escalation summary") to specific ("using the RESPONSE FORMAT")
- PATCH'd via Dataverse API → Status 204 → Published → Verified

**June 16, 2026 — PT Instructions Fix:**
- Same conditional → unconditional RESPONSE FORMAT fix
- PATCH'd via Dataverse API → Status 204 → Published

**June 15-16, 2026 — PT Guard Topic Activation:**
- 16 inactive topics activated via `PATCH { statecode: 0 }`
- Conv score went from 74% → 95%

### Pitfalls

1. **The `data` field contains YAML, not JSON.** Do not try `JSON.parse()` — it will fail. Use raw string replacement.
2. **Exact string matching required.** Even minor whitespace differences cause replacements to silently fail. Read the exact text via the API first.
3. **Must republish after PATCH.** PATCH updates the component but the agent still runs the last published version. Publishing is the activation step.
4. **CRLF vs LF.** The data field may contain `\r\n` line endings. Match the exact bytes from the API response.
5. **⚠️ Revert via `replace()` can corrupt instructions.** When reverting a RESPONSE FORMAT change (unconditional→conditional), the old/new text patterns may partially match, creating duplicates or malformed content. **Evidence:** PT instructions grew from ~7200 chars to 8709 chars after a conditional→unconditional→conditional revert cycle. TDA also corrupted (94%→88%). **Prevention:** Always check `newData.length` against the original `rawData.length` before PATCHing. If they differ by >10%, the replace created duplicates. **Fix:** Restore from the original `data` field (re-read from API), not a second replace cycle.
