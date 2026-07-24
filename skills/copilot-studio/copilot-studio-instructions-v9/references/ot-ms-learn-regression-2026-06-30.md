# OT Microsoft Learn Regression Pattern — 2026-06-30

Context: OT_Specialist SR regressed to 90% after topic/instruction edits even though earlier OT evidence showed much higher performance. Microsoft Learn General Quality requires all subcriteria to pass; relevance alone is not enough.

## Observed regression

Latest pre-fix run inspected in UI:
- `Evaluate OT_Specialist 260630_0803`
- 90% General Quality: 90 pass / 8 fail / 2 error

Failure classes:
1. Document-check prompts such as `Can you check if my OT daily note supports medical necessity?` were answered with headings/checklists or "this action needs to be done" instead of a direct first-sentence determination. Grader marked these as **Not answered**.
2. Generic document-analysis prompts invented or assumed user-note specifics when no note text was present. Grader marked incomplete/unsupported.
3. Knowledge prompts such as discharge-summary / Section GG / cognitive-assessment questions could fail groundedness when the response added extra items not in the retrieved source.
4. Some error rows were evaluator/execution errors (`Something went wrong while evaluating this test case`) rather than clear content failures.

## Root cause

The live OT topic YAML had been trimmed to a generic block:

```yaml
- Audit this OT documentation against CMS Ch. 15, AOTA OTPF-4, and MDS/Section GG standards.
- Focus on the user's specific clinical question (...)
- Use risk levels (High/Moderate/Low).
- If no document provided, give a standards-based compliance screen with risk indicators.
```

This broke two Microsoft Learn General Quality requirements:
- **Directness / answerability:** yes/no check prompts need a direct answer in sentence 1, not a section title or checklist.
- **Groundedness:** risk levels, scores, SMART-goal recommendations, patient-specific assumptions, and extra discharge/Section GG items can fail if not supported by the retrieved knowledge or user-provided note text.

## Patch attempted and lesson learned

A narrow Microsoft Learn patch was applied to six topics (`Analyze OT Daily Note`, `Analyze OT Progress Note`, `Analyze OT Recertification Note`, `Analyze OT Discharge`, `OT Clinical Documentation Standards`, `OT General Knowledge`) to require direct first sentence and suppress unsupported scores/risk tiers/SMART goals. It improved some cases (for example discharge-summary knowledge began passing) but did not fully restore OT because document-check responses still began with `Classification` / document titles rather than a direct determination.

Fresh partial validation after patch:
- Run `Evaluate OT_Specialist 260630_0909`
- Stopped at 37/100 to avoid wasting the full eval
- 29 pass / 4 fail / 4 error
- Remaining fails were still direct-answer document-check prompts:
  - `Is my OT recertification note compliant with AOTA standards?`
  - `Can you check if my OT documentation supports medical necessity?`
  - `Can you check if my OT discharge summary supports skilled need?`
  - `Can you check if my OT recertification note meets CMS standards?`

## Correct next repair pattern

Do **not** reintroduce the old static `ot_sr_guardrail_answer`; it caused response-too-long skips and duplicate answers. Instead:

1. Restore the known-good OT search additional-instructions block from:
   `D:/my agents copilot studio/pipeline/live_agent_dump/ot_search_additional_instructions.txt`
2. Layer the Microsoft Learn override on top:
   - Sentence 1 must answer the exact question directly.
   - For yes/no document-check questions: start with `Yes, it is compliant/supports skilled need only if...` or `No, it is not compliant if...` before any checklist.
   - If no note text is provided, do not invent patient-specific findings; use a conditional standards-based screen.
   - Do not provide numeric scores, risk tiers/High-Moderate-Low labels, or SMART-goal recommendations unless explicitly requested or supported by retrieved knowledge/user note.
   - Do not invent exact regulatory citations; if exact citations are not retrieved, say the source does not specify them.
3. Preserve prior working fixes:
   - static guardrail removed,
   - no duplicate `SendActivity` before `SearchAndSummarizeContent`,
   - keep `applyModelKnowledgeSetting: true` where used,
   - if `SendActivity = Topic.Answer` is used, place it after `SearchAndSummarizeContent`, not before.
4. Publish OT and rerun the same latest 100-case SR test set.

## Auth/tooling note

During the session, Dataverse PATCH succeeded initially with HTTP 204, then later token attempts returned 401 after cache/auth state changed. Do not encode this as a permanent tool limitation. The durable lesson is: if direct Dataverse calls fail mid-session, refresh the live Copilot Studio/PAC auth context or switch to UI editing rather than claiming the topic state cannot be changed.
