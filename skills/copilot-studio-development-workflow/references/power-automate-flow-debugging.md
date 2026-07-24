# Power Automate Flow Debugging

How to inspect, diagnose, and fix Power Automate flows that are part of the Copilot Studio agent pipeline.

## Get a flow definition via REST API

The Power Automate management API is **read-only** (GET only — no PUT/PATCH for flow definitions). Use the `service.powerapps.com` resource scope:

```bash
# Get token
token=$(az account get-access-token \
  --resource https://service.powerapps.com/ \
  --query accessToken -o tsv)

# Fetch flow definition (replace env and flow_id)
env="a944fdf0-0d2e-e14d-8a73-0f5ffae23315"
flow_id="3f1304de-89ff-1a28-dc83-2e3488d49b9e"

curl -s -H "Authorization: Bearer $token" \
  "https://api.flow.microsoft.com/providers/Microsoft.ProcessSimple/environments/$env/flows/$flow_id?api-version=2016-11-01"
```

The response includes the full `properties.definition` JSON with triggers, actions, and all parameters.

### OCR Check Status — List rows from Dataverse Notes

The "Async OCR Check Job Status" flow (commonly flowId `27c65bc3`) that topics invoke via `InvokeFlowAction` checks whether an OCR job has completed by querying Dataverse `Notes (annotations)`. The flow needs:

1. **List rows** action (Microsoft Dataverse connector) between the trigger and "Respond status"
2. **Table name:** `Notes (annotations)`
3. **Filter rows:** `subject eq '@{triggerBody()?['job_id']}'`
4. **Row count:** `1`
5. **Sort by:** `createdon desc`
6. **Respond status outputs** updated with expressions:

| Output | Expression |
|--------|-----------|
| `job_id` | Dynamic: `Job Id` from trigger |
| `found` | Expression: `not(empty(outputs('List_rows')?['body/value']))` |
| `job_json` | Expression: `if(empty(outputs('List_rows')?['body/value']), 'Status: Processing', concat('Status: Completed \| ', first(outputs('List_rows')?['body/value'])?['notetext']))` |
| `processing_status` | Expression: `if(empty(outputs('List_rows')?['body/value']), 'Processing', 'Completed')` |
| `message` | Expression: `if(empty(outputs('List_rows')?['body/value']), 'Still Processing', first(outputs('List_rows')?['body/value'])?['notetext'])` |
| `document_type` | Literal: `Unknown` |

The topic condition checks `"Status: Completed" in Topic.ocr_payload` — the `concat('Status: Completed | ', ...)` ensures this string match works when a note exists. Without this List rows step, the status check always returns "Processing" and the 3 auto-polls time out.

## "Invalid Character in Dataverse Field" error

This error occurs when Power Automate tries to write content containing control characters (0x00-0x1F) to a Dataverse text field — commonly the `documentbody` field of the `annotations` (Notes) table when storing PDF files.

### Root cause

The `Resolve file content base64` Compose action returns file content from the trigger. The `Create job note` action's `item/documentbody` field may receive characters the Dataverse `annotations.documentbody` column cannot store.

Common pattern in the flow:
```json
"item/documentbody": "@replace(outputs('Resolve_file_content_base64'), decodeUriComponent('%12'), '')"
```

This only strips `%12` (0x12 / DC2) but 28 other control characters in the 0x00-0x1F range can also cause failures.

### Fix: comprehensive control character sanitization

Replace the single `%12` strip with nested `replace()` calls covering ALL control characters except 0x09 (tab), 0x0A (LF), and 0x0D (CR):

```
@replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(replace(
  outputs('Resolve_file_content_base64'),
  decodeUriComponent('%00'), ''),
  decodeUriComponent('%01'), ''),
  decodeUriComponent('%02'), ''),
  decodeUriComponent('%03'), ''),
  decodeUriComponent('%04'), ''),
  decodeUriComponent('%05'), ''),
  decodeUriComponent('%06'), ''),
  decodeUriComponent('%07'), ''),
  decodeUriComponent('%08'), ''),
  decodeUriComponent('%0B'), ''),
  decodeUriComponent('%0C'), ''),
  decodeUriComponent('%0E'), ''),
  decodeUriComponent('%0F'), ''),
  decodeUriComponent('%10'), ''),
  decodeUriComponent('%11'), ''),
  decodeUriComponent('%12'), ''),
  decodeUriComponent('%13'), ''),
  decodeUriComponent('%14'), ''),
  decodeUriComponent('%15'), ''),
  decodeUriComponent('%16'), ''),
  decodeUriComponent('%17'), ''),
  decodeUriComponent('%18'), ''),
  decodeUriComponent('%19'), ''),
  decodeUriComponent('%1A'), ''),
  decodeUriComponent('%1B'), ''),
  decodeUriComponent('%1C'), ''),
  decodeUriComponent('%1D'), ''),
  decodeUriComponent('%1E'), ''),
  decodeUriComponent('%1F'), '')
```

To apply the fix:
1. **Via UI:** Open the "Create job note" action → Code view tab → replace the `item/documentbody` expression
2. **Via API (if DNS resolves):** PATCH the Dataverse `workflow` entity's `clientdata` field

### Dataverse org DNS restriction

Internal Dataverse org URLs (e.g. `powervamg.us-il106.crm.dynamics.com`) may not resolve from git-bash terminal's external DNS. Only the browser (which uses Windows OS DNS with corporate DNS servers) can reach them. When using the Dataverse PATCH API from the terminal:

```bash
# This will FAIL if the org URL is internal-only:
curl -X PATCH "https://powervamg.us-il106.crm.dynamics.com/api/data/v9.2/workflows(ID)" ...
```

Workarounds:
- **Browser CDP:** Launch Chrome with `--remote-debugging-port=9223` and use `execute_javascript` to make the PATCH call
- **PowerShell:** May use a different DNS resolution chain
- **Manual:** Apply the fix through the Power Automate UI Code view directly
