# OCR Check Status Power Automate Flow Fix

## Flow Identity
- **Name:** Async OCR Check Job Status
- **Flow ID:** `27c65bc3-277a-f111-ab0e-7ced8d6f2fba`
- **Type:** Power Automate cloud flow (Dataverse connector)
- **Environment:** Therapy AI Agents Dev (a944fdf0)

## Architecture

```
Trigger: When Copilot Studio calls a flow
    │ Input: job_id (string from topic)
    │
    ▼
Action: List rows (Microsoft Dataverse)
    │ Table: Notes (annotations)
    │ Filter: subject eq '@{triggerBody()?['job_id']}'
    │ Row count: 1
    │ Sort: createdon desc
    │
    ▼
Action: Respond status (Power Virtual Agents)
    │ Outputs:
    │   found: not(empty(outputs('List_rows')?['body/value']))
    │   job_id: Job Id (dynamic from trigger)
    │   job_json: if(empty(...), 'Status: Processing', 
    │                    concat('Status: Completed | ', first(...)?['notetext']))
    │   processing_status: if(empty(...), 'Processing', 'Completed')
    │   message: if(empty(...), 'Still Processing', first(...)?['notetext'])
    │   document_type: Unknown (literal)
```

## The Flow URL
```
https://make.powerautomate.com/environments/a944fdf0-0d2e-e14d-8a73-0f5ffae23315/solutions/~preferred/flows/4ed0b02f-8387-5fdd-eb56-5b4b279f4e45
```

## Key Design Decision

The `job_json` expression MUST contain the substring `"Status: Completed"` for the topic's condition (`"Status: Completed" in Topic.ocr_payload`) to evaluate true. The `concat('Status: Completed | ', ...)` pattern ensures this.

## Dataverse Schema

The Submit flow (`c71672f2`) creates records in the `Notes (annotations)` table:
- `subject` field = the job_id from the OCR submission
- `notetext` field = the OCR result text (or processing status)

The Check flow queries this table to determine if OCR has completed.

## Topic Condition That Reads the Response

```yaml
condition: "=\"Status: Completed\" in Topic.ocr_payload"
```

The `Topic.ocr_payload` variable is set from the flow's `job_json` output via:
```yaml
- kind: SetVariable
  id: setVariable_ocr_payload
  variable: Topic.ocr_payload
  value: =Topic.job_json
```
