# OCR Retry Polling Pattern (July 2026)

## What was fixed
4 document review topics were missing proper retry/poll logic after OCR check:
- Eval/Assessment + Plan of Care — had `RetryCount < 0` (dead code, never true)
- Treatment Encounter Note Review — no retry at all
- Recertification/UPOC Review — no retry at all
- Episode of Care — had `RetryCount < 0` (dead code, never true)

Two topics already worked:
- Discharge Summary — `retry_count_num` sentinel pattern (reference)
- Progress Report Review — `RetryCount < 10` (different var name, functional)

## The pattern (matching Discharge Summary)
Replace the `elseActions` after `conditionGroup_ocr_completed` with:

```
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

        - kind: GotoAction
          id: goto_retry_ocr_check
          actionId: invokeFlow_check_async_ocr_status
```

## How the pattern works
1. `retry_count_num` counted via sentinel formula: `>= 10` → `Blank()`
2. `IsBlank(retry_count_num)` → if blank (hit 10), condition triggers but does nothing (silent exit)
3. If not blank, `GotoAction` loops back to the OCR check step

## Method used for patching
- Each topic PATCHed individually via Dataverse API
- Publish after each topic (4 publishes total)
- Verified each patch with data re-query
- Run included `retry_count_num`, `IsBlank`, `GotoAction`, and `invokeFlow_check_async_ocr_status` checks

## Files modified by topic ID
| Topic | BotComponent ID |
|-------|----------------|
| Eval/Assessment + POC | aa5160f7-dced-49b7-bb9f-473946e77dd5 |
| Treatment Encounter Note Review | 261541b8-d3e2-41f0-bbad-e0f0f59217be |
| Recertification/UPOC Review | de006936-a7d7-4635-8b6f-e41e9622385d |
| Episode of Care | 800cc37e-27c6-4bc0-8169-d3936b7133c1 |
