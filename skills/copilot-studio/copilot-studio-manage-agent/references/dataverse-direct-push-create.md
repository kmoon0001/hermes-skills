# Direct Dataverse Push/Create for botcomponents

When `manage-agent.bundle.js push` fails with the `vscode-jsonrpc/node` error, use the Dataverse REST API directly.

## Token

**Pattern C — PowerShell native (most reliable).** When Python `urllib` repeatedly returns 401 despite a valid token, the `execute_code` sandbox Python (3.11) may be using a different TLS/trust store than the system Python (3.13). The workaround is to run the entire operation via a `.ps1` script through `terminal()` instead of `execute_code`:

```bash
# terminal() — works every time
powershell -ExecutionPolicy Bypass -File "C:\path\to\script.ps1"
```

The `.ps1` script can call `az account get-access-token` fresh for each REST call, pass it to `Invoke-RestMethod`, and never has the cross-process token issue. This is the recommended approach for any multi-step Dataverse operation.

**CRITICAL: Avoid special characters in .ps1 files written via `write_file`.** Unicode characters like ✓ ✗ → ☐ ■ cause PowerShell parser failures at the file level. The `write_file` tool writes UTF-8-BOM which PowerShell reads fine, but any non-ASCII character in the file body will cause `ParserError: The string is missing the terminator`. Use plain ASCII markers (Y/N, OK/FAIL) instead.

**Pattern A — Token file (preferred for .py scripts run via terminal):**
```bash
# In terminal() — save token to file
powershell -Command "az account get-access-token --resource '<orgUrl>' --query accessToken -o tsv" > /tmp/.dv_tokenfile
```
```python
# In your Python script — read from file immediately before first use
with open("/tmp/.dv_tokenfile") as f:
    token = f.read().strip()
```

**Pattern B — Fresh capture inline (preferred for ad-hoc queries):**
```bash
TOKEN=$(powershell -Command "az account get-access-token --resource '<orgUrl>' --query accessToken -o tsv" 2>/dev/null) && curl -s -H "Authorization: Bearer $TOKEN" ...
```
The key is ONE pipeline: get token → use it. Any intermediate step (storing in a Python variable, waiting for input) causes 401s.

```python
import subprocess
result = subprocess.run(
    ["powershell", "-Command",
     "az account get-access-token --resource '<orgUrl>' --query accessToken -o tsv"],
    capture_output=True, text=True, timeout=30)
token = result.stdout.strip()
```

## Batch query all topics (preferred over one-at-a-time)

Query ALL topics for a bot in one call to build a name→schemaname map. This avoids per-token-request overhead and reveals the exact live schemaname (which may be lowercased vs your local YAML):

```python
import json, urllib.request, urllib.parse
base = "https://<org>.crm.dynamics.com/api/data/v9.2"
bot_id = "<guid>"

filt = f"_parentbotid_value eq '{bot_id}' and componenttype eq 9"
url = f"{base}/botcomponents?$filter={urllib.parse.quote(filt)}&$select=botcomponentid,name,schemaname&$top=100"

req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/json")
req.add_header("OData-MaxVersion", "4.0")
req.add_header("OData-Version", "4.0")

with urllib.request.urlopen(req, timeout=30) as resp:
    all_topics = json.loads(resp.read()).get("value", [])

# Build lookups
live_by_sn = {t["schemaname"]: t for t in all_topics}
live_by_name = {t["name"].lower(): t for t in all_topics}
```

**PITFALL: schemaname casing mismatch.** The live agent's `schemaname` is often all-lowercase even when your local YAML references use mixed case. E.g. local `pcca_theradocworkbench.topic.PTProgressNoteCard` → live `pcca_theradocworkbench.topic.ptprogressnotecard`. Always verify against the batch query result.

## Query single live topic state (targeted verification after PATCH)

```python
filt = f"_parentbotid_value eq '{bot_id}' and componenttype eq 9 and schemaname eq '<schemaname>'"
url = f"{base}/botcomponents?$filter={urllib.parse.quote(filt)}&$select=botcomponentid,name,schemaname,data&$top=1"

req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/json")
req.add_header("OData-MaxVersion", "4.0")
req.add_header("OData-Version", "4.0")

with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())
```

## Query live topic state
```python
import json, urllib.request, urllib.parse
base = "https://<org>.crm.dynamics.com/api/data/v9.2"
bot_id = "<guid>"

filt = f"_parentbotid_value eq '{bot_id}' and componenttype eq 9 and schemaname eq '<schemaname>'"
url = f"{base}/botcomponents?$filter={urllib.parse.quote(filt)}&$select=botcomponentid,name,schemaname,data&$top=1"

req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/json")
req.add_header("OData-MaxVersion", "4.0")
req.add_header("OData-Version", "4.0")

with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.loads(resp.read())
```

## PATCH existing topic
Replace the entire `data` field with new YAML. HTTP 204 = success.
```python
payload = {"data": yaml_content_string}
req = urllib.request.Request(f"{base}/botcomponents({comp_id})",
    data=json.dumps(payload).encode(), method="PATCH")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")
req.add_header("OData-MaxVersion", "4.0")
req.add_header("OData-Version", "4.0")
with urllib.request.urlopen(req, timeout=30) as resp:
    assert resp.status == 204
```

**CRITICAL PITFALL: CRLF line endings in botcomponent `data`.** The YAML `data` field uses `\r\n` (CRLF) line endings, NOT plain `\n`. Python's `str.replace()` with `\n`-only patterns silently fails — HTTP 204 succeeds but the replacement doesn't match because `\r\n` ≠ `\n`.

**Safe approaches:**
1. **Regex** (preferred for structural changes): `re.sub(r'kind: SearchSpecificFiles\n\s+files:\n(\s+- .*\n)+', 'kind: SearchAllKnowledgeSources\n', data)` — regex `\n` matches the LF portion of CRLF, and `.` matches `\r` as any-char.
2. **Explicit CRLF**: `data.replace('searchMode: Standard\r\n', 'searchMode: Enhanced\r\n')` — use `\r\n` explicitly.
3. **Verify by re-querying** — always confirm the substring is in the live data after PATCH. HTTP 204 does NOT mean the replacement matched.

**Wrong (silently fails):**
```python
# Will NOT match because actual data has \r\n, not \n
data = data.replace('responseCaptureType: FullResponse\n              modelDescription:',
                     'responseCaptureType: FullResponse\n              additionalInstructions: ...')
```

**Correct (regex):**
```python
import re
data = re.sub(
    r'responseCaptureType: FullResponse\n\s+modelDescription:',
    'responseCaptureType: FullResponse\n              additionalInstructions: |-\n                Keep responses concise.\n\n              modelDescription:',
    data
)
```

`description` field is plain single-line text — no CRLF concern there.

## POST new topic
Create a brand new botcomponent. HTTP 201 = created.
```python
payload = {
    "schemaname": "pcca_agent.topic.NewTopicName",
    "name": "Display Name",
    "componenttype": 9,                            # MUST be int, not @odata.bind
    "parentbotid@odata.bind": f"/bots({bot_id})",  # MUST be entity ref, not raw GUID
    "data": yaml_content_string,
}
req = urllib.request.Request(f"{base}/botcomponents",
    data=json.dumps(payload).encode(), method="POST")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/json")
req.add_header("Content-Type", "application/json")
req.add_header("OData-MaxVersion", "4.0")
req.add_header("OData-Version", "4.0")
req.add_header("Prefer", "return=representation")
with urllib.request.urlopen(req, timeout=30) as resp:
    created = json.loads(resp.read())
    new_id = created.get("botcomponentid")
```

## Known error codes
| Status | Error pattern | Cause | Fix |
|--------|---------------|-------|-----|
| 400 | `ODataPrimitiveValue was instantiated with a value of type 'ODataEntityReferenceLink'` | Used `@odata.bind` where primitive int expected (componenttype) or vice versa | `componenttype: 9` (int), `parentbotid@odata.bind: "/bots(GUID)"` (entity ref) |
| 400 | `A 'PrimitiveValue' node with non-null value was found when trying to read the property 'parentbotid'` | Sent raw GUID for `parentbotid` instead of `parentbotid@odata.bind` | Use `parentbotid@odata.bind` syntax |
| 400 | `The property 'displayname' does not exist on type botcomponent` | Sent `displayname` field | Drop it — not a valid OData property on botcomponents |
| 400 | `The parameter 'asyncPublish' is not a valid parameter for the operation 'PvaPublish'` | Sent body with asyncPublish param | Call PvaPublish with empty POST (no body) |
| 200 | `PublishedBotContentId` is empty in PvaPublish response | Publish silently failed | Try `pac copilot publish` or Copilot Studio UI |
| **204** | **Patch succeeds but replacement doesn't match (silent no-op)** | str.replace() with `\n` didn't match CRLF `\r\n` in botcomponent `data` field | Use regex or explicit `\r\n` — see CRLF pitfall above |

## Verify
Always re-query after PATCH/POST:
```python
filt = f"_parentbotid_value eq '{bot_id}' and componenttype eq 9 and schemaname eq '{sn}'"
url = f"{base}/botcomponents?$filter={urllib.parse.quote(filt)}&$select=botcomponentid,name,data"
req = urllib.request.Request(url)
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Accept", "application/json")
with urllib.request.urlopen(req, timeout=30) as resp:
    vals = json.loads(resp.read()).get("value", [])
    assert len(vals) > 0, f"Topic {sn} not found in live agent!"
    live_data = vals[0].get("data", "")
    assert "modeldescription:" in live_data, "modeldescription patch did not stick"
```
