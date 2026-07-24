---
name: medicare-part-b-agent-hardening
description: "Hardening checklist for Medicare Part B Compliance Agent in Copilot Studio — 23 proven fixes and architectural patterns for production readiness. Applied and verified July 2026."
---

# Medicare Part B Agent Hardening

Complete hardening checklist for the Medicare Part B Compliance Agent (Therapy AI Agents Dev environment).

## Governing Rules
- NEVER remove capabilities, features, or details without explicit user approval — all changes must be additive only
- Preserve all existing nodes and their configurations — only add new condition branches or paths alongside existing ones
- MS Learn is the source of truth for YAML patterns, entity types, and Power Fx syntax
- Verify after every PATCH — re-read the YAML, validate with yaml.safe_load(), confirm key properties are intact
- When adding a text-input path alongside file upload, ensure the file-upload path (AI Builder input binding, trigger conditions) is 100% unchanged
- **Prefer writing YAML files for UI paste over API PATCH** — the Copilot Studio UI overwrites API changes when topics are opened in the visual editor (see Workflow Pitfall section)
- **Deliver YAML files by opening Notepad** (notepad "path") after writing — user copies from Notepad into the code editor
- **Condition format depends on target:** UI code editor → bare inline (no quotes): `condition: =!IsBlank(...)`; Dataverse API PATCH → single-quoted: `condition: '=!IsBlank(...)'`. **NEVER single-quote conditions intended for the UI code editor** — the editor's YAML parser strips content inside parentheses when the value is quoted, producing empty `=!IsBlank()`. See `references/condition-quoting.md` for the full breakdown.

## YAML Editing Safety

### 1. `.Text.Content` on Message nodes
**Problem:** `SendActivity` node outputs the full `SearchAndSummarizeContent` record variable, leaking AI metadata/citations to the user.
**Fix:** Replace `{Topic.Var}` with `{Topic.Var.Text.Content}` in the `activity:` field.
**Files:** All 11 doc-audit topic YAMLs under `medicare_cleanup_2026-07-09/`

### 2. `Text()` wrapper on `in` operator
**Problem:** `"Status: Completed" in Topic.ocr_payload` can cause "Incompatible type" at runtime because `Topic.ocr_payload` may not resolve as String.
**Fix:** Wrap topic variable in `Text()`: `'="Status: Completed" in Text(Topic.ocr_payload)'`
**Notes:** Use single quotes for YAML quoting. Proven pattern from `copilot-studio-yaml-reference` pitfall #14.

### 3. `RetryCount < 0` → `< 3`
**Problem:** `=Topic.RetryCount < 0` is always false (RetryCount starts at 0 and increments), making auto-poll dead code.
**Fix:** Change to `RetryCount < 3` for up to 3 automatic retries.

### 4. `knowledgeSources:` blocks
**Problem:** `SearchAndSummarizeContent` nodes without `knowledgeSources:` produce ungrounded AI answers.
**Fix:** Add `knowledgeSources:\n  kind: SearchSpecificKnowledgeSources` after the `modelDescription:` line in the SearchAndSummarizeContent block.
**YAML indentation:** At the same indent level as other properties of the action node.

### 5. Duplicate triggers
**Problem:** `Progress_Report_Review.yml` and `Progress_Report_Review_-_Text_Paste.yml` shared identical `triggerQueries:`, causing routing ambiguity.
**Fix:** Give the Text_Paste variant unique trigger phrases.

### 6. Null guard before `.Text.Content`
**Problem:** If `SearchAndSummarizeContent` returns empty, `.Text.Content` is blank and the user sees nothing.
**Fix:** Wrap the final `SendActivity` in a `ConditionGroup` that checks `!IsBlank(Topic.Var.Text.Content)`. If blank, show a fallback message.

### 7. Global pre-commit hook
Installed at `C:\Users\kevin\.hermes_hooks\pre-commit`, configured with hooks for common YAML anti-patterns.

### 8. SendActivity `value:`/`text:` dict anti-pattern
**Problem:** Some topic YAMLs use a dict form for activity that parses but produces no visible output.
**Fix:** Replace with a flat string: `activity: "{Topic.Answer.Text.Content}"`

### 9. FilePrebuiltEntity → StringPrebuiltEntity (File+Text Input)
**Problem:** Question nodes with FilePrebuiltEntity never complete when user responds with text. The Question keeps re-prompting. This is the #1 cause of Conversational eval failures.

**Fix (additive — file upload path 100% preserved):**
1. Change `entity: FilePrebuiltEntity` to `entity: StringPrebuiltEntity`
2. Update prompt: "Paste the text of or upload the document..."
3. File check: `=!IsBlank(First(System.Activity.Attachments))` instead of `=!IsBlank(Topic.var)`
4. AI Builder binding: `=First(System.Activity.Attachments).Content` instead of `=Topic.var`
5. Add text-input else branch with SearchAndSummarizeContent + SendActivity + EndDialog
6. Keep GotoAction fallback for when neither text nor file provided

**CRITICAL — IncompatibleTypes error with `=` comparisons on StringPrebuiltEntity variables:**
When converting from ClosedListEntity to StringPrebuiltEntity, conditions using `=Topic.Var = 'value'` cause `IdentifierNotRecognized` and `IncompatibleTypes` publish errors. Fix: use the `in Text()` pattern:
```yaml
# ❌ Fails with IdentifierNotRecognized on StringPrebuiltEntity
condition: =Topic.DocumentTypeSelection = 'Evaluation and Plan of Care'

# ✅ Works — uses in operator with Text() wrapper
condition: '="Evaluation and Plan of Care" in Text(Topic.DocumentTypeSelection)'
```
The `in Text()` pattern resolves the type correctly because `Text()` explicitly converts to String, which satisfies the static validator.

**CRITICAL - AI Builder type:** Do NOT use a SetVariable to assign `First(System.Activity.Attachments)` (Record) to a String-typed variable — causes `IncorrectTypeError` on publish. Bind directly in the input expression.

**CRITICAL - Entity requirement:** A Question node requires an entity. Never remove `entity:` entirely — change the type. Removing causes `MissingRequiredProperty: Entity` on publish.

### 10. Conversational Eval Upload-Loop Diagnosis
**Symptom:** Conv eval scores 20-35% (0% by strict grader). Every case follows:
- Loop A: "What type of therapy document?" — Document Upload Intake keeps re-asking
- Loop B: "Please upload X document" — Specific topic keeps asking for file

**Root cause:** FilePrebuiltEntity loops forever without a file. The Conv test set only provides text.

**Fix:** Apply Fix #9 to all doc review topics.

**Detection via gateway API:**
```javascript
const cases = details.testCases;
for (const c of cases) {
  for (const q of c.queries) {
    if (q.answer.includes('upload') && (q.query.includes('here is') || q.query.includes('attached'))) {
      // Loop B detected
    }
  }
}
```

## 11. pac CLI Publish — Not Cached, Always Retry
**Misconception:** The "Failed [timestamp]" display looks like a cached failure from the first attempt. **It is not.** Each `pac copilot publish` call re-runs full validation. The timestamp shown is the last attempt's result. Always try `pac copilot publish` first — it works even after showing the same timestamp multiple times. Check the bot's `publishedon` field from Dataverse for the real publish timestamp.

To verify publish succeeded: query the bot's `publishedon` field from Dataverse:
```python
GET /bots({botId})?$select=publishedon
# Returns timestamps like: 2026-07-11T11:15:55Z
```

## 12. Question Entity Requirement
A Question node requires an entity. Removing it causes `MissingRequiredProperty: Entity`. Use `StringPrebuiltEntity` to accept any text input while allowing file attachments via `System.Activity.Attachments`.

## Text-Input Additive Else Branch Template

**IMPORTANT — This is the bare inline format for the UI code editor.** Do NOT wrap condition values in quotes or the editor strips them.

```yaml
      elseActions:
        - kind: ConditionGroup
          id: conditionGroup_text_check
          conditions:
            - id: condition_has_text
              # Bare inline format — no quotes around the Power Fx expression
              condition: =!IsBlank(Trim(Topic.DocumentText))
              actions:
                - kind: SearchAndSummarizeContent
                  id: search_text_audit
                  variable: Topic.AuditResult
                  userInput: '=Concatenate("Audit this documentation:\n\n", Topic.DocumentText, "\n\nProvide assessment...")'
                  applyModelKnowledgeSetting: true
                  responseCaptureType: FullResponse
                - kind: SendActivity
                  id: sendActivity_text_audit
                  activity: "{Topic.AuditResult}"
          elseActions:
            - kind: GotoAction
              id: goto_upload_retry
              actionId: question_upload_doc
```

**CRITICAL:**
- Use `Topic.DocumentText` (the Question's variable), not `System.Activity.Text`
- NO single quotes around the condition value: `condition: =!IsBlank(Trim(Topic.DocumentText))`
- Single quotes cause the editor to strip to empty `=!IsBlank()` — verified across 6 topics Jul 10-11 2026
- Remove the `SetVariable` block — the Question node already captured the text into `Topic.DocumentText`
- If using the AI Builder file path alongside: use `=First(System.Activity.Attachments).Content` for the input binding, NOT `SetVariable` + `=Topic.var`

## YAML Editing Safety
- NEVER remove lines by index from a split list — always use targeted `data.replace(old, new)` on the complete YAML string
- Verify YAML with `yaml.safe_load()` after every edit
- Re-read and check key properties after every PATCH
- **Patch tool CRLF→LF reformatting**: The `patch` tool may normalize line endings (CRLF→LF) when rewriting files, inserting blank lines between every line. This doubles the YAML line count (e.g. 125→250 lines). YAML content is preserved and valid, but the reformatting is noisy. If a file's line count doubles after a patch, restore from Dataverse GET (live original) or use targeted `data.replace()` in Python instead of the patch tool on large blocks.

## Verification After All Fixes
```python
checks = ['FilePrebuiltEntity' not in data,
          'StringPrebuiltEntity' in data,
          'First(System.Activity.Attachments)' in data,
          'set_file_input_' not in data,
          yaml.safe_load(data)]
assert all(checks), f'Verification failed for {cid}'
```

## Related Files
- `references/stale-begindialog-ids.md` — Troubleshooting stale BeginDialog topic IDs
- `references/gateway-api-eval-scripts.md` — Reusable eval scripts (check_medicare_eval.cjs, run_conv_eval.cjs, poll_eval.cjs)
- `references/live-patch-inline-quote.md` — Exact curl recipe for live Dataverse PATCH + verify (instr component type 15 / topic type 9) and the inline-quote rule texts
- `scripts/pre-commit-hook.sh` — The global pre-commit hook

## 13. ConvStart EndDialog (Conversational Eval Scaffolding)
**Problem:** ConvStart topic ends with `SendActivity` but no `EndDialog(clearTopicQueue: true)`. Without it the agent never terminates the initial topic, so subsequent user turns get no response or fall into error handlers → Conv eval tanks. This is the #1 documented Conv eval killer per MS Learn.

**Fix (additive):** Add EndDialog with clearTopicQueue: true as the LAST action in ConvStart:
```yaml
  - kind: SendActivity
    activity: Hello. I can review therapy documentation...
  - kind: EndDialog
    id: end_conversation_start
    clearTopicQueue: true
```

**Already verified live** on Medicare Part B Compliance Agent ConvStart topic (componentId: 57d758c7).

## 14. Cloned Resource Repositories (Jul 2026)
The following repos are cloned at `C:\Users\kevin\` and contain reusable patterns, YAML schemas, and agent templates:

| Repo | Path | Contents |
|------|------|----------|
| skills-for-copilot-studio | `C:\Users\kevin\skills-for-copilot-studio\` | Microsoft official — 20 skills, 15 patterns, YAML schema |
| awesome-copilot-studio-agents | `C:\Users\kevin\awesome-copilot-studio-agents\` | 89 M365 agent instruction templates |
| cat-agent-skills | `C:\Users\kevin\cat-agent-skills\` | Copilot Studio community gallery |
| agent-academy | `C:\Users\kevin\agent-academy\` | Microsoft training (prompts, cards, flows) |
| awesome-copilot | `C:\Users\kevin\awesome-copilot\` | Community Copilot resources |
| mcscatblog | `C:\Users\kevin\mcscatblog\` | Microsoft CAT blog |

Use `read_file` to access any file within these repos. The `copilot-studio-microsoft-skills` skill has the full index.

## 15. M365 Declarative Agent → Copilot Studio Topic Remix

The 89 agents in `awesome-copilot-studio-agents` are M365 declarative agent instruction blocks. They can be remixed into Copilot Studio topics:

1. **Instructions:** The agent's `## Instructions` block goes into `additionalInstructions` on SearchAndSummarizeContent, or into the agent-level Instructions field (Settings → General)
2. **Triggers:** Extract from `## Conversation Starters` section
3. **Guardrails:** The `WHAT YOU DO NOT DO` section becomes else-branches or condition checks
4. **Output format:** The agent's template becomes the SendActivity activity text

See `copilot-studio-microsoft-skills` skill → `templates/m365-to-cs-remix.md` for the full conversion guide and `templates/document-reviewer-topic.yaml` for a worked example.

## 16. Gateway API Eval Scripts (Jul 2026)
Written and used this session at `D:/my agents copilot studio/pipeline/scripts/`:
- `check_medicare_eval.cjs` — List recent runs, get details, analyze failures
- `run_conv_eval.cjs` — Launch a new Conv eval
- `poll_eval.cjs` — Poll completion of a running eval

All use MSAL cache auth (no interactive login). See `references/gateway-api-eval-flow.md` for the API endpoints and patterns.

## 17. Response Formatting Override (Settings → Generative AI → Responses)
**Problem:** The Response formatting field under Settings → Generative AI → Responses OVERRIDES the agent's main instructions when conflicts exist. The previous content was:
```
Respond concisely. Use 2-3 bullet points with inline citations. No headers or markdown. Keep responses under 4 sentences for simple questions.
```
The phrase "No headers or markdown" directly contradicted Route A's DOCUMENT REVIEW OUTPUT CONTRACT (which requires markdown headers, tables, 🔴🟡🟢), causing the agent to strip all formatting from audit outputs.

**Diagnosis:** This field is UI-only — not accessible via Dataverse API (see `references/generative-ai-responses-api-gap.md`). The small print says "If these conflict with other instructions for this agent, these will override."

**Recommended text (~380 chars, under 500 limit):**
```
Follow your route-specific output contracts:
• Document audits — markdown headers, tables, 🔴🟡🟢 risk ratings, inline citations
• General questions — 2–3 concise bullet points with citations
• Missing docs — state what's needed, invite paste

Cite sources, disclose AI status, keep simple answers under 4 sentences.
```

**Key change:** Removed "No headers or markdown" which was breaking audit formatting. The routes are defined in the main instructions (Route A/B/C). This field now references them instead of conflicting.

## Update path:** Manual paste in Copilot Studio UI → Settings → Generative AI → Responses. No API path exists.

## 18. API-vs-UI Cache Conflict (Critical Workflow Pitfall)

**Problem:** Copilot Studio's SPA caches topic YAML in browser memory. When you PATCH via Dataverse API and then open the topic in the UI editor, the UI shows its cached (pre-PATCH) version. If you then save in the UI, it **overwrites** the API changes with the old cached version, reverting all fixes.

**Symptoms:**
- Topics "reset" or "undo" themselves after being fixed
- A topic that was valid becomes invalid after opening in the UI
- "Can't load variable set action" errors — UI can't render API-modified YAML

**Root cause:** The Copilot Studio SPA loads topics into memory on first open and doesn't re-fetch them from the server when you navigate between topics. API PATCHes modify the server-side data, but the UI never knows about them.

**Workflow rules (prevent this):**
1. **Pick ONE channel** — use either API PATCH OR UI editor, never both for the same topic
2. **If you must switch channels:** Close the browser tab completely → reopen → verify YAML in code editor before saving
3. **Shift+Reload** in Chrome bypasses cache for that page
4. **F12 → Network → Disable cache** checkbox while DevTools is open ensures fresh loads
5. **Direct URL navigation** bypasses some caching: navigate to `https://copilotstudio.microsoft.com/environments/{env}/bots/{bot}/adaptive/{topic-guid}` instead of clicking topics in the list

**Preferred approach:** Write corrected YAML to files → user pastes into UI code editor → UI is sole source of truth. No API PATCHes for topics the user will edit.

**Reference:** See `references/api-vs-ui-cache-conflict.md` for full reproduction steps.

## 19. Inline Verbatim Quote + Citation Pattern (Audit/Extraction Topics)
**Problem:** User added citation/quote requirements to agent-level Instructions AND the Response-formatting field, but audit output showed only regulation citations — never the quoted flagged source text.
**Root cause:** The audit prose is generated inside `SearchAndSummarizeContent` (the topic's `userInput`/`additionalInstructions`), NOT by the agent-level Instructions at response time. Agent Instructions govern routing/guardrails, but the actual audit text is produced by the SearchAndSummarizeContent call in the topic. Adding the rule only at the agent level is insufficient — the model paraphrases the gap instead of echoing the exact flagged phrase.
**Fix (additive — both places):**

1. **Agent Instructions** — add a guardrail requiring verbatim inline quotation, e.g.
   `G4a. Inline Quoted Evidence (MANDATORY for document reviews): For every finding on a submitted document, quote the EXACT verbatim phrase from the user's documentation inline, immediately followed by its regulation citation. Format: > "[exact phrase]" — [Regulation citation]. If the phrase is missing, write > "[Not documented in submitted note]" — [citation].`
2. **Topic `SearchAndSummarizeContent`** — embed a "MANDATORY INLINE QUOTE RULE" inside the `userInput` Concatenate string AND restate it in `additionalInstructions` (verbatim quotation inline with citation).

**Verified live (Jul 13 2026):** PATCH of instructions component (type 15) + Progress Report Review topic (type 9) returned HTTP 204; GET readback confirmed both rules persisted. Exact recipe in `references/live-patch-inline-quote.md`.

## 20. YAML Editing Safety — Unquoted Scalar With Internal Colon Breaks Parse
**Problem:** A value like `additionalInstructions: Provide ... For each finding: quote the literal phrase ...` fails YAML parse with `mapping values are not allowed here` because the unquoted scalar contains a `:` mid-value.
**Fix:** Double-quote the entire value: `additionalInstructions: "Provide ... For each finding, quote the literal phrase ..."`. Applies to ANY field whose plain-scalar value contains `:`, `{`, `}`, `#`, or starts with a special char.
**Distinct from condition quoting (pitfall #9 / `references/condition-quoting.md`):** conditions need single quotes around the Power Fx expression (`condition: '=!IsBlank(...)'`); plain prose values need double quotes. Mixing them up is the usual cause of this parse error.

## 21. Live Dataverse PATCH + Verify Workflow (validated one-way push)
**Context:** #18 warns that opening a topic in the UI after an API PATCH overwrites the server change (API-vs-UI cache conflict). That makes API PATCH invalid as a *two-way* edit, but it is a VALID *one-way push* when you will NOT also hand-edit that same topic in the UI afterward. This session validated the full push+verify loop.
**Recipe (exact curl in `references/live-patch-inline-quote.md`):**
1. Token: `TOKEN=$(az account get-access-token --resource "https://orgbd048f00.crm.dynamics.com" --query accessToken -o tsv)`
2. PATCH instructions component (type 15) or topic (type 9):
   `PATCH https://orgbd048f00.api.crm.dynamics.com/api/data/v9.2/botcomponents({GUID})`
   body `{"data": <instructions text OR full topic YAML>}`, headers `Authorization: Bearer $TOKEN`, `Content-Type: application/json`, `OData-Version: 4.0`.
3. Expect **HTTP 204** (no body).
4. **VERIFY readback:** `GET .../botcomponents({GUID})?$select=data` and assert the new rule text is present in `data`. Never assume success from 204 alone — confirm the readback.
**DNS quirk:** `orgbd048f00.api.crm.dynamics.com` intermittently fails DNS (Non-existent domain). If PATCH fails that way, retry or fall back to UI paste (#18). This session DNS resolved, so PATCH succeeded.
**When to use vs UI paste:** Use live PATCH for fast additive pushes across many components + programmatic verify. Use UI paste (Notepad → code editor) when the user will subsequently hand-edit in the visual editor.

## 22. High-Performance Architecture — AI Builder Models Replacing Async OCR (July 12 Snapshot)

**Context:** A version of the agent tested at ~90% Conv eval pass rate replaced the async Power Automate OCR pipeline with individual AI Builder models per document type. This snapshot exists at `C:/Users/kevin/Desktop/Pacific-Coast-Therapy-Hub/_medicare_ref/` (dated July 12 2026, 21:02).

**Architecture differences vs async OCR version:**

| Feature | Async OCR (current live) | AI Builder (July 12 ref) |
|---------|------------------------|--------------------------|
| File input | `FilePrebuiltEntity` → async Power Automate OCR flow | `StringPrebuiltEntity` + `First(System.Activity.Attachments).Content` |
| Text input | Separate Text Paste duplicate topic | Built into each topic via else-branch |
| Text processing | SearchAndSummarizeContent on `Topic.ocr_payload` | SearchAndSummarizeContent on `Topic.DocumentText` directly |
| File processing | InvokeFlowAction → poll loop → SearchAndSummarizeContent | `InvokeAIBuilderModelAction` (AI Builder model) → direct result |
| Topic size | ~130-300 lines per topic | ~74 lines per topic |
| Topics removed | — | Large_Document_OCR_Extraction, Check_Async_OCR_Job_Status, Check_OCR_Status, Text Paste duplicate |
| OCR polling | `InvokeFlowAction` with retry logic | None |

**Key structural pattern (from Progress_Report_Review.yml snapshot):**
```yaml
  actions:
    - kind: Question
      variable: init:Topic.DocumentText
      entity:
        kind: StringPrebuiltEntity
      prompt: Paste the text of or upload the Progress Report document...
    - kind: ConditionGroup
      conditions:
        - id: condition_file_uploaded
          condition: =!IsBlank(First(System.Activity.Attachments))
          actions:
            - kind: InvokeAIBuilderModelAction
              aIModelId: 2ae9d680-9db2-4dbd-8446-37589397ca0f
              input:
                binding:
                  ProgressReportInput: =First(System.Activity.Attachments).Content
              output:
                binding:
                  predictionOutput: Topic.ProgressReportResults
            - kind: SendActivity
              activity: "{Topic.ProgressReportResults.text}"
      elseActions:
        - kind: ConditionGroup
          conditions:
            - id: condition_has_text
              condition: =!IsBlank(Trim(Topic.DocumentText))
              actions:
                - kind: SearchAndSummarizeContent
                  variable: Topic.AuditResult
                  userInput: '=Concatenate("Audit this...\\n\\n", Topic.DocumentText, "...")'
                  applyModelKnowledgeSetting: true
                  responseCaptureType: FullResponse
                - kind: SendActivity
                  activity: "{Topic.AuditResult}"
          elseActions:
            - kind: GotoAction
              actionId: question_upload_doc
    - kind: EndDialog
```

**Each topic uses its own AI Builder model ID** (unique GUID per document type). The models were already registered in Dataverse. To find them: query the `aIBuilderModelAction` blocks in each topic YAML in `_medicare_ref/`.

**Missing from snapshot:** Instructions component (separate), Treatment Encounter Note topic (not in ref — may have been removed or not backed up).

**Trade-offs:**
- **Pro:** Much simpler topics, no OCR poll latency, no OCR flow binding errors, higher eval scores (~90%)
- **Con:** Requires AI Builder model registration per document type; no async OCR fallback for very large documents; Treatment Encounter topic may need separate handling

**To restore this version:** PATCH each topic component in Dataverse with the ref YAML (GET component ID from `GET /botcomponents?$filter=_parentbotid_value eq '{botguid}' and componenttype eq 9`). Verify AI Builder model IDs still active before pushing.

**Conversation_Start snapshot** is a minimal 11-line version:
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnConversationStart
  id: main
  actions:
    - kind: SendActivity
      activity: Hello. I can review therapy documentation for Medicare Part B compliance and denial risk. Tell me what you need.
    - kind: EndDialog
      clearTopicQueue: true
```

**Document_Upload_Intake** routes via ClosedListEntity to each doc type — simpler than current version.

**Reference file:** `references/ai-builder-high-perf-architecture.md` — Full YAML of all 17 topic files from the snapshot, AI Builder model IDs per topic.

## 23. Cross-Agent Knowledge Sharing via Instructions

**Problem:** Knowledge source files (type 19 components) are per-agent — no Dataverse API to share them across agents. Uploading the same files multiple times is impractical for fleet management.

**Solution:** Add the same approved knowledge source descriptions and knowledge hierarchy to the target agent's instructions component (type 15). The model reads the instructions and applies the same regulatory framework, even without direct file access.

**When to use:** Give a second agent (e.g. Pacific Coast Case Historian) the same regulatory grounding as the Medicare Part B Compliance Agent without re-uploading every CMS/Medicare knowledge file.

**Limitations:** Instructions-based knowledge won't give the model direct file access — it can't search file content or quote verbatim from knowledge PDFs. For full file-grounded answers, actual knowledge files must still be uploaded per-agent. Works best for citation standards, regulation hierarchy, scoring methodology, and framework descriptions.

**Full recipe:** `references/cross-agent-knowledge-sharing.md`

## 24. Route D Expansion — Explicit "how do I get" Handling in Instructions (Validated 2026-07-14)

**Problem:** Questions starting with "how do I get" (color-coded risk ratings, coaching, compliance summaries) were being answered with "paste the text" (Route C behavior) instead of being handled as procedural questions (Route D). The agent has routing disambiguation but the original patterns didn't cover this specific phrasing.

**Signal in SR evaluation:** `completeness=No` + answer contains "paste the text" or "paste the therapy note text" — the question is about what the agent CAN do, not asking for an audit of a specific document.

**Fix (additive to instructions component type 15):** Add a PROCEDURAL ROUTE EXPANSION section after the existing ROUTING DISAMBIGUATION block in the agent instructions:

```
  # PROCEDURAL ROUTE EXPANSION — "how do I get" patterns (Route D)
  - Questions starting with "how do I get" (e.g., "how do I get color-coded risk ratings", "how do I get coaching", "how do I get a compliance summary") are procedural Route D questions. Answer directly: EXPLAIN that color-coded risk ratings (🔴🟡🟢) are AUTOMATICALLY generated for each section of every audit. Coaching on strengths/weaknesses is part of every audit output. Do NOT just say "paste the text" — describe WHAT the agent will produce, then invite document paste as a SECOND step.
  - Questions about "what are the five sections you audit" — this is Route B. LIST the five sections directly from knowledge...
  - Questions like "Can you review my documentation for compliance with the Medicare Benefit Policy Manual" or "Does my evaluation meet CMS standards" — these are Route B (general compliance). Answer from approved sources. Do NOT route to Fallback "I could not find an answer".
```

**Apply via:** Dataverse PATCH on instruction component `1b6244b9-f417-4027-a601-0d94c9d3ef9c` (type 15). Insert the expansion text after the ROUTING DISAMBIGUATION block ends.

**Verify:** Run a targeted SR eval, check that "how do I get color-coded risk ratings" and similar questions no longer contain "paste the text" as the primary answer."
