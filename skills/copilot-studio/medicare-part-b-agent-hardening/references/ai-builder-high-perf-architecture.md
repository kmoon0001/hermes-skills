# AI Builder High-Performance Architecture (July 12 Snapshot)

Snapshot location: `C:/Users/kevin/Desktop/Pacific-Coast-Therapy-Hub/_medicare_ref/`
Date: July 12, 2026 21:02
Tested at: ~90% Conv eval pass rate

## AI Builder Model IDs

| Document Type | Model ID | Source File |
|---------------|----------|-------------|
| Progress Report | `2ae9d680-9db2-4dbd-8446-37589397ca0f` | Progress_Report_Review.yml |
| Episode of Care | `658e5bb8-8412-40ff-b9f6-9ba0cbb7c1de` | Episode_of_Care.yml |
| Evaluation/POC | (read from Evaluation_Assessment_and_Plan_of_Care.yml) | Evaluation_Assessment_and_Plan_of_Care.yml |
| Discharge Summary | (read from Discharge_Summary.yml) | Discharge_Summary.yml |
| Recertification/UPOC | (read from Recertification_UPOC_Review.yml) | Recertification_UPOC_Review.yml |

**Note:** The remaining 3 model IDs need to be extracted from the respective YAML files in `_medicare_ref/`. Each `InvokeAIBuilderModelAction` block has a unique `aIModelId`.

## Topic YAML Inventory in _medicare_ref

17 topic YAMLs, all ~74 lines each (~3,500 bytes):

| File | Lines | Bytes | Has AI Builder? | Has SearchAndSummarize? |
|------|-------|-------|-----------------|------------------------|
| Conversation_Start.yml | 11 | 363 | No | No |
| Discharge_Summary.yml | 74 | 3,596 | Yes | Yes |
| Document_Upload_Intake.yml | 118 | 5,216 | No | No |
| End_of_Conversation.yml | . | 755 | No | No |
| Episode_of_Care.yml | 74 | 3,620 | Yes | Yes |
| Escalate.yml | . | 3,225 | No | No |
| Evaluation_Assessment_and_Plan_of_Care.yml | 75 | 3,481 | Yes | Yes |
| Fallback.yml | 114 | 5,537 | No | Yes (Q&A path) |
| Goodbye.yml | . | 1,752 | No | No |
| Greeting.yml | . | 1,128 | No | No |
| Multiple_Topics_Matched.yml | . | 1,573 | No | No |
| On_Error.yml | . | 3,223 | No | No |
| Progress_Report_Review.yml | 74 | 3,616 | Yes | Yes |
| Recertification_UPOC_Review.yml | 74 | 3,631 | Yes | Yes |
| Reset_Conversation.yml | . | 752 | No | No |
| Sign_in_.yml | . | 560 | No | No |
| Start_Over.yml | . | 1,396 | No | No |

## Topics NOT in _medicare_ref (removed from this architecture)
- Large_Document_OCR_Extraction — not needed (AI Builder handles files)
- Check_Async_OCR_Job_Status — not needed (no async polling)
- Check_OCR_Status — not needed (no OCR pipeline)
- Treatment_Encounter_Note_Review — NOT present. Either removed or not backed up. Document_Upload_Intake references "Treatment Encounter Note" as a routing option but just ends with SendActivity + EndDialog (no dedicated topic routing).
- Progress_Report_Review_-_Text_Paste — removed (text paste path built into each topic)

## Topic YAML Common Pattern

All 5 documentation-review topics follow an identical 74-line structure:

```yaml
kind: AdaptiveDialog
modelDescription: "[per-doc-type description]"
beginDialog:
  kind: OnRecognizedIntent
  id: main
  intent:
    displayName: [Audit Name]
    triggerQueries:
      - [10 trigger phrases]
  actions:
    - kind: Question
      id: question_upload_doc
      variable: init:Topic.DocumentText
      entity:
        kind: StringPrebuiltEntity
      prompt: "Paste the text of or upload the [doc type] document..."
    - kind: ConditionGroup
      id: conditionGroup_file_check
      conditions:
        - id: condition_file_uploaded
          condition: =!IsBlank(First(System.Activity.Attachments))
          actions:
            - kind: InvokeAIBuilderModelAction
              aIModelId: [unique GUID per doc type]
              input:
                binding:
                  [InputField]: =First(System.Activity.Attachments).Content
              output:
                binding:
                  predictionOutput: Topic.[DocType]Results
            - kind: SendActivity
              activity: "{Topic.[DocType]Results.text}"
      elseActions:
        - kind: ConditionGroup
          id: conditionGroup_text_check
          conditions:
            - id: condition_has_text
              condition: =!IsBlank(Trim(Topic.DocumentText))
              actions:
                - kind: SearchAndSummarizeContent
                  id: search_text_audit
                  variable: Topic.AuditResult
                  userInput: '=Concatenate("[audit prompt]...", Topic.DocumentText, "...")'
                  applyModelKnowledgeSetting: true
                  responseCaptureType: FullResponse
                - kind: SendActivity
                  activity: "{Topic.AuditResult}"
          elseActions:
            - kind: GotoAction
              id: goto_upload_retry
              actionId: question_upload_doc
    - kind: EndDialog
      id: endDialog_main
      clearTopicQueue: true
```

## Restore Workflow

To push this version live:
1. Verify AI Builder model IDs are still registered in Dataverse (test with a GET)
2. For each topic in _medicare_ref, GET its component ID from Dataverse: `GET /botcomponents?$filter=_parentbotid_value eq '{botguid}' and componenttype eq 9`
3. PATCH each: `PATCH /botcomponents({id})` body `{"data": <topic YAML>}`
4. Verify readback
5. Publish
