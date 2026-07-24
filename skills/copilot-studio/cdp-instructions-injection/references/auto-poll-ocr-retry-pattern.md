# Auto-Poll OCR with Retry Limit — YAML Pattern

For Copilot Studio topics that call the async OCR flow (c71672f2) and need to wait for completion, use this pattern instead of a dead-end message + manual re-check.

## Problem

The naive pattern sends "not complete yet, check back later" and ends. The user must manually re-trigger the check. Adding a GotoAction without a retry counter causes infinite loops (500+ executions → Copilot Studio kills the dialog).

## Solution

Add a `Topic.RetryCount` (Number, default 0) variable and a nested ConditionGroup in the `elseActions` of the status check:

```yaml
    # Initialize retry counter
    - kind: SetVariable
      id: init_retry
      variable: Topic.RetryCount
      value: "=0"

    - kind: InvokeFlowAction
      id: invokeFlow_check_async_ocr_status
      flowId: c71672f2-113b-f111-88b4-0022480b6bd9
      input:
        binding:
          job_id: =Topic.async_job_id
      output:
        binding:
          job_json: "Topic.job_json"

    - kind: SetVariable
      id: set_ocr_payload
      variable: Topic.ocr_payload
      value: =Topic.job_json

    - kind: ConditionGroup
      id: condition_check_status
      conditions:
        - id: status_completed
          condition: '="Status: Completed" in Text(Topic.ocr_payload)'
          actions:
            # SUCCESS: show the report
            - kind: SendActivity
              id: send_result
              activity: "=Topic.job_json"
            - kind: EndDialog
              id: end_success
              clearTopicQueue: true

      elseActions:
        - kind: ConditionGroup
          id: condition_check_retries
          conditions:
            - id: retries_remaining
              condition: "=Topic.RetryCount < 10"
              actions:
                - kind: SetVariable
                  id: increment_retry
                  variable: Topic.RetryCount
                  value: "=Topic.RetryCount + 1"
                - kind: SendActivity
                  id: send_still_processing
                  activity: |-
                    Still processing (attempt {Topic.RetryCount} of 10)...
                - kind: GotoAction
                  id: goto_retry_check
                  actionId: invokeFlow_check_async_ocr_status
          elseActions:
            - kind: SendActivity
              id: send_timeout
              activity: |-
                Job taking too long. Check again with ID: {Topic.async_job_id}
            - kind: EndDialog
              id: end_timeout
              clearTopicQueue: true
```

## Key Points

- `Topic.RetryCount` MUST be initialized to `=0` before the loop starts.
- The GotoAction targets the InvokeFlowAction (re-checks status), NOT the submit action.
- 10 retries × ~3s per cycle = ~30s max wait before timeout message.
- The `data` field stores the Shell/draft version. The `content` field stores the compiled YAML. Only the UI code editor can update `content` — API PATCH on `content` returns 400.
- Always verify content persisted by re-opening the code editor post-save.

## Template Variables

When adapting for different document types, change:
- `document_type` value
- `Topic.{variable_name}` for the upload file
- `modelDescription` / `componentName`
- triggerQueries
