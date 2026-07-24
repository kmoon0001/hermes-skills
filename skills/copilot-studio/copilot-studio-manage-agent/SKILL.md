---
name: copilot-studio-manage-agent
description: Push, pull, clone, publish, and validate Copilot Studio agent content via manage-agent.bundle.js LSP binary.
tags: [copilot-studio, dataverse, push, pull, clone, publish, validate, rollback, revert]
---

# Manage Agent

Push, pull, clone, publish, and validate Copilot Studio agent content via the VS Code extension's LanguageServerHost LSP binary.

## IMPORTANT: Do Not Modify Scripts
manage-agent scripts are pre-built bundles. If script fails:
1. Report error as-is
2. Do not attempt to fix
3. Direct user to https://github.com/microsoft/skills-for-copilot-studio/issues
4. Fall back to direct Dataverse REST API (see "Direct Dataverse Push/Create Workflow" below)

## CRITICAL: Source of Truth — Live UI Wins

**Live UI = source of truth. Local files = backup snapshots only.**
**NEVER push local→live without explicit user direction. Live-only editing.**

When Kevin is editing in Copilot Studio UI, do NOT sync local YAML to live.
Local is a read-only backup pulled FROM live, never the other direction.

**User stop signal:** If Kevin says “don’t do anything,” “stop,” or asks to “just figure out the root cause,” switch to read-only mode immediately: Dataverse GET/query, local parse/validation, and explanation only. Do not PATCH, publish, push, or run repair scripts until he explicitly re-authorizes changes. In this mode, make the final answer bottom-line first: root cause, exact topic/line, and why it happened; avoid broad remediation unless asked.

### Sync Local From Live (backup)

When Kevin finishes a UI editing session and wants the local backup updated:

1. Get Dataverse token: `az account get-access-token --resource 'https://<org>.crm.dynamics.com'`
2. Query botcomponents where `_parentbotid_value eq '<botId>' and componenttype eq 9` → write each `data` field to `.mcs.yml`
3. Query where `componenttype eq 15` → extract GPT instructions from `instructions:` block
4. Remove local files with no live match
5. `git status`, commit as backup snapshot

See skill `copilot-studio-live-sync-backup` for the full script.

### When Pushing IS Appropriate (rare — user must opt in)

Only push local→live when Kevin explicitly says so. The pattern:
1. Pull live first (ensure you're not overwriting newer live changes)
2. Edit local .mcs.yml files  
3. Validate locally with schema-lookup
4. Push to Dataverse via manage-agent push (LSP) OR direct REST API fallback
5. **Query live Dataverse to confirm changes took effect**
6. Publish the agent

## Prerequisites
1. Copilot Studio VS Code extension installed (ms-copilotstudio.vscode-copilotstudio)
2. Environment details from .mcs/conn.json (tenant ID, environment ID, environment URL, agent management URL)

### Auth
Two auth flows:
- Push/pull/clone/changes/list-agents: interactive browser login, tokens cached 90 days
- Auth command: device code flow for chat/test token

No separate auth step needed before push/pull. Commands handle token acquisition automatically.

### Token handling on Windows (Dataverse API)
When using the direct Dataverse REST API (not LSP), `az account get-access-token -o tsv` returns ~2930-char tokens that truncate in terminal output. **Save to file first:**
```bash
az account get-access-token --resource 'https://<org>.crm.dynamics.com' --query accessToken -o tsv > "C:/Users/<user>/Desktop/az_token.txt"
```
Then read in Python:
```python
with open("C:/Users/<user>/Desktop/az_token.txt") as f:
    token = f.read().strip()
```

**Python 3.13 `_validate_path` breaks inline OData URLs:** Python 3.13 introduced strict
`http.client._validate_path` that raises `InvalidURL` on any space or control character in the
URL path. Simple `urllib.parse.quote()` on an f-string is NOT enough — `urlparse()` + `quote()`
on the path component only + resetting `req.selector` and `req.full_url` is required:

```python
p = urllib.parse.urlparse(url)
encoded_path = urllib.parse.quote(p.path, safe='/@:$&?=%,')
safe_url = urllib.parse.urlunparse(p._replace(path=encoded_path))
req = urllib.request.Request(safe_url, headers=h)
req.selector = encoded_path
req.full_url = safe_url
```

**Cleanest workaround:** use `az rest` for all GET queries (it handles URL encoding internally),
and fall back to Python `urllib` only for PATCH/POST where the target URL has no query string.
This avoids `_validate_path` entirely on the read path.

**Verification via `az rest` (not Python urllib):** Python `urllib` has OData `$select` URL encoding issues on Windows. Use `az rest`:
```bash
az rest --resource "https://<org>.crm.dynamics.com/" --method GET \
  --url "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents(<id>)?\$select=name,data" -o json
```

## Commands

### Pull (download remote changes)
```bash
node "D:/my agents copilot studio/pipeline/scripts/manage-agent.bundle.js" pull --workspace <path> --tenant-id <id> --environment-id <id> --environment-url <url> --agent-mgmt-url <url>
```

### Push (upload local changes)
ALWAYS pull before push to get fresh row versions (avoids ConcurrencyVersionMismatch).
Push auto-validates all .mcs.yml files before pushing. Add --force to bypass (not recommended).
```bash
node "D:/my agents copilot studio/pipeline/scripts/manage-agent.bundle.js" push --workspace <path> --tenant-id <id> --environment-id <id> --environment-url <url> --agent-mgmt-url <url>
```

**PITFALL: `push` can fail with `Cannot find module 'vscode-jsonrpc/node'`** — the same LSP dependency issue documented for `validate` also affects `push`. When this happens, fall back to direct Dataverse REST API for PATCH (existing topics) and POST (new topics) — see "Direct Dataverse Push/Create Workflow" below. Do NOT attempt to fix the bundle.

### Clone (download agent to new local folder)
Requires --agent-id or --url. Uses Island API token automatically.
With URL (recommended):
```bash
node "D:/my agents copilot studio/pipeline/scripts/manage-agent.bundle.js" clone --workspace <path> --tenant-id <id> --url <copilotStudioUrl>
```

### Validate (check YAML before pushing)
Validates all .mcs.yml files using LSP binary's full diagnostics.
```bash
node "D:/my agents copilot studio/pipeline/scripts/manage-agent.bundle.js" validate --workspace <path> --tenant-id <id> --environment-id <id> --environment-url <url> --agent-mgmt-url <url>
```
Returns JSON: { valid: true|false, summary: { errors: N, warnings: N }, files: [...] }

### Publish via Gateway publishv2-operations API (bypasses pac cache)

When `pac copilot publish` is stuck with a cached failure (same timestamp every retry), use the PowerVA gateway API directly. This bypasses the LSP binary entirely and does not require interactive login — works with token from `az`.

**Auth:** Get a token scoped to the PVA resource `96ff4394-9197-43aa-b393-6a41652e21f8`:
```bash
TOKEN=$(powershell -Command "az account get-access-token --resource '96ff4394-9197-43aa-b393-6a41652e21f8' --query accessToken -o tsv" 2>/dev/null)
```

**Endpoint:** `POST /api/botmanagement/v1/environments/{envId}/bots/{botId}/publishv2-operations`
**Gateway URL:** `https://powervamg.us-XXX.gateway.prod.island.powerapps.com` (region varies: us-il106, us-il107, etc.)

**Required headers:**
- `Authorization: Bearer <token>`
- `X-CCI-TenantId: <tenant-guid>` — must be the full tenant GUID from `az account show --query tenantId -o tsv`, not a shortened prefix; using only the prefix returns gateway `BadRoutingHeaderValue` / `ErrorCode 4002`.
- `x-cci-applicationsource: Web`
- `Accept: application/json`

**Trigger publish (POST):**
```python
publish_url = f"{GATEWAY}/api/botmanagement/v1/environments/{ENV_ID}/bots/{BOT_ID}/publishv2-operations"
req = urllib.request.Request(publish_url, data=b"{}", method="POST")
# Returns { "state": "Queued", "isInFinalState": false, ... }
```

**Poll for completion (GET — same URL):**
```python
req = urllib.request.Request(publish_url, method="GET")
# Poll every 5s. When isInFinalState=true:
#   state="Finished" → SUCCESS
#   state="FinishedWithUserErrors" → validation failure (check exceptionType/exceptionMessage)
```

**Known failure modes:**
- `StorageUnitNotAssigned` on GET (404) — no operation in progress, POST first
- `ValidationFailedException` on state `FinishedWithUserErrors` — the agent has a validation problem (blank conversation starters, stale knowledge references, etc.) that must be fixed before publish. The gateway API does NOT expose diagnostic details — use the Copilot Studio UI Publish button to see them.
- Publish returns too fast (next poll already `FinishedWithUserErrors`) — validation failed immediately, no model training occurred

**Power Platform token expiry (HTTP 403 "Unable to validate token"):** The gateway uses a Power Platform-scoped token (`96ff4394-9197-43aa-b393-6a41652e21f8` / `PowerVirtualAgents.Components.ReadWrite`), NOT the Dataverse-scoped `az` token. When the PPAPI token expires mid-session:
- The Dataverse `az account get-access-token` token is still valid for Dataverse PATCH/POST
- But the gateway rejects it with 403
- The saved token file at `~/.copilot-studio-cli/powerplatform-env-token.txt` may be stale
- **Fix:** Launch Chrome with CDP (`chrome.exe --remote-debugging-port=9223`), navigate to Copilot Studio, then extract a fresh PPAPI token by capturing a `botcomponents` API call's `Authorization` header from within the browser session (via CDP Network.enable). The token is valid for ~60-90 minutes.

**When the gateway API also fails:** The issue is likely a validation error in the agent's configuration, not the publish mechanism. Publish via the Copilot Studio UI to see the specific error messages.
### Publish (make draft agent live)
ALWAYS confirm with user before publishing (makes agent live for all shared users).
```
pac copilot publish --environment <orgUrl> --bot <botId>
```
The `--bot` flag accepts the bot GUID. Use `--bot-id` if a PAC command rejects `--bot` (varies by PAC CLI version).

**PITFALL: cached publish failure.** If `pac copilot publish` returns the same failed timestamp on every retry, the Dataverse has a cached failure. DO NOT attempt to clear `synchronizationstatus` on the Bot entity — this can crash `pac` with `System.ArgumentException` and may not resolve the issue. Instead:

  1. **Gateway publishv2-operations API** (recommended) — see `references/gateway-publish-api.md`. This bypasses both `pac` and LSP entirely, works with `az` tokens, and is the most reliable programmatic publish path.
  2. **Copilot Studio UI** — always shows the specific validation error when the gateway API returns `FinishedWithUserErrors` without diagnostics.

### List Agents
```bash
node "D:/my agents copilot studio/pipeline/scripts/manage-agent.bundle.js" list-agents --tenant-id <id> --environment-url <url> [--no-owner]
```

### List Environments
```bash
node "D:/my agents copilot studio/pipeline/scripts/manage-agent.bundle.js" list-envs --tenant-id <id>
```

## Direct Dataverse Push/Create Workflow (when LSP push fails)

When `manage-agent.bundle.js push` fails with the `vscode-jsonrpc/node` error, use the Dataverse REST API directly via `az account get-access-token` + Python/curl. The `pac` CLI auth works where the LSP interactive login does not.

### Prerequisites
- `az` CLI authenticated: `az account get-access-token --resource <orgUrl>` works
- Environment details from `agent.manifest.json` or `.mcs/conn.json`
- Bot ID, org URL, tenant ID

### Auth
```bash
TOKEN=$(powershell -Command "az account get-access-token --resource 'https://<org>.crm.dynamics.com' --query accessToken -o tsv" 2>/dev/null)
```

### Find botcomponent IDs for all topics

Batch-query all topics in one call to build a local-to-live schema name mapping:
```python
filt = f"_parentbotid_value eq '{bot_id}' and componenttype eq 9"
url = f"{base}/botcomponents?$filter={urllib.parse.quote(filt)}&$select=botcomponentid,name,schemaname&$top=100"
```

**PITFALL: schema name casing differs between local and live.** The live agent's `schemaname` field may be lowercase when your local YAML `dialog` references are mixed-case. E.g. local `pcca_theradocworkbench.topic.PTProgressNoteCard` → live `pcca_theradocworkbench.topic.ptprogressnotecard`. Always use the live schemaname from the query result when PATCHing or referencing in BeginDialog.

### Query existing botcomponents
```bash
# List all topics for a bot
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" \
  "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents?\
\$filter=_parentbotid_value eq '<botId>' and componenttype eq 9&\
\$select=botcomponentid,name,schemaname,\$top=100"
```

### PATCH existing topic metadata
Use REST API PATCH on the `data` field of an existing botcomponent to update YAML content (modeldescription, description, trigger changes, etc.).

**RECOMMENDED: Use `az rest` (not Python urllib) for PATCH.** Python `urllib` frequently fails with OData filter quoting issues (control characters in URLs cause `InvalidURL` errors). `az rest` handles all OData encoding internally and is the most reliable method.

#### Method 1: `az rest` PATCH (recommended)

```bash
# Inline body (required for PATCH — --body @file fails with "Stream was not readable")
BODY='{"data": "kind: AdaptiveDialog\nmodelDescription: ..."}'
az rest --method PATCH \
  --resource "https://<org>.crm.dynamics.com/" \
  --url "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents(<topicId>)" \
  --body "$BODY"
# Exit 0 = success (HTTP 204)
```

**CRITICAL PITFALL: `az rest --body @file` fails for PATCH.** The `@file` syntax works for GET/POST but returns `Error 0x80048d19: Stream was not readable` on PATCH. Always pass the JSON body inline as a quoted string.

#### Method 2: Python urllib (only if `az` unavailable)

```python
import urllib.request
payload = {"data": yaml_content_string}
req = urllib.request.Request(f"{base}/botcomponents({comp_id})",
    data=json.dumps(payload).encode(), method="PATCH")
req.add_header("Authorization", f"Bearer {token}")
req.add_header("Content-Type", "application/json")
req.add_header("OData-MaxVersion", "4.0")
req.add_header("OData-Version", "4.0")
with urllib.request.urlopen(req, timeout=30) as resp:
    assert resp.status == 204  # 204 = success
```

**PITFALL: OData filter quoting in Python.** Building OData filter URLs in Python `urllib` often introduces control characters (e.g., smart quotes from copy-paste, or `\n` in f-strings). Use `az rest` instead to avoid this class of error entirely.

**KEY RULES for PATCH:**
- Always back up the live `data` field first (query full record before PATCH)
- PATCH only the `data` field — do NOT touch `content` (contains Markdown headers that break the parser)
- HTTP 204 = success. Any other status = failure.
- ALWAYS verify by re-querying the record and checking the field.
- **CRITICAL: CRLF line endings.** The `data` field YAML uses `\r\n` (CRLF), NOT `\n`. Python `str.replace()` with `\n`-only patterns silently succeeds (HTTP 204) but never matches. Use regex `re.sub()` or explicit `\r\n` in replace strings. See `references/dataverse-direct-push-create.md` for full examples.

### POST new topic (create a new botcomponent)
Use the correct OData payload format. Both `componenttype` (as int) AND `parentbotid@odata.bind` are required:

```python
payload = {
    "schemaname": "pcca_agent.topic.NewTopicName",
    "name": "Display Name",
    "componenttype": 9,                            # int, NOT @odata.bind
    "parentbotid@odata.bind": f"/bots({bot_id})",  # entity reference syntax
    "data": yaml_content_string,
}
req = urllib.request.Request(f"{base}/botcomponents",
    data=json.dumps(payload).encode(), method="POST")
req.add_header("Prefer", "return=representation")
# HTTP 201 = created
```

**PITFALLS for POST (validated 2026-07-12, PCCH):**
- Do NOT use `_parentbotid_value` (GUID string) — OData rejects it with `0x80060888 "CRM do not support direct update of Entity Reference properties. Use Navigation properties instead."` Use `parentbotid@odata.bind: "/bots(<GUID>)"`.
- Do NOT use `componenttype@odata.bind` — use `componenttype: 9` (integer).
- `schemaname` MUST start with a valid customization prefix (e.g. `auto_agent_XRF5I.`). A bare name 400s with `0x800608ad "Export key attribute schemaname for component botcomponent must start with a valid customization prefix."` Reuse the prefix from a sibling topic's schemaname (`botcomponents?$select=schemaname` filtered by `_parentbotid_value eq '<botId>'`).
- Do NOT include `displayname` — it's not a valid OData property on `botcomponents`.
- Leave out `iscustomizable` / `overwritetime` — not required and can 400.
- The POST returns a full entity with `botcomponentid` in the `OData-EntityId` response header (status **204** in this tenant, not 201). Re-query by `schemaname` to verify it landed under the right bot.
- Verify by re-querying with `$filter=schemaname eq '...'` AND confirm `_parentbotid_value` matches the target bot (the collection spans the whole org — multiple agents share one Dynamics org).
- **Reusable script:** `scripts/create_topic_botcomponent.py` — handles the prefix + bind + token-from-file. Run `python scripts/create_topic_botcomponent.py <local_yaml_path> [--dry]`. Override target via env `PCCH_BOT` / `PCCH_PREFIX` / `PCCH_ORG` / `DV_TOKEN_FILE`.

### Verify changes stuck
Always re-query after PATCH/POST to confirm. A PATCH that returns 204 can still fail to write the data. **Do NOT trust the return code alone — verify by reading back:**
```python
filt = f"_parentbotid_value eq '{bot_id}' and componenttype eq 9 and schemaname eq '{sn}'"
url = f"{base}/botcomponents?$filter={urllib.parse.quote(filt)}&$select=botcomponentid,name,data"
# Check raw 'data' field for expected strings
# HTTP 200 + non-empty 'value' array = present in live
assert len(vals) > 0, f"Topic {sn} not found in live agent!"
assert "modeldescription:" in live_data, "modeldescription patch did not stick"
```

### Publish after push
After successful PATCH/POST, publish to make live. See `references/gateway-publish-api.md` for the full gateway workflow. Priority order:
1. **Gateway publishv2-operations API** — most reliable when `pac` is broken (see reference file)
2. **Direct PvaPublish API** — `POST bots({botId})/Microsoft.Dynamics.CRM.PvaPublish` via `az rest`. Returns 200 with empty `PublishedBotContentId` even on success — verify via `synchronizationstatus`. **Verified working 2026-07-09** for Therapy AI Dev.
   ```bash
   az rest --resource "https://<org>.crm.dynamics.com/" --method POST \
     --url "https://<org>.crm.dynamics.com/api/data/v9.2/bots(<botId>)/Microsoft.Dynamics.CRM.PvaPublish" \
     --body "{}" --headers "Content-Type=application/json"
   ```
   Then check:
   ```bash
   az rest --resource "https://<org>.crm.dynamics.com/" --method GET \
     --url "https://<org>.crm.dynamics.com/api/data/v9.2/bots(<botId>)?\$select=synchronizationstatus" -o json | \
     python3 -c "import json,sys;ss=json.loads(json.load(sys.stdin)['synchronizationstatus']);op=ss.get('lastFinishedPublishOperation',{});print(f\"Status: {op.get('status')} @ {op.get('operationEnd')}\")"
   ```
   The `pac copilot publish` command **caches the failed result** — same timestamp on every retry even after the fix. PvaPublish bypasses this cache. Verify with `synchronizationstatus` never with `pac` return code.
3. **`pac copilot publish`** — cached result may persist; PvaPublish is preferred. If `pac` returns the same failed timestamp, DO NOT retry — use PvaPublish.
4. **Copilot Studio UI Publish button** — fallback when all API paths fail

#### Knowledge File Description Patching

Knowledge files (type 14, `FileAttachmentComponentMetadata`) typically have no `description:` field. Per MS Learn, descriptions help generative orchestration route to the right sources. Add them via Dataverse PATCH:

```python
# Current KB YAML format: kind: FileAttachmentComponentMetadata\ntriggerCondition: true
# Add description between kind and triggerCondition:
new_yaml = "kind: FileAttachmentComponentMetadata\ndescription: CMS Medicare Benefit Policy Manual Ch 15 Sections 220-230 — therapy coverage, medical necessity, Plan of Care, skilled services, and documentation standards for Part A and Part B.\ntriggerCondition: true"
body = json.dumps({"data": new_yaml_crlf}).encode("utf-8")
# PATCH via urllib or az rest
```

**PITFALL: Unique descriptions** — each KB should have a unique, specific description that tells the AI what the document contains. Generic descriptions like "CMS regulation document" don't help routing.

### ConditionGroup publish failure — MissingRequiredProperty: Id / Condition

When publish fails with `MissingRequiredProperty: 'Id'` and `MissingRequiredProperty: 'Condition'` on a `conditionGroup_file_check` action, the cause is typically **YAML block scalar indentation corruption**. The `additionalInstructions: |-` content lines broke out of the instructions block and are being parsed as sibling YAML nodes, displacing the ConditionGroup's `id:` and `condition:` properties.

**Detection:** Check the published YAML lines near the ConditionGroup — if instructions content appears at the wrong indent level (e.g. 8 spaces instead of 16), the block scalar broke out:

```yaml
# WRONG — instructions content at indent 8 instead of 16
      additionalInstructions: |-
        Identify whether this is...   # indent 16 (correct)
        For MAC appeals...            # indent 8 (BROKEN OUT — parsed as sibling YAML)
        For surveys...                # indent 8 (BROKEN OUT)

# CORRECT — all lines at indent 16
      additionalInstructions: |-
        Identify whether this is...   # indent 16
        For MAC appeals...            # indent 16
        For surveys...                # indent 16
```

**Fix:** Re-indent all instructions continuation lines to match the first line's indent level (2 spaces deeper than `additionalInstructions:` key).

### .Content vs no .Content on System.Activity.Attachments

When referencing uploaded file attachments in YAML, the `.Content` suffix has specific use cases:

| Context | Use `.Content`? | Example |
|---------|----------------|---------|
| Condition (IsBlank check) | **NO** | `=!IsBlank(First(System.Activity.Attachments))` |
| AI Builder input binding | **YES** | `UserDocument: =First(System.Activity.Attachments).Content` |
| Concatenate in userInput | **Use Concat() instead** | `'=Concatenate("label:\\n\\n", Concat(System.Activity.Attachments, Content, "\\n---\\n"))'` |
| SendActivity output from SASC variable | **YES** | `"{Topic.Answer.Text.Content}"` not `"{Topic.Answer}"` |

Using `.Content` in a condition passes a File-type blob to `IsBlank()` which expects a Boolean/string — causes `MissingRequiredProperty: Condition` or `ExpressionError`.

## Publish Failure Diagnosis from synchronizationstatus

When publish fails, the exact errors are in `bot.synchronizationstatus.lastFinishedPublishOperation.diagnosticDetails`. Parse it:

```python
import json
# Get bot record
data = dv_get(f"bots({bot_id})?$select=synchronizationstatus")
ss = json.loads(data['synchronizationstatus'])
lop = ss.get('lastFinishedPublishOperation', {})
if lop.get('status') == 'Failed':
    for detail in lop.get('diagnosticDetails', []):
        comp_id = detail.get('componentId', '?')  # Topic GUID
        ref = detail.get('reference', {})
        diag_id = f"{ref.get('dialogId','?')}.{ref.get('actionId','?')}"
        for d in detail.get('diagnosticList', []):
            print(f"[{comp_id[:8]}] {d['errorCode']}: {d['errorMessage'][:120]}")
```

**Common publish failures after data PATCH:**
- `BindingKeyNotFoundError` + `InvalidBindingInvokeAction` — Your InvokeFlowAction YAML references an output binding (`job_json`, `found`, etc.) that the flow doesn't produce. **Fix:** Query the flow's `clientdata` to find actual output bindings, or copy bindings from a working topic that uses the same flow.
- `ExpressionError` + `IdentifierNotRecognized` for `Topic.Answer` — You referenced `Topic.Answer` but the SearchAndSummarizeContent node uses a custom `variable` name (e.g., `Topic.ProgressReportAuditReport`). **Fix:** Use the variable name from the topic's existing SearchAndSummarizeContent node.
- `ExpressionError` + `PowerFxError` for `Concatenate()` — The YAML block scalar (`|-)` introduced whitespace/newlines into the Power Fx formula. **Fix:** Use single-line string or ensure the block scalar doesn't break the formula.
- **`MissingRequiredProperty: Title` on the instructions component (type 15)** — Repeated 10+ times across the same `componentId`. The `conversationStarters` array has items with only `text:` fields but missing the required `title:` field. Each starter MUST include both `title:` and `text:`. **Fix:** Add a short human-readable `title:` before each `text:` in `conversationStarters` (e.g. `title: PT Note Review` / `text: Review a PT progress note...`). Verified 2026-07-13 — fixing 10 conversation starters in Case History Reviewing Agent resolved the publish block immediately.

### Flow Schema Injection via Dataverse PATCH

When `InvokeFlowAction` YAML fails with `BindingIncorrectTypeError: File vs String`, the flow's trigger schema needs adjustment. The schema lives in the `workflows` entity's `clientdata` field:

```python
# Get flow definition
url = f"{org}/api/data/v9.2/workflows({flow_id})?$select=clientdata"
cd = json.loads(json.loads(urllib.request.urlopen(url, headers=headers).read())["clientdata"])

# Remove "type": "string" from file_name and file_content
schema = cd["properties"]["definition"]["triggers"]["manual"]["inputs"]["schema"]
for field in ["file_name", "file_content"]:
    schema["properties"][field].pop("type", None)

# PATCH back
patch_url = f"{org}/api/data/v9.2/workflows({flow_id})"
payload = json.dumps({"clientdata": json.dumps(cd)})
# HTTP 204 = success
```

This avoids needing to open Power Automate's Code view. See `references/invokeflowaction-file-type-pitfall.md`.

## Token Handling on Windows (Dataverse API)

`az account get-access-token -o tsv` returns ~2930-char tokens. **The terminal tool truncates long output.** Do NOT capture the token via `TOKEN=$(az ...)` and use it in the same shell — the variable will be truncated. **Always save to file first:**

```bash
az account get-access-token --resource 'https://<org>.crm.dynamics.com' \
  --query accessToken -o tsv > "C:/Users/kevin/Desktop/az_token.txt"
```

Then read from file in Python:
```python
with open("C:/Users/kevin/Desktop/az_token.txt") as f:
    token = f.read().strip()
```

**The `az` token expires ~10 minutes** after `az account get-access-token` is called. Re-fetch before each batch operation.

**Verification via `az rest` (not Python urllib):** Python `urllib` has OData `$select` quoting issues on Windows (control characters in f-strings cause `InvalidURL`). Use `az rest` for queries:
```bash
az rest --resource "https://<org>.crm.dynamics.com/" --method GET \
  --url "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents(<id>)?\$select=name,data" -o json
```
For PATCH operations, Python `urllib` works fine as long as the token is read from file (not from shell variable).

## Power Automate Management REST API

The management plane at `api.flow.microsoft.com` supports GET and PATCH of flow definitions. Use this as an ALTERNATIVE to Dataverse PATCH when you need to modify the full `definition` object (not just `clientdata`). The flow definition's `properties.definition` field follows the Logic Apps Workflow Definition JSON schema.

**Auth:** Token scoped to `https://service.powerapps.com/` (NOT the Dataverse org URL).

### ⚠️ Critical pitfall: ActiveUnpublished draft state

PATCH via the management API fails if the flow has an existing unpublished draft. The error is:

```
CurrentState=ActiveUnpublished ... context.IsModified=False
```

This happens because the flow's Dataverse `workflow` entity has a draft row that was never published. The management API only targets the published version, and Dataverse blocks the update when `IsModified=False` and a draft exists.

**Resolution options** (in priority order):
1. **Use Dataverse `workflows` entity PATCH on `clientdata`** instead — `copilot-studio-manage-agent` already covers this above
2. **Discard the existing draft via Power Automate UI** — open the flow in the maker portal and discard the draft, then the management API PATCH succeeds
3. **Use the Power Automate maker portal browser UI** directly to make edits

See `references/powerautomate-management-api.md` for full API patterns, payload structure, and the draft-state workaround.

## InvokeFlowAction Integration (OCR Preprocessing Pipeline)

When agent topics accept file uploads (PDFs, scanned images) for audit/review, the raw file often can't be processed by Prompty models directly. Insert a Power Automate flow step between the file question and the AI Builder audit call.

### Pattern Per Topic

**Full pipeline (AI Builder exists):**
```
Question (file upload) → InvokeFlowAction [OCR flow] → SetVariable (extracted text) → InvokeAIBuilderModelAction [audit] → SendActivity
```

**Simplified pipeline (AI Builder model missing — common for copied agents):**
```
Question → Condition (file check) → GotoAction (retry) → InvokeFlowAction [OCR flow] → [agent GPT auto-responds]
```
No SetVariable, SendActivity, InvokeAIBuilderModelAction, or EndDialog needed. The agent's GPT reads `Topic.xxx_doc_extracted` and responds per its Instructions. ~2,000 chars vs ~6,000.

### Finding Flow Schemas

Power Automate flows live in the Dataverse `workflows` entity (`category=5`). The trigger and I/O schemas are in the `clientdata` field:

```python
filt = urllib.parse.quote(f"contains(name, 'OCR') or contains(name, 'Extract')")
url = f"{org}/api/data/v9.2/workflows?$filter={filt}&$select=workflowid,name,clientdata&$top=50"
```

Look for `triggers.manual.kind: "VirtualAgent"` — only these work with Copilot Studio InvokeFlowAction. The response action defines the output bindings. See `references/ocr-flow-integration.md` for the full YAML pattern.

### Patching Topics

1. Get current `data` field from the topic's botcomponent
2. Find the GotoAction end (last line of file-retry loop)
3. Insert InvokeFlowAction YAML block there
4. Change the AI Builder model's `poc_doc` binding from the raw file variable to the extracted text variable (e.g., `Topic.eval_doc_extracted`)
5. PATCH via Dataverse REST API, verify by re-querying

### Flow Selection

- **Standard docs** (eval, progress, discharge, note, recert): use an OCR text extraction flow with AI Builder Document Intelligence
- **Large docs** (100+ pages, Episode of Care): use a flow with size-aware chunking/truncation

## Sync Local From Live (when manage-agent pull or pac clone fails)

When `manage-agent.bundle.js pull` requires interactive LSP login that can't be completed, or `pac copilot clone` is unavailable (v2.7.4 bug), use the direct Dataverse REST API to download all topics and GPT instructions:

See skill `copilot-studio-live-sync-backup` for the full script.

Key steps:
1. Get Dataverse token: `az account get-access-token --resource 'https://<org>.crm.dynamics.com'`
2. Query botcomponents where `_parentbotid_value eq '<botId>' and componenttype eq 9` for topics
3. Query where `componenttype eq 15` for GPT instructions
4. Write each `data` field to a `.mcs.yml` file
5. Remove local files with no live match
6. Git status, commit the backup state

## Revert / Rollback Workflow

When a PATCH or push introduces unintended changes and you need to revert to the last known-good state:

### Prerequisite: Know the last good state

Before ANY PATCH, **GET the current `data` field from Dataverse and save it**. This is your rollback target:
```bash
az rest --resource "https://<org>.crm.dynamics.com/" --method GET \
  --url "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents(<componentId>)?\$select=data" -o json > backup.json
```

If you did NOT save a backup, the live Dataverse IS the last good version for components that were never PATCHed. For components that WERE PATCHed, reconstruct the original from your knowledge of what changed.

### Step-by-step revert

1. **GET the current live data** from the component you need to revert:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" \
     "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents(<componentId>)"
   ```

2. **Identify what changed** — diff the `data` field against your backup or known original. Look for specific string additions (G4a block, MANDATORY INLINE QUOTE RULE).

3. **Build the revert payload** — reconstruct the original `data` field as a JSON string:
   ```json
   {"data": "kind: GptComponentMetadata\n..."}
   ```

4. **PATCH the revert**:
   ```bash
   curl -s -X PATCH -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" -H "If-Match: *" \
     -d '{"data": "..."}' \
     "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents(<componentId>)"
   ```

5. **VERIFY by re-querying** — do NOT trust the 204 alone:
   ```bash
   curl -s -H "Authorization: Bearer $TOKEN" \
     "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents(<componentId>)" |
     python3 -c "import json,sys; d=json.load(sys.stdin); print('G4a present:', 'G4a' in d['data'])"
   ```

### Restoring local files from live Dataverse

When local YAML files get corrupted (e.g., the `patch` tool reformatted them with blank lines — see PITFALL below), restore from the live copy:

1. Get the botcomponent ID for each topic
2. GET the `data` field from Dataverse
3. Write it to the local file:
   ```python
   yaml_data = d.get('data', '')
   with open(f"{workspace}/topics/{filename}", 'w') as f:
       f.write(yaml_data)
   ```

This works because **for topics never PATCHed, Dataverse IS the original**.

### Botcomponent ID Discovery via curl --data-urlencode

Query all topics for a bot in one call. Use `--data-urlencode` to avoid Python urllib quoting issues:

```bash
curl -s --get -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" \
  --data-urlencode "\$filter=_parentbotid_value eq '<botId>' and componenttype eq 9" \
  --data-urlencode "\$select=botcomponentid,schemaname" \
  --data-urlencode "\$top=100" \
  "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents"
```

The `schemaname` field contains the topic name (e.g., `cr917_Agent.topic.EpisodeofCare`). This avoids multiple round-trips per topic.

### ⚠️ PITFALL: Patch tool reformatting

The Hermes `patch` tool normalizes line endings from CRLF (`\r\n`) to LF (`\n`). For YAML files that originally had CRLF line endings (Copilot Studio exports on Windows), this doubles the apparent line count. The YAML still parses correctly, but the file becomes harder to read. **Mitigation:** GET the original from Dataverse and write it directly instead of using `patch` on the YAML structure.

### ⚠️ PITFALL: Patch tool over-matching

The `patch` tool's fuzzy matching can match MORE lines than intended. In this session, a patch targeting only a MANDATORY INLINE QUOTE RULE also removed the CONSTRAINTS line that followed it — breaking the Concatenate() call. **Mitigation:** After every patch, re-read the affected region to verify ONLY the intended text changed.

### ⚠️ PITFALL: `$select` with invalid property names returns 0 results silently

OData on Dataverse `botcomponents` uses **all-lowercase** property names. Using `displayName` (camelCase) in `$select` causes HTTP 400 `"Could not find a property named 'displayName'"`. **Fix:** Use `displayname`, `schemaname`, `botcomponentid` — all lowercase. When debugging, omit `$select` entirely to get all fields.

### Finding Backup Versions of an Agent

When reverting to a known-good state, check these locations for backup YAML files:

1. **Project workspace backups directory** — `Pacific-Coast-Therapy-Hub/backups/` may contain dated snapshots
2. **Project `_medicare_ref` or similar reference directories** — dated YAML snapshots with timestamps
3. **Desktop cleanup directories** — contain publish reports but NOT full YAML snapshots
4. **Dataverse GET** — for components never PATCHed, the live Dataverse IS the original

**PITFALL: Partial snapshots.** Backup directories may not contain ALL topics. Check for missing topics and handle explicitly.

### OData Query Pitfalls for `botcomponents`

**Single quotes REQUIRED around GUIDs in filters:**
```bash
curl -s "...?$filter=_parentbotid_value%20eq%20'b0346795-4876-f111-ab0e-70a8a5b1b8cc'&$top=5"
```
Without the single quotes around the GUID value, the filter silently returns 0 results. Use `%20` for spaces and `$` escaped with backslash in bash.

**`-w` HTTP code appends to JSON body** and breaks `json.load(sys.stdin)`. Save curl output to file first, then read from file.

### Alternative Architectures (Non-OCR)

When an agent is rebuilt from scratch or reverted, recognize the **File + Text dual-path** pattern:

```
Question (StringPrebuiltEntity, var: Topic.DocumentText) →
  Condition: !IsBlank(First(System.Activity.Attachments)) →
    InvokeAIBuilderModelAction [AI Builder model, per-doc-type unique ID]
    SendActivity: "{Topic.[DocType]Results.text}"
  else: !IsBlank(Trim(Topic.DocumentText)) [text paste] →
    SearchAndSummarizeContent
    userInput: =Concatenate("...", Topic.DocumentText, "...")
    SendActivity: "{Topic.AuditResult}"
  else → GotoAction [retry]
```

**Key differences from OCR pipeline:**
- No `InvokeFlowAction`, no `SetVariable`, no async OCR status polling
- No `Large_Document_OCR_Extraction`, `Check_Async_OCR_Job_Status`, `Check_OCR_Status` topics
- File branch uses `InvokeAIBuilderModelAction` with per-doc-type AI Builder model IDs
- Each topic ~74 lines / ~3,500 bytes (vs ~130-300 lines with OCR)
- `Topic.DocumentText` (StringPrebuiltEntity) instead of `Topic.ocr_payload`
- `applyModelKnowledgeSetting: true` in SearchAndSummarizeContent

### Publishing via `pac copilot publish`

```bash
pac copilot publish --environment "https://<org>.crm.dynamics.com/" --bot "<full-bot-guid>"
```
The `--bot` flag accepts the **full bot GUID** (e.g., `b0346795-4876-f111-ab0e-70a8a5b1b8cc`). Short ID or schema name returns `"Copilot with ID '...' not found"`.

### Knowledge Source Transfer Between Agents

Knowledge files (type 19) are **per-agent** in Dataverse — you cannot share or copy them between agents via API. To give Agent B the same knowledge as Agent A:

1. **Instructions-based approach (recommended):** PATCH Agent B's instructions component with the same `## APPROVED KNOWLEDGE SOURCES` and `## KNOWLEDGE HIERARCHY` sections. The model applies the standards even without the actual files attached.
2. **File re-upload:** Requires the actual source file bytes (not available from Dataverse `data` field alone — it stores a blob reference, not the content). Upload via Copilot Studio UI.
3. **fileSearchDataSource in topics:** Reference the schemaname of Agent A's knowledge files in Agent B's topics — only works if knowledge is shared at the environment level.

## References
- `references/live-context-dump.md` — Read-only Dataverse workflow for gathering full live agent context before executing a later prompt; includes sync diagnostics and topic/action maps
- `references/dataverse-data-only-topic-repair.md` — Minimal targeted data field repair
- `references/dataverse-full-topic-replacement.md` — Full YAML replacement via data PATCH
- `references/dataverse-direct-push-create.md` — Python implementation of PATCH/POST/verify
- `references/gateway-publish-api.md` — Gateway publishv2-operations API (recommended programmatic publish)
- `references/powerautomate-management-api.md` — Power Automate Management REST API (GET/PATCH), draft-state pitfall, and Compose action patterns
- `references/pvapublish-api.md` — PvaPublish API details and pitfalls
- `references/ocr-flow-integration.md` — Inserting Power Automate OCR flows between file upload and AI Builder audit steps in document processing topics
- `references/flow-response-output-compatibility.md` — Preserve legacy `InvokeFlowAction` output bindings while repairing VirtualAgent flow response schemas
- `references/topic-dedupe-and-poll-cleanup.md` — Duplicate topic cleanup, statecode-vs-componentstate nuance, bounded poll-loop repairs, and Work IQ component verification
- `references/optional-ux-cleanup-and-visual-verification.md` — Safe optional UX cleanup pattern: backup, data-only PATCH, re-query, validate, publish, and visually verify custom/system topics
- `references/system-topic-api-limitation.md` — Which topics are system topics, why PATCHing them via API breaks publish, and the only fix path (UI code editor)
- `references/on-conversation-start-eval-pattern.md` — OnConversationStart topic hijack pattern: why it kills eval scores and how to fix without reactivating
- `references/conditional-response-format-fix.md` — Instructions fix pattern: additive conditional format rules that improved SR by +10 points

## Agent Rename / Rebrand Workflow (validated 2026-07-17)

When renaming a live Copilot Studio agent (display name, internal name, and all text references), patch components in this order:

### Affected component list

| Component | Patch type | What to change |
|-----------|-----------|----------------|
| Instructions (ct=15) | `data` + `name` | `displayName:` field, `You are [name]` in instructions body, component `name` |
| Fallback topic (ct=9, name: Fallback) | `data` | `description:` field, `additionalInstructions:` body |
| On Error topic (ct=9, name: On Error) | `data` | Error message body text |
| Feedback settings (ct=18) | `name` | Component `name` field |
| Content Moderation settings (ct=18) | `name` | Component `name` field |
| Bot record (bots table) | `name` | Bot entity `name` field |
| Eval test set markers (ct=19) | `name` | Component `name` field matching old eval name pattern |
| Duplicate bot files (ct=14) | `statecode` | Deactivate duplicates (keep canonical) |
| Topic data references | `data` | Any topic whose data field contains the old name in text |

### Workflow steps

1. Query all components for old-name references: `contains(name,'OldName') or contains(data,'OldName')`
2. PATCH instructions `data` first (highest impact): replace `displayName`, `You are [name]`, any body text references. Also PATCH component `name` field.
3. PATCH Fallback, On Error, Feedback settings data references
4. PATCH settings component `name` fields (Feedback, Content Moderation)
5. PATCH bot record `name` (bots table)
6. Batch update eval markers (ct=19): replace old eval set name in component `name`
7. Deactivate duplicate bot files (statecode=1) if any
8. Publish via PvaPublish API or pac copilot publish
9. Verify: re-query instructions for new `displayName` + 0 old-name references across all components

**Key pitfalls:**
- Check BOTH `data` field text AND component `name` field — they're separate PATCH operations
- Eval markers (ct=19) often have old names in their `name` field even when data is clean
- On Error topic error messages and Feedback disclaimer text are the most commonly missed references
- After renaming, verify zero hits: `contains(name,'OldName')` across all botcomponents
- `az` CLI is a **shell script** on Windows (`/c/Program Files/Microsoft SDKs/Azure/CLI2/wbin/az`), NOT a `.exe`. System Python `subprocess.run(['az',...])` fails because git-bash PATH is invisible to Windows Python. Use `az` from terminal (git-bash) and save token to file for Python.

## Direct Dataverse Repair Fallback

If the user cannot complete the Copilot Studio API/LSP interactive login but `pac`/Azure auth can access the Dataverse environment, use the targeted Dataverse `botcomponents` repair workflow instead of repeatedly asking the user to sign in.

See `references/dataverse-data-only-topic-repair.md` for the tested pattern.
See `references/dataverse-direct-push-create.md` for the full Python implementation of PATCH/POST/verify against the `botcomponents` table.

If normal CLI/MSAL/pac auth is blocked but an authenticated Copilot Studio browser session exists, use `references/browser-token-dataverse-publish-fallback.md` for the CDP token-capture + Dataverse PATCH + gateway `publishv2-operations` workflow.

**CORRECTED (2026-07-16): `pac org fetch` DOES read `botcomponents` successfully.** The earlier "crashes on botcomponents (stack overflow)" note is OUTDATED — verified working this session: `pac org fetch -xf file.xml` returned the full `data` field of a topic botcomponent (18107 bytes). Syntax that works: no `top` attribute (pac injects paging and rejects it), use a Windows-path FetchXML file (NOT `/tmp/` — may not resolve under MSYS/git-bash), and read the `data` attribute as a YAML dump from the XML body. See `references/pac-cli-auth-and-fetch.md` for the full working pattern. NOTE: `pac` holds its token in-memory only (no msal.cache) and has NO generic PATCH verb — so `pac org fetch` is a READ path, not a write path.

## Error Handling (referenced content)
Key rules:
- Query `botcomponents` with `_parentbotid_value eq '<botId>' and componenttype eq 9` and back up exact live records before patching.
- Prefer minimal `data` field patches for YAML/metadata repairs; avoid whole-record replacement.
- **Full topic replacement is also possible via `data` PATCH** — replace the entire `data` field with new YAML content. This works for Fallback/Conversational Booster replacements and topic-wide fixes. The `data` field stores raw YAML as a string; PATCH it with the complete new YAML.
- **Deactivate topics by setting `statecode=1` on the botcomponent record.** You can include `componentstate=2` in the PATCH body, but Dataverse may still read back `componentstate=0`; treat `statecode=1` as the reliable inactive signal. For true duplicate-topic cleanup: back up all topic records, verify the original/non-copy topic is active, deactivate the copy first, re-query, then DELETE the duplicate record only after confirming no `BeginDialog`/schema references point to it. This avoids duplicate trigger routing while preserving the original topic.
- Be careful with `content`: it may contain a leading `# Topic Name` header and PATCHing it can fail with `Unexpected character encountered while parsing value: #`. If that happens, patch only `data` and verify by re-querying.
- Publish afterward with `pac copilot publish --environment <orgUrl> --bot <botId>`.
- Verify with `pac copilot list --environment <orgUrl>` if `pac copilot status` fails.

## Error Handling Table
| Error | Cause | Resolution |
| Extension not found | VS Code extension not installed | Install from marketplace |
| ConcurrencyVersionMismatch | Push without fresh versions | Pull first, then push |
| Token expired + refresh failed | Refresh token expired (~90 days) | Re-auth |
| PvaPublish failed | Insufficient permissions | Verify publish permissions |
| `Cannot find module 'vscode-jsonrpc/node'` during LSP validate | Local VS Code extension/runtime dependency not available to the bundle | Do a local YAML syntax sanity check, then use direct Dataverse repair only for targeted fixes; do not edit bundled scripts |
| Dataverse PATCH says `Unexpected character encountered while parsing value: #` | Attempted to PATCH a field containing a leading Markdown/header line, commonly `content` | Stop whole-record/content patch attempts; patch only the minimal `data` field change and verify by re-querying |
| `pac copilot publish` returns same failed timestamp on every retry (e.g. `Failed [7/3/2026 7:26:12 AM]`) | Persistent cached publish failure in Dataverse; timestamp never changes | Use the gateway publishv2-operations API (post then poll GET) — see `references/gateway-publish-api.md`. Do NOT clear synchronizationstatus on Bot entity — this can crash pac CLI. If gateway API returns `FinishedWithUserErrors` without diagnostics, publish from Copilot Studio UI to see validation errors. If UI also fails, check for blank conversation starters, stale knowledge references, or BeginDialog targeting deleted topics. |
| Publish fails with topic validation errors ("We failed to publish your agent" dialog with error counts) | Topics have YAML binding errors — type mismatches, missing AI model refs, invalid property paths | Click "Show raw" on each error entry in the publish dialog for full diagnostic JSON. Common patterns: `BindingIncorrectTypeError` (file_content type mismatch — fix: remove `"type": "string"` from flow trigger schema via Code view or Dataverse PATCH), `InvalidReferenceError: AIModel not found` (pre-existing, affects all topics — remove InvokeAIBuilderModelAction nodes), `InvalidPropertyPath: predictionOutput` (cascading from missing model), `ExpressionError: Topic.xxx.text not recognized` (cascading). Compare error count between modified and unmodified topics to isolate your changes. See `references/invokeflowaction-file-type-pitfall.md`. |
| Publish fails with `SynchronizationSystemError` after PATCHing system topics | A system topic was modified — platform may reject publish when certain system topics are edited through the data plane | **Updated Jul 10 2026: ConvStart CAN be API-patched.** Previous blanket claim was overly broad — we successfully patched Conversation Start (`kind: OnConversationStart`) via API PATCH multiple times and published. The `SynchronizationSystemError` may be specific to Escalate/OnError/ResetConversation or `content` field patches, not all system topics. **Strategy:** Try API PATCH first for ConvStart. For Escalate/OnError/ResetConversation, be more cautious. If publish fails, revert via API PATCH, then use UI code editor as fallback. See `references/system-topic-api-limitation.md` for full updated guidance. |
| PATCH returns 204 but YAML replacement didn't take effect | CRLF mismatch — `str.replace()` used `\n` but data uses `\r\n` | Use `re.sub()` or explicit `\r\n` in replace strings. Always verify by re-querying. See `references/dataverse-direct-push-create.md`. |\n| PvaPublish API / gateway returns 404 `Does Not Exist` | Bot GUID from Copilot Studio URL (e.g. `4d0ed0d3-30f6-f011-8406-000d3a37eba2`) is NOT the same as the Dataverse `bots` entity `botid` | Query `/api/data/v9.2/bots?$select=botid,name` to find the actual Dataverse bot ID. The Copilot Studio URL GUID is internal and won't match Dataverse entity IDs. When querying `botcomponents`, `_parentbotid_value` also uses the Dataverse bot ID, not the URL GUID. |
| Gateway returns HTTP 400 `BadRouting` / `ErrorCode: 4002` | Environment ID format is wrong — used the `Default-<guid>` prefix from the browser URL instead of the short GUID | Use the short environment GUID from `.mcs/conn.json`. The SPA URL format `environments/Default-03cc92c3-...` does NOT work with the gateway API — strip the `Default-` prefix. See `references/gateway-publish-api.md`. |
| Gateway returns HTTP 400 `BadRouting` / `ErrorCode: 4002` | Environment ID format is wrong — used the `Default-<guid>` prefix from the browser URL instead of the short GUID | Use the short environment GUID from `.mcs/conn.json`. The SPA URL format `environments/Default-03cc92c3-...` does NOT work with the gateway API — strip the `Default-` prefix. See `references/gateway-publish-api.md`. |
| PATCH returns 204 but YAML replacement didn't take effect | CRLF mismatch — `str.replace()` used `\n` but data uses `\r\n` | Use `re.sub()` or explicit `\r\n` in replace strings. Always verify by re-querying. See `references/dataverse-direct-push-create.md`. |\n| PvaPublish API / gateway returns 404 `Does Not Exist` | Bot GUID from Copilot Studio URL (e.g. `4d0ed0d3-30f6-f011-8406-000d3a37eba2`) is NOT the same as the Dataverse `bots` entity `botid` | Query `/api/data/v9.2/bots?$select=botid,name` to find the actual Dataverse bot ID. The Copilot Studio URL GUID is internal and won't match Dataverse entity IDs. When querying `botcomponents`, `_parentbotid_value` also uses the Dataverse bot ID, not the URL GUID. |
| `pac copilot status` complains about `componentstate_Property` | PAC status-command quirk in some tenants/CLI versions | Use successful publish output plus `pac copilot list --environment <orgUrl>` to verify Published/Active state |

## Output Format
All commands output JSON with status field. status: "ok" for success, status: "error" for failure.
