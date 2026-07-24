---
name: invokeflowaction-file-fix
description: Fix for InvokeFlowAction file content validation — prevents "type":"string" rejection and flow errors when passing file attachments via Dataverse PATCH.
---

# InvokeFlowAction File Fix

When patching Copilot Studio topic YAML via Dataverse API, file content in `InvokeFlowAction` triggers must follow specific rules:

## Rules

1. **File content MUST NOT have `"type":"string"`** — the validator rejects File→String type coercion.
2. **Remove via `workflow.clientdata` PATCH in Dataverse** if the flow trigger already has the bad type.
3. **No dot (`.`) on Blobs** — pass the file directly as `{ contentBytes: ..., name: ... }`.
4. **Minimal YAML** — strip unused SetVariable/SendActivity/InvokeAIBuilder nodes if the model is missing; GPT auto-responds in the fallback.

## Example

```yaml
- kind: InvokeFlowAction
  id: invokeFlow_submit
  input:
    binding:
      file: "={ contentBytes: First(System.Activity.Attachments).Content, name: First(System.Activity.Attachments).Name }"
      file_name: =First(System.Activity.Attachments).Name
```

## When to use

- When a Dataverse PATCH of a topic with InvokeFlowAction + file attachment is rejected with a validation error about `"type":"string"`
- When a published bot shows "Flow not found" for document processing flows
- When cleaning up stale flow references from simplified topic versions
