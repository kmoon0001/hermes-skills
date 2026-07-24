# TheraDoc Publish Error Masking Pattern

A 45-topic card-based agent (TheraDoc Workbench) showed how publish errors mask each other. Fixing one layer revealed the next.

## Error Layer Sequence

| Layer | Error Count | What was fixed | How |
|-------|-------------|----------------|-----|
| 1 | 22 | Missing dialog `AuditExistingNote` | Replaced refs with `ComplianceAuditV2` (inactive), then activated it, then removed the refs entirely |
| 2 | 20 | `Topic.Answer` identifier errors | SASC had no `variable:` — output was lost. Added `variable: Topic.Answer` + fixed SendActivity references |
| 3 | 19 | `Concatenate()` / `Text()` Power Fx errors | SASC `userInput` used `=Concatenate(...)` instead of `=System.Activity.Text`. The massive inline Power Fx expression was malformed. |
| 4 | 13+89 | Missing `outputType` + `errorMessage` | Actually NOT about card inputs — these were **output binding errors** from a managed Power Automate flow. Adding `outputType: {}` and `errorMessage: "Required"` had zero effect because the real issue was elsewhere. |
| 5 | 89+53 | Output binding errors (52 fields not found) | All from a **managed flow** (`TheraDoc – Compliance Audit Flow`, ismanaged=True) that couldn't be deleted via API. The flow's Adaptive Card input schema expected 52 card field names that the topic's `outputType` didn't declare. Adding the 52 fields to MasterPatientContext's outputType had NO effect (wrong scope). |

## Key Lessons

1. **Publish iteratively** — Fix one error category at a time, then publish. The remaining errors will change. DO NOT try to fix all at once — you'll fix things that aren't actually the problem.

2. **"Output binding 'X' is not found"** means a Power Automate flow expects fields the topic doesn't output. Check the `workflows` table:
   ```sql
   SELECT workflowid, name, statecode, ismanaged FROM workflows 
   WHERE contains(name, 'CrossAgent') OR contains(name, 'ComplianceAudit')
   ```

3. **Managed flows** (ismanaged=True) can't be deleted via Dataverse API (405 Method Not Allowed). They must be removed from Copilot Studio UI → Flows tab → Remove.

4. **Draft flows still block publish.** Even if a flow is in Draft state (not Activated), the publish validation still checks its output bindings.

5. **The "Required adaptive-card input is missing an error message" error** (89 occurrences) was MISDIAGNOSED as missing `errorMessage` on card inputs. It was actually Power Automate flow binding errors misreported by the validation. Always check the `workflows` table when seeing this error.

## Detection Script

```python
import json, urllib.request, os
TOKEN = open("az_token.txt").read().strip()
BASE = "https://<org>.crm.dynamics.com/api/data/v9.2"
H = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}

# Find all flows for a bot
filter_str = "contains(name,'TheraDoc') or contains(name,'CrossAgent') or contains(name,'ComplianceAudit')"
url = f'{BASE}/workflows?$filter={urllib.parse.quote(filter_str)}&$select=workflowid,name,statecode,ismanaged'
req = urllib.request.Request(url, headers=H)
with urllib.request.urlopen(req, timeout=15) as r:
    flows = json.loads(r.read()).get("value", [])
for f in flows:
    print(f'{f.get("name","?")}: state={f.get("statecode")} managed={f.get("ismanaged")}')
```
