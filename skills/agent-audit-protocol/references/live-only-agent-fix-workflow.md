# Live-Only Agent Fix Workflow

Some Therapy AI Dev agents exist ONLY in Dataverse with no local workspace (`agent.mcs.yml` or `topics/` directory on disk). Example: **Case History Reviewing Agent** (`f19e1c40-...`).

## When to Use This Pattern
- `pac copilot list` shows the agent but no `agent.mcs.yml` exists locally
- User says "this agent was created in the portal, never pulled to a workspace"
- All topic YAMLs must be read from and written to Dataverse directly

## Workflow

### 1. Auth
```bash
pac auth create --environment https://orgbd048f00.crm.dynamics.com/
az account get-access-token --resource "https://orgbd048f00.crm.dynamics.com/" --query accessToken -o tsv > az_token.txt
```
`az` works on Therapy AI Dev (unlike pccapackage which 401s). Use it for PATCH.

### 2. Inventory via pac org fetch
FetchXML for `parentbotid` (NOT `_parentbotid_value` — logical attribute name):
```xml
<fetch>
  <entity name="botcomponent">
    <attribute name="botcomponentid"/>
    <attribute name="name"/>
    <attribute name="componenttype"/>
    <attribute name="statecode"/>
    <attribute name="schemaname"/>
    <attribute name="data"/>
    <filter>
      <condition attribute="parentbotid" operator="eq" value="<botId>"/>
    </filter>
  </entity>
</fetch>
```
```bash
pac org fetch -xf "C:\path\to\query.xml" > components.txt
```

### 3. Structural Assessment
Identify topics (type 9), instructions (type 15), KBs (type 14), test cases (type 19 with `kind: EvaluationData`).
Check for: FilePrebuiltEntity, SearchSpecificFiles, SearchSpecificKnowledgeSources, GPT55Chat model name, missing responseCaptureType, unconditional format bans.

### 4. Surgical PATCH (no workspace, direct to Dataverse)
Extract the component data field, apply targeted fixes, PATCH via API:
```python
TOKEN = open('az_token.txt').read().strip()
BASE = f'https://orgbd048f00.crm.dynamics.com/api/data/v9.2'
H = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json', 'If-Match': '*'}

# ALWAYS normalize \r\n → \n before regex edits, then back
data_lf = data.replace('\r\n', '\n')
# ... edit ...
fixed = data_lf.replace('\n', '\r\n')

body = json.dumps({'data': fixed}).encode()
req = urllib.request.Request(f'{BASE}/botcomponents({comp_id})', data=body, headers=H, method='PATCH')
# Expect HTTP 204
```

**PATCH format:** Entity-level `PATCH /botcomponents({id})` uses `{"data":"<yaml>"}`. NOT `{"value":"..."}` (that's for property-specific endpoints).

### 5. Publish
```bash
pac copilot publish --bot "<botId>" --environment "https://orgbd048f00.crm.dynamics.com"
```
Verify via `synchronizationstatus.lastFinishedPublishOperation.status`.

### 6. Eval
Same as workspace-based agents. List test sets, start run, poll, analyze.

## Typical Fixes for Live-Only Agents (Case History Example)
| Fix | Method |
|-----|--------|
| GPT55Chat → GPT5Chat | `str.replace` on instructions data |
| Remove "under 4 sentences" | `re.sub` on instructions data |
| Remove SearchSpecificFiles | `re.sub` with DOTALL |
| Remove SearchSpecificKnowledgeSources | `re.sub` with DOTALL |
| Add responseCaptureType | Insert after allowLatencyMessage: false (normalize CRLF first!) |
| FilePrebuiltEntity → StringPrebuiltEntity | `str.replace` |

## Pitfalls
- **CRLF regex trap:** Always normalize `\r\n` → `\n` before regex edits on Dataverse YAML. `\s*` in `re.sub` consumes `\r\n` line endings and next-line indentation → broken YAML → publish fails.
- **PATCH field name:** Entity-level uses `{"data":"..."}`, NOT `{"value":"..."}`.
- **No workspace backup:** Can't `git commit` before change. The backup IS the live data you read before PATCHing. Save it to a file.
