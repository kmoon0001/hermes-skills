# OCR Async Polling with Retry

## Use When

A Copilot Studio topic submits a document to an async Power Automate OCR flow, then needs to poll for completion with a retry limit instead of a one-shot check.

## Architecture

```
Upload → Submit Async OCR → Send "submitted" message → Check OCR Status
  ├─ Completed? → SearchAndSummarizeContent audit → SendActivity → EndDialog
  └─ Not complete?
       → Send "not complete yet" message
       → SetVariable retry_count_num (sentinel formula)
       → ConditionGroup: IsBlank(retry_count_num)? → silent exit (10 attempts)
       → GotoAction → loop back to Check OCR Status
```

## Key Nodes (YAML)

### 1. Submit OCR (InvokeFlowAction)
```yaml
- kind: InvokeFlowAction
  id: invokeFlow_submit_async_ocr
  output:
    binding:
      job_id: Topic.async_job_id
```
Input includes document bytes, document_type, extraction_goal, file_name.

### 2. Check OCR Status (InvokeFlowAction)
```yaml
- kind: InvokeFlowAction
  id: invokeFlow_check_async_ocr_status
  output:
    binding:
      job_json: Topic.job_json
```
After this, set `Topic.ocr_payload = Topic.job_json`.

### 3. Completion Check (ConditionGroup)
```yaml
- kind: ConditionGroup
  id: conditionGroup_ocr_completed
  conditions:
    - id: condition_ocr_completed
      condition: "=\"Status: Completed\" in Topic.ocr_payload"
      actions:
        # SearchAndSummarizeContent audit + SendActivity
```

### 4. Retry Else Block (the polling loop)
```yaml
elseActions:
  - kind: SendActivity
    id: sendActivity_processing_status
    activity: |-
      The OCR audit job is not complete yet.
      Job ID: {Topic.async_job_id}
      Current status response: {Topic.ocr_payload}
      Use "check OCR job status" with this Job ID to retrieve the completed report.

  - kind: SetVariable
    id: setVariable_retry_count
    variable: Topic.retry_count_num
    value: =If(Value(Text(Topic.'retry_count_num')) + 1 >= 10, Blank(), Value(Text(Topic.'retry_count_num')) + 1)

  - kind: ConditionGroup
    id: conditionGroup_retry_limit
    conditions:
      - id: conditionItem_retry_exit
        condition: =IsBlank(Topic.retry_count_num)
    # No actions = silent exit when IsBlank (10 attempts reached)

  - kind: GotoAction
    id: goto_retry_ocr_check
    actionId: invokeFlow_check_async_ocr_status
```

## Sentinel Formula Explained

```
=If(Value(Text(Topic.'retry_count_num')) + 1 >= 10, Blank(), Value(Text(Topic.'retry_count_num')) + 1)
```

- First call: `retry_count_num` is unset → `Text(Blank())` → `Value("")` → `Blank()` → `Blank() + 1` → `1` → `1 >= 10` = false → result = `1`
- Attempt 9: result = `9`, `9 >= 10` = false → result = `9`
- Attempt 10: `9 + 1 = 10`, `10 >= 10` = true → result = `Blank()`
- `IsBlank(Topic.retry_count_num)` = true → silent exit (ConditionGroup with no actions stops execution)

## Common Pitfalls

- **Don't use `RetryCount < 0`** — dead code, will never loop
- **Don't forget the GotoAction** — without it, the topic ends after one failed check
- **The IsBlank ConditionGroup must have NO actions** — empty actions block acts as exit
- **The 5-second delay is in the Power Automate flow** (not in Copilot Studio YAML)
- **Use same flow IDs** (`c71672f2` for submit, `27c65bc3` for check) across all doc types — they're shared flows

## Topics Using This Pattern

- Discharge Summary (reference)
- Progress Report Review (uses `RetryCount < 10` variant)
- Evaluation/Assessment + Plan of Care
- Treatment Encounter Note Review
- Recertification/UPOC Review
- Episode of Care
