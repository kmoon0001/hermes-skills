# Power Automate Management REST API

`api.flow.microsoft.com` is the management plane for Power Automate flows. Supports GET (read flow definition) and PATCH (update), but **has a critical draft-state limitation**.

## Endpoint Pattern

```
GET/PATCH  /providers/Microsoft.ProcessSimple/environments/{envId}/flows/{flowId}
```

## Auth

Token scoped to `https://service.powerapps.com/`:

```bash
TOKEN=$(az account get-access-token --resource https://service.powerapps.com/ --query accessToken -o tsv)
```

## GET Flow Definition

```bash
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" \
  "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{envId}/flows/{flowId}"
```

Returns the full ARM resource with `properties.definition` containing the Logic Apps workflow JSON. The flow schema lives in `properties.definition.actions.{actionName}`.

The definition structure follows the Logic Apps Workflow Definition schema (`2016-06-01`). Actions are nested under:
- `triggers.manual.inputs.schema` — trigger schema (for VirtualAgent kind)
- `actions.{actionName}` — root-level actions
- Conditional branching via `actions.{actionName}.else.actions` (False branch) or `actions.{actionName}.cases` (Switch)

## PATCH to Update the Definition

```bash
curl -s -X PATCH \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  --data-binary @payload.json \
  "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/{envId}/flows/{flowId}"
```

Payload shape:
```json
{"properties": {"definition": { ... }}}
```

## ⚠️ CRITICAL PITFALL: ActiveUnpublished Draft State

**PATCH fails if the flow has an existing unpublished draft.** Error:

```json
{
  "error": {
    "code": "XrmApiServerError",
    "message": "Request to XRM API failed with server error: 'You are attempting to do a published update of publishable component in an unmodified active context when there exists an unpublished active row.\\nThis is not allowed context.IsModified =False Component Type: 29  Object Id: {workflowEntityId} CurrentState=ActiveUnpublished'"
  }
}
```

### Root Cause

The flow's Dataverse `workflow` entity has:
- Published row with `IsModified=False` (never actually modified since last publish)
- ActiveUnpublished row (draft started but never published)

The management API only updates the published version, and Dataverse blocks this when a draft exists.

### Resolution Options

1. **Discard existing draft via Power Automate UI** — open flow → discard draft → then PATCH succeeds
2. **Publish existing draft via UI** — makes the draft the new published version, setting IsModified=True, then PATCH succeeds
3. **Use Dataverse REST API directly** (most reliable) — PATCH the `workflows` entity's `clientdata` field (see `copilot-studio-manage-agent` SKILL.md → "Flow Schema Injection via Dataverse PATCH")

### Detection

Check `properties.componentState` in the GET response:
- `"Published"` — no draft conflict, PATCH should work
- GET returns `"componentState": "Published"` but PATCH still fails with `CurrentState=ActiveUnpublished` → there is a hidden draft

## Compose Action Pattern for Sanitization

When adding a Compose action between existing actions in a flow definition, the key JSON properties are:

```json
"Sanitize_document_body": {
    "runAfter": { "Resolve_file_content_base64": ["Succeeded"] },
    "type": "Compose",
    "inputs": "@replace(replace(replace(...), ...), ...)"
}
```

The action ordering in the JSON object determines the visual order in the designer. Insert the new action entry at the correct position and update the downstream action's `runAfter` to reference it.

### Example: Nested replace expression for stripping control characters

Strips all bytes 0x00-0x1F except 0x09 (tab), 0x0A (newline), 0x0D (CR):

```
@replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(outputs('Resolve_file_content_base64'), decodeUriComponent('%00'), ''), decodeUriComponent('%01'), ''), decodeUriComponent('%02'), ''), decodeUriComponent('%03'), ''), decodeUriComponent('%04'), ''), decodeUriComponent('%05'), ''), decodeUriComponent('%06'), ''), decodeUriComponent('%07'), ''), decodeUriComponent('%08'), ''), decodeUriComponent('%0B'), ''), decodeUriComponent('%0C'), ''), decodeUriComponent('%0E'), ''), decodeUriComponent('%0F'), ''), decodeUriComponent('%10'), ''), decodeUriComponent('%11'), ''), decodeUriComponent('%12'), ''), decodeUriComponent('%13'), ''), decodeUriComponent('%14'), ''), decodeUriComponent('%15'), ''), decodeUriComponent('%16'), ''), decodeUriComponent('%17'), ''), decodeUriComponent('%18'), ''), decodeUriComponent('%19'), ''), decodeUriComponent('%1A'), ''), decodeUriComponent('%1B'), ''), decodeUriComponent('%1C'), ''), decodeUriComponent('%1D'), ''), decodeUriComponent('%1E'), ''), decodeUriComponent('%1F'), '')
```
