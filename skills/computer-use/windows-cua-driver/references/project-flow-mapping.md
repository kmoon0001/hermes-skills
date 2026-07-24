# Project Flow Mapping — Therapy AI Agents Dev

Environment: `a944fdf0-0d2e-e14d-8a73-0f5ffae23315`
Org URL: `powervamg.us-il106.crm.dynamics.com` (internal DNS only — not resolvable from git-bash)
Gateway: `powervamg.us-il106`

## Key Flows

| Display Name | Flow ID (Power Automate URL) | Workflow Entity ID (Dataverse) |
|---|---|---|
| OCR Text Extraction - Async Submit and Process | `3f1304de-89ff-1a28-dc83-2e3488d49b9e` | `c71672f2-113b-f111-88b4-0022480b6bd9` |
| SNF - Large Document Processor | (different) | `765136b6-9509-4554-9bf0-016fc63923c7` |

Note: The Dataverse `workflowEntityId` differs from the Power Automate URL flow ID.
Topics reference the workflow entity ID in their `flowId` field.

## Topics → Flow Mapping (Agent: Therapy Documentation Feedback Agent Prod)

All 8 topics below call flow `c71672f2` (OCR Text Extraction - Async Submit and Process) with the same binding pattern:

| Topic | document_type |
|---|---|
| Large_Document_OCR_Extraction | "Large Document" |
| Discharge_Summary_Review | "Discharge Summary" |
| Treatment_Encounter_Note_Review | (standard binding) |
| Evaluation_and_Plan_of_Care_Review | (standard binding) |
| Episode_of_Care | (standard binding) |
| Progress_Report_Review | (standard binding) |
| Recertification_UPOT_Review | (standard binding) |
| Check_Async_OCR_Job_Status | (same flow, different binding — passes job_id) |

**Standard binding (submit):**
```yaml
binding:
  file: ={ contentBytes: First(System.Activities.Attachments).Content, name: First(System.Activities.Attachments).Name }
  file_name: =First(System.Activities.Attachments).Name
  document_type: "<type>"
  requesting_agent: "Topic Therapy Docuementation Feedback Agent"
  extraction_goal: "Asynchronous OCR and structured compliance audit"
  neutral_patient_id: "Not provided"
  neutral_file_id: =First(System.Activities.Attachments).Name
```

## Flow Input Resolution (inside the flow)

The flow's `Resolve_file_content_base64` Compose action uses coalesce:
```
@coalesce(triggerBody()?['file']?['contentBytes'], triggerBody()?['file_content']?['contentBytes'], triggerBody()?['file_content'])
```

This handles three input formats:
1. `file.contentBytes` — object with `contentBytes` + `name` (what all topics send via InvokeFlowAction)
2. `file_content.contentBytes` — alternative object format
3. `file_content` — raw text string (legacy format)

The `Create job note` action's `item/filename` uses:
```
@coalesce(triggerBody()?['file']?['name'], triggerBody()?['file_name'], concat(variables('JobId'), '.pdf'))
```

## Topics → Action Mapping (Agent: Pacific Coast Case Historian)

| Topic | Action | Flow Referenced |
|---|---|---|
| OCRTextExtraction | via topic actions directly (InvokeFlowAction) | `765136b6` (SNF - Large Document Processor) |
| SNFLargeDocumentProcessor | InvokeFlowTaskAction (action file) | `765136b6` (SNF - Large Document Processor) |

The Case Historian's action passes data differently (via `InvokeFlowTaskAction` with Prompt input mode):
```yaml
inputs:
  binding:
    file_content: Topic.file_content
    file_name: Topic.file_name
    document_type: Topic.document_type
    requesting_agent: Topic.requesting_agent
    extraction_goal: Topic.extraction_goal
```

The OCRTextExtraction topic in Case Historian also passes `file_content` as plain text:
```yaml
file_content: =Topic.UploadedText
file_name: ="pasted_clinical_document.txt"
```

## Flow Definition Access

**Fetch (read-only, works from any network):**
```bash
token=$(az account get-access-token --resource https://service.powerapps.com/ --query accessToken -o tsv)
curl -s -H "Authorization: Bearer $token" \
  "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/$env/flows/$flow_id?api-version=2016-11-01"
```

**Update (must use UI Code view or Dataverse API):**
The management API is read-only. For UI updates, use `set_value` on the Code view editor (see `monitoring-browser-ai-agents.md`).

## Dataverse API (write — requires internal DNS resolution)

```bash
# Token for internal org URL
token=$(az account get-access-token --resource https://powervamg.us-il106.crm.dynamics.com --query accessToken -o tsv)

# PATCH workflow clientdata
curl -s -X PATCH \
  -H "Authorization: Bearer $token" \
  -H "Content-Type: application/json" \
  -d '{"clientdata": "<escaped flow JSON>"}' \
  "https://powervamg.us-il106.crm.dynamics.com/api/data/v9.2/workflows(c71672f2-113b-f111-88b4-0022480b6bd9)"
```

**Note:** `powervamg.*.crm.dynamics.com` URLs are internal corporate DNS. The git-bash terminal cannot resolve them. PowerShell may or may not resolve depending on network configuration. The browser can always reach them.
