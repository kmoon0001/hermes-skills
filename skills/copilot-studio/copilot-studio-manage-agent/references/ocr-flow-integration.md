# OCR Flow Integration for Document Processing Topics

## When to Use

When Copilot Studio agent topics accept file uploads (PDF, scanned images) via `FilePrebuiltEntity` and send them directly to an `InvokeAIBuilderModelAction` (Prompty model), but the model can't handle native PDF text or large documents (100+ pages). Solution: insert an `InvokeFlowAction` between the file question and the AI Builder audit step that passes files through a Power Automate flow for OCR/text extraction.

## Architecture

```
Question (file upload) → InvokeFlowAction [OCR flow] → SetVariable (extracted text) → InvokeAIBuilderModelAction [audit Prompty] → SendActivity
```

The flow receives the raw file, uses AI Builder Document Intelligence / OCR to extract text, and returns clean text that the Prompty model can analyze.

## Finding Flow Schemas

Power Automate flows are stored in the Dataverse `workflows` entity with `category=5`. The flow's trigger and input/output schemas are in the `clientdata` field as JSON:

```python
url = f"{org}/api/data/v9.2/workflows?$select=workflowid,name,clientdata"
# Filter by name:
filt = urllib.parse.quote("contains(name, 'OCR') or contains(name, 'Extract')")
url = f"{org}/api/data/v9.2/workflows?$filter={filt}&$select=workflowid,name,clientdata"
```

The `clientdata` JSON structure:
```json
{
  "properties": {
    "definition": {
      "triggers": {
        "manual": {
          "kind": "VirtualAgent",    // Copilot Studio-compatible trigger
          "inputs": {
            "schema": {
              "properties": {
                "file_content": { "type": "string", "description": "Uploaded file content" },
                "file_name": { "type": "string" },
                "document_type": { "type": "string" },
                "requesting_agent": { "type": "string" },
                "extraction_goal": { "type": "string" }
              }
            }
          }
        }
      },
      "actions": {
        "Respond_to_agent": {
          "type": "Response",
          "inputs": {
            "schema": {
              "properties": {
                "extracted_text": { "type": "string" },
                "processing_status": { "type": "string" },
                "char_count": { "type": "integer" },
                "error_message": { "type": "string" }
              }
            }
          }
        }
      }
    }
  }
}
```

## InvokeFlowAction YAML Pattern

Insert after the GotoAction block (file retry loop), before the first SetVariable:

```yaml
    - kind: InvokeFlowAction
      id: invokeFlow_ocr_{doc_var}
      flowId: {guid-of-flow}
      input:
        binding:
          file_name: "=Topic.{doc_var}.name"
          document_type: "{Document Display Name}"
          requesting_agent: "{Agent Name}"
          extraction_goal: "Extract all clinical text for compliance audit"
          file_content: "=Topic.{doc_var}"
      output:
        binding:
          extracted_text: "Topic.{doc_var}_extracted"
          processing_status: "Topic.{doc_var}_ocr_status"
```

**IMPORTANT — file_name binding will cause a publish error.** Power Fx can't use the `.` operator on File/Blob values (`The '.' operator cannot be used on Blob values.`). Remove the `file_name` line from the input binding to avoid this.

**IMPORTANT — file_content type mismatch.** The flow trigger declares `file_content` with `"type": "string"` but Copilot Studio passes a File/Blob. This causes `BindingIncorrectTypeError` at publish time. **Fix in Power Automate:** open the flow trigger Code view, remove `"type": "string",` from both `file_content` and `file_name` properties, save.

## Patching via Dataverse REST API

```python
# 1. Get token
tok = subprocess.run(["powershell", "-Command",
    "az account get-access-token --resource 'https://<org>.crm.dynamics.com' --query accessToken -o tsv"],
    capture_output=True, text=True, timeout=30).stdout.strip()

# 2. Get current topic YAML
filt = urllib.parse.quote(f"_parentbotid_value eq '{bot_id}' and schemaname eq '{schema_name}'")
url = f"{org}/api/data/v9.2/botcomponents?$filter={filt}&$select=data&$top=1"

# 3. Find insertion point: after the GotoAction block, before the first SetVariable
#    In the YAML, the pattern is typically:
#      - kind: GotoAction
#      ...
#    (next line with "- kind:")
#    Insert the InvokeFlowAction block there.

# 4. PATCH
patch_url = f"{org}/api/data/v9.2/botcomponents({comp_id})"
payload = json.dumps({"data": new_yaml})
req = urllib.request.Request(patch_url, data=payload.encode(), method="PATCH")
req.add_header("Authorization", f"Bearer {tok}")
req.add_header("Content-Type", "application/json")
req.add_header("OData-MaxVersion", "4.0")
req.add_header("OData-Version", "4.0")
with urllib.request.urlopen(req, timeout=30) as resp:
    assert resp.status == 204  # success
```

## Verifying Changes

Re-query the `data` field and check for:
- `InvokeFlowAction` present in the YAML
- The flow GUID appears
- The Prompty model input now references `_extracted` text instead of raw file variable
- `_extracted` in the YAML confirms output binding mapped

```python
assert "InvokeFlowAction" in live_data
assert flow_guid in live_data
assert f"Topic.{doc_var}_extracted" in live_data
```

## Which Flow to Use

| Document Type | Recommended Flow | Reason |
|---|---|---|
| Standard docs (eval, progress, discharge, note, recert) | OCR Text Extraction | AI Builder OCR, handles PDFs and scans page-by-page |
| Large docs (100+ pages, Episode of Care) | Large Document Processor | Size-aware chunking, truncation handling |

## Known Pitfalls

- **Flow must have `kind: VirtualAgent` trigger** — only flows with this trigger type will appear as options in Copilot Studio. Plain Request triggers won't bind correctly.
- **File content binding** — use `"=Topic.{doc_var}"` (the raw file variable), NOT the `.name` or `.contentBytes` sub-property. The flow's VirtualAgent trigger handles the file content natively.
- **Output binding keys must match the Response schema** — the left-side key in the output binding (e.g., `extracted_text`) must match the property name in the flow's `Respond_to_agent` action's response schema exactly (case-sensitive).
- **Flow state must be 1 (activated)** — flows with `statecode=0` (draft) exist in the Workflow table but won't execute from Copilot Studio.
- **Remove integer-type output bindings to avoid validation errors** — Flow response schemas often include `char_count` (type: integer). Binding `char_count` to a topic variable causes 2-3 topic validation errors per topic (Copilot Studio can't coerce integer → topic variable). Only bind `extracted_text` and `processing_status` (both strings); skip `char_count` and `error_message` in the output binding.
- **CRITICAL: flow trigger file_content type mismatch blocks publish** — If the YAML validator rejects `file_content` with `BindingIncorrectTypeError: expected String, assigned File`, the flow's trigger schema has `"type": "string"` on the file parameter. **Fix:** Open the flow in Power Automate → click the "When Copilot Studio calls a flow" trigger → click "Code view" in the panel → remove `"type": "string",` from the `file_content` and `file_name` property blocks in the JSON schema → Save → Publish. After this, Copilot Studio won't enforce strict type validation. The flow already handles both string and object-with-contentBytes formats at runtime.
- **Remove `file_name` from input binding** — `Topic.{doc_var}.name` produces `The '.' operator cannot be used on Blob values.` in Power Fx. The flow doesn't need `file_name` to function; remove this line from the InvokeFlowAction input binding.
- **Pre-existing errors in unmodified topics** — If the publish validation shows errors in topics you didn't touch, compare the error count per topic. Unmodified topics with similar structure (e.g., same AI Builder model, same SetVariable patterns) will also have errors. Not all errors are from your changes. Always check an unmodified topic's error count as a baseline.
- **PvaPublish with `b"{}"` may return empty PublishedBotContentId** — This is a known issue documented in the manage-agent skill. The publish may still succeed despite the empty response. Check the bot's `statecode` / `componentstate` after calling PvaPublish to verify.
