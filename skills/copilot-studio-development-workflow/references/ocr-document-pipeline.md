# OCR Document Processing Pipeline (Copilot Studio)

## Problem

Document-processing agents in Copilot Studio that accept file uploads via `FilePrebuiltEntity` and pass them directly to `InvokeAIBuilderModelAction` fail on:

- **PDF files** — the AI Builder Prompty model receives a raw binary blob and cannot extract text
- **Scanned images** — no OCR step exists in the pipeline
- **Large documents** (>50 pages, e.g. Episode of Care at 100+ pages) — the model's context window is exceeded or the file transfer times out

## Architecture

### Current (broken) pipeline — all Feedback B doc topics

```
Question (FilePrebuiltEntity) → SetVars → InvokeAIBuilderModelAction (raw file) → SendActivity → EndDialog
```

The AI Builder model (`aIModelId`) gets a raw file blob in its input binding (e.g. `poc_doc: "=Topic.eval_doc"`). It works for small text-based `.txt`/`.docx` files, but fails for PDFs, scanned images, and large documents.

### Required pipeline

```
Question (FilePrebuiltEntity) 
  → InvokeFlowAction (Power Automate OCR flow) 
    [extracts text from PDF, runs OCR on images, chunks large docs] 
  → SetVariable (extracted_text = flow output)
  → InvokeAIBuilderModelAction (pass extracted text, not raw file)
  → SendActivity
```

## Power Automate OCR Flow Requirements

The flow must:

1. Accept a file blob as input (from `FilePrebuiltEntity` topic variable)
2. Extract text using:
   - **AI Builder PDF extraction** — for text-based PDFs
   - **Azure Document Intelligence (Form Recognizer)** — for scanned PDFs/images
   - **Regular text extraction** — for `.txt`/`.docx`
3. Handle pagination/chunking for documents over ~50 pages
4. Output the extracted text as a string for the AI Builder Prompty model

## Per-Topic InvokeFlowAction Binding Pattern

Each doc-processing topic uses the same pattern with per-topic variable names:

```yaml
- kind: InvokeFlowAction
  id: invokeFlow_ocr_{doc_var}
  flowId: <ocr-flow-guid>
  input:
    binding:
      file_name: "=Topic.{doc_var}.name"
      document_type: "{display_name}"        # e.g. "Progress Report"
      requesting_agent: "Therapy Documentation Feedback Agent"
      extraction_goal: "Extract all clinical text for compliance audit"
      file_content: "=Topic.{doc_var}"       # the raw file blob
  output:
    binding:
      extracted_text: "Topic.{doc_var}_extracted"
      processing_status: "Topic.{doc_var}_ocr_status"
      char_count: "Topic.{doc_var}_ocr_count"
      error_message: "Topic.{doc_var}_ocr_error"
```

**Key rules:**
- `file_content` receives the raw `FilePrebuiltEntity` variable from the Question node
- `file_name` uses `Topic.{doc_var}.name` (the filename property)
- Output `extracted_text` is passed to `InvokeAIBuilderModelAction` instead of the raw file
- Use a separate output prefix per topic so different flow runs don't clobber each other
- **Flow output binding:** Bind `extracted_text`, `processing_status`, `error_message`, and `char_count`. All 4 fields are returned — bind them all to avoid unexpected behavior.

### Full topic structure (after patching):

```yaml
  actions:
    - kind: Question                          # 1. File upload
      id: question_upload_doc
      variable: "init:Topic.{doc_var}"
      entity: FilePrebuiltEntity

    - kind: ConditionGroup                    # 2. Check file uploaded
      id: conditionGroup_file_check
      conditions:
        - condition: "=!IsBlank(Topic.{doc_var})"
      elseActions:
        - kind: GotoAction
          id: goto_upload_retry
          actionId: question_upload_doc

    - kind: InvokeFlowAction                  # 3. OCR extraction (INSERTED)
      id: invokeFlow_ocr_{doc_var}
      flowId: <guid>
      input:
        binding:
          file_name: "=Topic.{doc_var}.name"
          document_type: "{display_name}"
          requesting_agent: "..."
          extraction_goal: "..."
          file_content: "=Topic.{doc_var}"
      output:
        binding:
          extracted_text: "Topic.{doc_var}_extracted"
          processing_status: "Topic.{doc_var}_ocr_status"
          char_count: "Topic.{doc_var}_ocr_count"
          error_message: "Topic.{doc_var}_ocr_error"

    - kind: SetVariable                       # 4. Audit guidelines (existing)
      variable: "Topic.{doc_var}_guidelines"

    - kind: SetVariable                       # 5. System instructions (existing)
      variable: Global.feedback_system_instructions

    - kind: InvokeAIBuilderModelAction        # 6. Audit with extracted text
      input:
        binding:
          poc_doc: "=Topic.{doc_var}_extracted"   # ← changed from raw file

    - kind: SendActivity                      # 7. Display results

    - kind: EndDialog                         # 8. End
```

## Discovering Flow IDs and Schemas via Dataverse API

When a Power Automate flow exists in the environment but the ID isn't known:

```python
org = "https://{org}.crm.dynamics.com"
headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

# 1. Search for flows by name
filt = urllib.parse.quote("contains(name, 'OCR') or contains(name, 'Extraction')")
url = f"{org}/api/data/v9.2/workflows?$select=workflowid,name,statecode,category&$filter={filt}&$top=20"
# category=5 = Power Automate flow, statecode=1 = published

# 2. List ALL flows (no filter)
url = f"{org}/api/data/v9.2/workflows?$select=workflowid,name,statecode,category&$top=50"

# 3. Extract input/output schema from clientdata
url = f"{org}/api/data/v9.2/workflows({flow_id})?$select=clientdata"
# Parse clientdata JSON:
#   properties.definition.triggers.manual.kind="VirtualAgent" → Copilot Studio trigger
#   properties.definition.triggers.manual.inputs.schema → input parameters
#   properties.definition.actions.Respond_to_agent.inputs.schema → output parameters
```

## Flow Selection by Document Size

| Document type | Flow ID | Flow Name | Rationale |
|--------------|---------|-----------|-----------|
| Evaluation, Progress Note, Discharge, Treatment Note, Recertification | `c71672f2-113b-f111-88b4-0022480b6bd9` | OCR Text Extraction | Uses AI Builder OCR. Input: `file_name`, `document_type`, `requesting_agent`, `extraction_goal`, `file_content`. Output: `extracted_text`, `processing_status`, `char_count`, `error_message`. |
| Episode of Care (100+ pages) | `765136b6-9509-4554-9bf0-016fc63923c7` | SNF - Large Document Processor | Chunking for 100+ page docs. Same I/O schema. |

## When AI Builder Native Handling IS Sufficient

The hub `copilot-studio-yaml-reference` skill claims AI Builder handles document text natively. This is **partially true**:

| File type | AI Builder native | Needs OCR flow |
|-----------|-------------------|----------------|
| `.txt`, `.docx` (text) | ✅ Works | ❌ |
| `.pdf` (text-based) | ⚠️ Sometimes | ✅ If fails |
| `.pdf` (scanned/image) | ❌ | ✅ Always |
| `.docx` (with images) | ❌ | ✅ |
| >50 pages any format | ❌ | ✅ (chunking) |

**Rule of thumb:** If your users upload anything other than small text files, add the OCR flow. Kevin's Feedback B agent users upload PDFs and 100+ page EoC documents — the flow is required.

## Publish After OCR Patching

After patching topics with InvokeFlowAction, the bot must be published:

1. **PvaPublish API** (Dataverse-native):
   ```python
   url = f"{org}/api/data/v9.2/bots({bot_id})/Microsoft.Dynamics.CRM.PvaPublish"
   req = urllib.request.Request(url, data=b"", method="POST")
   req.add_header("Authorization", f"Bearer {dv_token}")
   ```
   Returns HTTP 200 with empty `PublishedBotContentId` — this is normal. Verify published state:
   ```python
   url = f"{org}/api/data/v9.2/bots({bot_id})?$select=botid,name,statecode,componentstate,statuscode"
   # componentstate=0 and statecode=0 means published
   ```

2. **Gateway publishv2-operations API** — alternative. Requires PPAPI token (resource `96ff4394-9197-43aa-b393-6a41652e21f8`). May return BadRoutingHeaderValue (4002) if the X-CCI-TenantId header doesn't match routing config.
