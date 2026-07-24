# InvokeFlowAction File Type Pitfall

## The Problem

When a Copilot Studio topic collects a file (`Question` + `FilePrebuiltEntity`)
and passes it to a Power Automate flow via `InvokeFlowAction`, the YAML
validator rejects the binding if the flow declares `file_content` as `type: string`.

**Error:**
```
BindingIncorrectTypeError — Input variable 'File Content' is of incorrect type: File
```
```
ExpressionError — The '.' operator cannot be used on Blob values.
```
(From `Topic.xxx_doc.name`)

## Root Cause

The flow's trigger schema defines `file_content` with `"type": "string"`.
Copilot Studio's topic validator treats the File/Blob entity from
`FilePrebuiltEntity` as incompatible and blocks publish — even though the
flow's runtime `coalesce()` resolver handles both formats fine.

## Fix: Remove type constraint from flow trigger

Two ways:

### A) Power Automate Code View
1. Open flow → Click trigger → "Code view"
2. Remove `"type": "string",` from `file_content` and `file_name` entries
3. Save + Publish the flow

### B) Direct Dataverse PATCH (faster)

Use the `workflows` entity to PATCH the `clientdata` field:

```python
import subprocess, json, urllib.request

# Get token
cmd = ["powershell", "-Command",
       "az account get-access-token --resource 'https://<org>.crm.dynamics.com' --query accessToken -o tsv"]
tok = subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()

org = "https://<org>.crm.dynamics.com"
headers = {"Authorization": f"Bearer {tok}", "Accept": "application/json",
           "OData-MaxVersion": "4.0", "OData-Version": "4.0"}

# Get flow
url = f"{org}/api/data/v9.2/workflows({flow_id})?$select=clientdata"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=15) as resp:
    cd = json.loads(json.loads(resp.read().decode())["clientdata"])

# Remove type constraints
schema = cd["properties"]["definition"]["triggers"]["manual"]["inputs"]["schema"]
for field in ["file_name", "file_content"]:
    if field in schema.get("properties", {}):
        schema["properties"][field].pop("type", None)

# PATCH
patch_url = f"{org}/api/data/v9.2/workflows({flow_id})"
payload = json.dumps({"clientdata": json.dumps(cd)})
patch_req = urllib.request.Request(patch_url, data=payload.encode(), method="PATCH")
for k, v in headers.items(): patch_req.add_header(k, v)
patch_req.add_header("Content-Type", "application/json")
urllib.request.urlopen(patch_req, timeout=30)
```

## Additional YAML adjustments

After fixing the flow schema, also remove the `file_name` binding from the
topic's InvokeFlowAction YAML — the `.` operator can't be used on Blobs:

```yaml
# BEFORE (causes ExpressionError):
    - kind: InvokeFlowAction
      flowId: <flow-guid>
      input:
        binding:
          file_name: "=Topic.xxx_doc.name"     # ❌ Blob dot-operator
          file_content: "=Topic.xxx_doc"

# AFTER (clean):
    - kind: InvokeFlowAction
      flowId: <flow-guid>
      input:
        binding:
          document_type: "Evaluation"
          requesting_agent: "Agent Name"
          extraction_goal: "Extract all clinical text"
          file_content: "=Topic.xxx_doc"       # ✅ file entity accepted
```

## Flow Trigger Schema

Correct schema (no `"type": "string"` on file fields):

```json
{
  "properties": {
    "file_name": {
      "description": "Original filename with extension.",
      "title": "File Name",
      "x-ms-dynamically-added": true
    },
    "file_content": {
      "description": "Uploaded file content.",
      "title": "File Content",
      "x-ms-dynamically-added": true
    },
    "document_type": {
      "description": "Type of document",
      "title": "Document Type",
      "type": "string",
      "x-ms-dynamically-added": true
    }
  },
  "type": "object"
}
```

The `document_type`, `requesting_agent`, `extraction_goal` fields keep their
`"type": "string"` — they take plain text values, not files.

## Runtime flow resolver pattern

Flows that receive files from Copilot Studio should use this pattern to handle
both serialized-file format and raw string fallback:

```json
"Resolve_file_content_base64": {
  "type": "Compose",
  "inputs": "@coalesce(triggerBody()?['file_content']?['contentBytes'], triggerBody()?['file_content'])"
}
```

## Pre-existing publish blockers

When topics are copied between environments, common issues:
- **AIModel not found**: The `aIModelId` in `InvokeAIBuilderModelAction`
  references a Prompty model that may not exist in the target environment.
  Error: `InvalidReferenceError — AIModel with id '...' not found`.
  Fix: Re-create the Prompty model or remove `InvokeAIBuilderModelAction` nodes.
- **predictionOutput InvalidPropertyPath**: Cascading error from missing AI model.
  The output binding key `predictionOutput` can't be validated.
- **Topic.evaluation.text not recognized**: Cascading error — the Prompty model
  output variable doesn't exist because the model isn't found.
