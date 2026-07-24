# Agent Rename Workflow (Dataverse PATCH)

Full end-to-end workflow for renaming a Copilot Studio agent hosted in Dataverse — updates every component that carries the old name.

## Overview

Renaming a live agent touches 5+ component types. Do NOT just patch the instructions — the old name lingers in settings, eval markers, On Error, Fallback, Feedback, and the bot entity itself.

## Auth

Use `az` terminal for all queries and Python/system calls to avoid PATH and UTF-8 issues:

```bash
az account get-access-token --resource "https://<org>.crm.dynamics.com" --query accessToken -o tsv | tr -d '\r\n' > az_token.txt
```

**Pitfall:** The `--resource` trailing slash is unstable on some tenants. If WhoAmI returns 401, try adding/removing trailing slash.

**Pitfall:** System Python 3.13 (Windows Store) does NOT inherit `az` from git-bash PATH. Use `az` directly in terminal commands, or provide the full path: `C:/Program Files/Microsoft SDKs/Azure/CLI2/wbin/az`. Process calls from system Python may fail with `FileNotFoundError`.

## Components to Update

### 1. Instructions (componenttype 15)

The agent's GPT instructions. Update:
- `displayName` in YAML
- `name` field on the botcomponent record
- Every `You are [name]` reference in instructions text itself

```python
# PATCH data field
new_data = data.replace('displayName: Old Name', 'displayName: New Name')
new_data = new_data.replace('You are Old Name', 'You are New Name')

# Normalize CRLF
d2 = new_data.replace('\r\n','\n').replace('\r','\n').replace('\n','\r\n')
payload = json.dumps({'data': d2}).encode()
# PATCH via urllib ...
```

Separately PATCH the component `name` field:

```python
payload = json.dumps({'name': 'New Name'}).encode()
# PATCH ...
```

### 2. Fallback topic (componenttype 9, name="Fallback")

The Fallback topic's `additionalInstructions` and `description` often reference the old agent name. Use the same `.replace()` pattern on the data field.

### 3. On Error topic (componenttype 9, name="On Error")

The error message sent to users (e.g. `"An unexpected error occurred in [Old Name]"`) must be updated.

**Pitfall:** On Error is a system topic but CAN be API-patched (unlike Escalate/OnSystemRedirect). The old CrossAgentAuditLog flow reference may have already been removed — check before acting.

### 4. Settings (componenttype 18)

Both Feedback and Content Moderation settings have component names like `"[Old Name] - Feedback Settings"`. PATCH the `name` field:

```python
payload = json.dumps({'name': 'New Name - Feedback Settings'}).encode()
```

Also check the `data` field — the disclaimer text (Feedback) or moderated response (Content Moderation) may reference the old name.

### 5. Eval markers (componenttype 19)

Eval test set names like `"Evaluate Old Name"` need updating. Batch-query with OData `contains()`:

```python
flt = urllib.parse.quote(f"_parentbotid_value eq {BOT_ID} and (contains(name,'OldName1') or contains(name,'OldName2'))")
```

Then iterate and PATCH each component's `name` field. Test case trigger questions that mention "SimpleLTC export" as a product (not an agent name) should be left as-is.

### 6. Bot entity (bots table)

The `bots` record's `name` field controls what shows in Copilot Studio:

```bash
curl -s -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"New Name"}' \
  "https://<org>.crm.dynamics.com/api/data/v9.2/bots(<botId>)"
```

### 7. Duplicate Bot Files (componenttype 14) — optional P1 cleanup

Look for same-name files with different extensions (.md, .pdf, .docx vs extensionless). These are duplicate uploads. Disable the duplicate (keep the canonical copy):

```python
payload = json.dumps({'statecode': 1}).encode()
# PATCH ...
```

## Non-UTF-8 Data Pitfall

Some Dataverse `data` fields contain non-UTF-8 characters (e.g. byte 0x97 in `responseInstructions`). This causes `json.loads()` to fail with `UnicodeDecodeError`.

**Fix:** Read with error replacement:

```python
raw = resp.read().decode('utf-8', errors='replace')
d = json.loads(raw)
```

## Publish

After all patches, trigger publish via PvaPublish API:

```bash
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{}' \
  "https://<org>.crm.dynamics.com/api/data/v9.2/bots(<botId>)/Microsoft.Dynamics.CRM.PvaPublish"
```

Poll `synchronizationstatus.lastFinishedPublishOperation.status` until `"Succeeded"`. Note: `publishedon` may NOT update for minor data-only changes — check the operation end timestamp instead.

## Verification

Re-query each updated component to confirm the rename stuck:

```bash
az rest --resource "https://<org>.crm.dynamics.com/" --method GET \
  --url "https://<org>.crm.dynamics.com/api/data/v9.2/botcomponents(<id>)?$select=name,data" -o json
```

Check for zero remaining old-name occurrences in the data field.
