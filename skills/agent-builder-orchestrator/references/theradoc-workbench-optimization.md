# TheraDoc Workbench Optimization (2026-07-16)

## Session Profile
- **Agent:** TheraDoc Workbench (45 topics, 304 components, 33 KB sources)
- **Initial state:** Could not publish (7 blocker categories)
- **Final state:** All topic issues fixed. 1 remaining managed flow blocker needs UI removal.
- **Fixes applied:** ~30 across 45 topics

## Blocker Categories Found & Fixed

### 1. Missing responseCaptureType (22 topics)
- Every SearchAndSummarizeContent node needs `responseCaptureType: FullResponse`
- Regex fix: `re.sub(r'(kind: SearchAndSummarizeContent[^}]*?)(\\n)', ...)`
- PATCH via `botcomponents({id})/data` with escaped JSON

### 2. Variable Scope Mismatch (22 topics)
- SASC writes to `Global.Answer`, SendActivity reads `Topic.Answer` → empty output
- Fix: Ensure SendActivity reads from the SAME variable the SASC writes to
- OR add `variable: Topic.Answer` to the SASC node
- **Key lesson:** The `variable:` field goes on the SASC node, NOT the topic root

### 3. Power Fx Error in userInput (1 topic)
- `userInput: =Concatenate(...)` is NOT valid SASC userInput in all contexts
- The userInput should be the SYSTEM text input, NOT a concatenation
- Fix: `userInput: =System.Activity.Text` and put concatenation logic in `additionalInstructions`

### 4. Missing Dialog References (22 topics)
- References to renamed dialogs (AuditExistingNote → ComplianceAuditV2)
- Fix: Remove BeginDialog blocks referencing old dialog names
- Verify the new dialog exists and is active (type 9, statecode=0)

### 5. WelcomeStart Redirect (1 topic)
- `dialog: WelcomeStart` doesn't exist in custom agents
- Fix: Redirect to `ConversationStart` or remove the BeginDialog

### 6. InvokeFlowAction Without FlowId (2 topics)
- `kind: InvokeFlowAction` with `action:` field instead of `flowId:`
- Fix: Replace with `InvokeConnectedAction` + `action:` for cross-agent calls
- OR remove entirely if the flow doesn't exist

### 7. Managed Flow Blocking Publish
- `TheraDoc – Compliance Audit Flow` (managed, Draft state)
- Cannot delete via API → requires Copilot Studio UI → Flows tab → Remove
- Detected via `workflows` table: `contains(name,'Compliance')`

## Patterns That Worked

### Multiple PATCHes to the Same Component
When fixing YAML in a single botcomponent, chain replacements BEFORE sending:
```python
data = re.sub(r'pattern1', 'replacement1', data)
data = re.sub(r'pattern2', 'replacement2', data)
data = data.replace('text1', 'text2', 1)
body = json.dumps({'data': data}).encode()
PATCH ...  # ONE PATCH, not 3
```
This avoids race conditions from parallel edits to the same component.

### Batch PATCHing via Topic List
Fetch all topics for a bot, filter by name pattern, apply fix to each:
```python
url = f'{BASE}/botcomponents?$filter=_parentbotid_value eq {BOT_ID}'
comps = json.loads(urllib.request.urlopen(...).read())
for c in comps:
    if 'Audit' in c.get('name',''):
        data = fix(c['data'])
        PATCH c['botcomponentid']
```
This is 10x faster than individual reads.

### Token Refresh Pattern
The `az` token expires after ~15min on this tenant.
Always refresh before a batch PATCH or publish:
```python
import subprocess
r = subprocess.run(["az", "account", "get-access-token",
    "--resource", "https://orgbd048f00.crm.dynamics.com/",
    "--query", "accessToken", "-o", "tsv"],
    capture_output=True, text=True, timeout=30)
TOKEN = r.stdout.strip()
```
Note: `az` from git-bash spawns cmd.exe subprocesses. Kill orphaned cmd.exe after many calls.

### Orphaned cmd.exe Zombie Detection
After many `az` calls from git-bash, cmd.exe processes accumulate.
Check: `tasklist /FI "IMAGENAME eq cmd.exe" /FO LIST`
Kill: Write a PowerShell script to kill processes older than 30min:
```powershell
$cutoff = (Get-Date).AddMinutes(-30)
$orphans = Get-Process cmd | Where-Object { $_.StartTime -lt $cutoff }
foreach ($p in $orphans) { Stop-Process -Id $p.Id -Force }
```

## Tools Used
- **Dataverse REST API** (az token) — PATCH botcomponents, query bots/workflows
- **pac CLI** — `pac copilot publish --bot --environment`
- **Python** — regex replacements, JSON processing, API calls
- **cua-driver** — browser UIA inspection (limited this session due to Chrome tab switching)
