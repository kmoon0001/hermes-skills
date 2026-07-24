# OCR Pipeline for Copilot Studio Document Topics

## Problem
Uploaded PDFs and scanned images fail when sent directly to AI Builder Prompty models (InvokeAIBuilderModelAction). The Prompty model can't extract text from binary files, and 100+ page episodes exceed context limits.

### Pre-existing blocker when copying agents
When agent topics are copied between environments, `InvokeAIBuilderModelAction` often references a Prompty model (`aIModelId`) that doesn't exist in the target environment. Error: `AIModel with id '...' not found`. This blocks publish. The cascading errors are `predictionOutput InvalidPropertyPath` and `Topic.xxx_evaluation.text not recognized`.

**Fix: Strip the broken AI Builder + SendActivity + SetVariable nodes entirely. Let the agent's built-in GPT auto-respond.**

## Architecture (two patterns)

### Pattern A — Full pipeline (AI Builder exists)
Insert a Power Automate OCR/text extraction flow between the file upload Question and the audit InvokeAIBuilderModelAction:

```
Question (file upload) → InvokeFlowAction [OCR flow] → SetVariable [clean text] → InvokeAIBuilderModelAction [audit with text] → SendActivity
```

### Pattern B — Simplified (AI Builder missing OR you don't need it)
When the Prompty model doesn't exist, strip down to just the OCR flow. The agent's GPT (configured in Instructions) auto-generates the response using the extracted text context:

```
Question (file upload) → Condition → GotoAction → InvokeFlowAction [OCR flow] → [agent auto-responds]
```

No SetVariable, no SendActivity, no EndDialog needed. The agent reads `Topic.xxx_doc_extracted` and responds based on its Instructions. This is ~2,000 chars vs ~6,000 for the full pipeline.

## Finding OCR Flows in Dataverse

```python
# Query the Workflow entity for Power Automate flows (category=5)
url = f"{org}/api/data/v9.2/workflows?$select=workflowid,name,clientdata&$filter=category eq 5 and contains(name, 'OCR')"
```

The flow's schema lives in `clientdata`:
```python
import json
cd = json.loads(flow["clientdata"])
schema = cd["properties"]["definition"]["triggers"]["manual"]["inputs"]["schema"]
# Check kind == "VirtualAgent" — required for Copilot Studio
```

## Common Flow Schema (VirtualAgent)
| Input | Type | Description |
|-------|------|-------------|
| file_name | string | Original filename |
| document_type | string | Type descriptor (e.g. "Evaluation") |
| requesting_agent | string | Agent/caller name (e.g. "Feedback_Agent") |
| extraction_goal | string | What to extract |
| file_content | file | Uploaded file bytes |

| Output | Type | Description |
|--------|------|-------------|
| extracted_text | string | OCR-processed text |
| processing_status | string | Status |
| char_count | integer | Length |
| error_message | string | Errors |

## YAML Patterns

### Pattern A — Full pipeline (with AI Builder)
Replace the raw `poc_doc: "=Topic.xxx_doc"` binding with clean text from the OCR flow:

```yaml
- kind: Question
  id: question_upload_doc
  variable: init:Topic.audit_doc
  prompt: "Please upload the document."
  entity: FilePrebuiltEntity

# 👇 DO NOT include file_name binding — '.' operator breaks on Blob
- kind: InvokeFlowAction
  id: invokeFlowAction_ocr
  flowId: "<workflow-guid>"
  input:
    binding:
      document_type: "Evaluation"
      requesting_agent: "Feedback_Agent"
      extraction_goal: "Extract all clinical text from the document"
      file_content: "=Topic.audit_doc"    # passes File type — flow must not have "type":"string"
  output:
    binding:
      extracted_text: Topic.ocr_text
      processing_status: Topic.ocr_status
      # char_count omitted — integer type causes binding error
      # error_message omitted — not needed

- kind: SetVariable
  variable: Topic.clean_text
  value: "=Topic.ocr_text"

- kind: InvokeAIBuilderModelAction
  input:
    binding:
      poc_doc: "=Topic.clean_text"       # text, not raw file
  output:
    binding:
      predictionOutput: audit_result
```

### Pattern B — Simplified (no AI Builder, GPT auto-responds)
When the Prompty model doesn't exist in the target environment:

```yaml
- kind: Question
  id: question_upload_doc
  variable: init:Topic.audit_doc
  prompt: "Please upload the document."
  entity: FilePrebuiltEntity

- kind: ConditionGroup
  conditions:
    - condition: "=!IsBlank(Topic.audit_doc)"
  elseActions:
    - kind: GotoAction
      actionId: question_upload_doc

- kind: InvokeFlowAction
  id: invokeFlowAction_ocr
  flowId: "<workflow-guid>"
  input:
    binding:
      document_type: "Evaluation"
      requesting_agent: "Feedback_Agent"
      extraction_goal: "Extract all clinical text"
      file_content: "=Topic.audit_doc"
  output:
    binding:
      extracted_text: Topic.audit_doc_extracted
      processing_status: Topic.audit_doc_ocr_status

# No SetVariable, No InvokeAIBuilderModelAction, No SendActivity, No EndDialog
# Agent's GPT reads Topic.audit_doc_extracted and auto-responds
```

## Flow Selection
- **Standard OCR flow** (e.g. "OCR Text Extraction"): Uses AI Builder OCR, page-by-page. Good for evaluations, progress notes, discharges, treatment notes, recertifications.
- **Large Document flow** (e.g. "SNF - Large Document Processor"): Chunks and processes large files. Use for Episode of Care (100+ pages).

## Verification
After PATCHing topics via Dataverse, verify by:
1. Re-querying the botcomponent's `data` field
2. Confirming `kind: InvokeFlowAction` node exists with the correct flowId
3. Confirming `poc_doc` now binds to the clean text variable, not the raw file
4. Publish via gateway API or Copilot Studio UI

## Known Pitfalls
- **State=0 flows are drafts** — state=1 means published/active
- **Non-VirtualAgent triggers won't work** — check `kind` before wiring
- **Variable naming collision** — don't reuse the same variable name for file input and extracted text (e.g. `Topic.eval_doc` vs `Topic.clean_text`)
- **All topics must use the same pattern** — the agent should not mix SASC and OCR+AI Builder approaches for document processing
- **`file_name` binding breaks on Blob** — `"=Topic.xxx_doc.name"` causes ExpressionError: "The '.' operator cannot be used on Blob values." Just remove the binding entirely.
- **`char_count` / `error_message` cause type errors** — flow outputs them as integer/string but Copilot Studio YAML validator may reject them. Drop them from the output binding unless the flow was created in this env.
- **`file_content` needs flow trigger without `"type": "string"`** — Copilot Studio passes File/Blob, not String. Remove `"type": "string"` from the flow's trigger schema. Fix via Power Automate Code view or Dataverse PATCH (see `references/invokeflowaction-file-type-pitfall.md`).
- **AIModel not found in copied agents** — When topics are copied between environments, `aIModelId` in `InvokeAIBuilderModelAction` references a Prompty model that doesn't exist in the target. The cascading errors (`predictionOutput invalid`, `Topic.evaluation.text not found`) are all from this root cause. Fix: strip the broken nodes (Pattern B).
