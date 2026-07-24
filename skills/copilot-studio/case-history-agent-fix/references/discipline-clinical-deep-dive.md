# Discipline Clinical Deep Dive (PCR Reviewing Agent)

Validated live 2026-07-16 ~11:57 PM Pacific on bot `f19e1c40` (Therapy AI Agents Dev). Publish status Succeeded.

## Intent
After the first case-history report, let the clinician open a **knowledge-grounded** PT/OT/SLP deep dive: finding → clinical meaning → significance for eval → day-1 precautions (e.g. med class → effect → risk → precaution). Not a note writer; not free-floating opinion.

## Live IDs
| Item | Value |
|------|--------|
| Topic name | Discipline Clinical Deep Dive |
| botcomponentid | `4f5099b3-ab81-f111-ab0e-70a8a59d4e65` |
| schemaname | `cr917_CaseHistoryReviewingAgent.topic.DisciplineClinicalDeepDive` |
| Local YAML | `C:\Users\kevin\Desktop\pcr_DisciplineClinicalDeepDive.yaml` |

## Architecture (do not put the card on Fallback)
```
Clinical Analysis / Multi-Discipline / Fallback
  → SendActivity(report)
  → gate:
       long paste OR keywords (case history, eval, synthesize, hospital course, clinical document)
         → BeginDialog → DisciplineClinicalDeepDive  (AdaptiveCard)
       else
         → text hint with trigger phrases only
  → EndDialog clearTopicQueue

DisciplineClinicalDeepDive:
  AdaptiveCardPrompt (PT | OT | SLP | ALL | SKIP)
  → if SKIP: short ack + EndDialog
  → else: SASC (SearchSpecificFiles ×16 + 2 knowledge packs, applyModelKnowledgeSetting: true)
  → SendActivity deep dive + re-prompt phrases
  → EndDialog clearTopicQueue
```

**Why Fallback is text-only:** AdaptiveCardPrompt on the SR catch-all path returns interactive content → grader Abstention. Keep card on the dedicated topic; Fallback only advertises trigger phrases.

## Deep-dive SASC contract
- Patient facts only from prior report in conversation + user message this turn
- Knowledge files: Beers, labs, APTA, AOTA, ASHA, IDDSI, vitals, CMS discharge/billing, Ensign postettes, etc. (same 16 as Clinical Analysis)
- KBs: Core Clinical Manuals + Therapy Shared Knowledge
- `applyModelKnowledgeSetting: true` so clinical mechanism/precaution reasoning is allowed while still file/KB grounded
- Sections: snapshot → Finding/Meaning/Significance/Eval → meds-labs → imaging/course → safety checklist → assessment focus → gaps
- Footer: DRAFT — CLINICAL REVIEW REQUIRED

## userInput formula (publish-safe)
```yaml
userInput: "=Concatenate(\"Provide a DISCIPLINE-SPECIFIC clinical deep dive ... Target discipline(s): \", Topic.SelectedDiscipline, \". ... USER MESSAGE: \", System.Activity.Text)"
```
- Double-quoted YAML string; escaped inner quotes
- **Do not** wrap `Topic.SelectedDiscipline` or `System.Activity.Text` in `Text()` here (publish: "Text has some invalid arguments")
- **Do not** Concatenate complex `Global.Answer` records into the prompt (type errors). Prefer conversation context + user message text

## Adaptive Card requirements (publish)
- `Input.ChoiceSet` with `isRequired: true` **must** include `errorMessage`
- `label` on ChoiceSet required
- `Action.Submit` with unique `data.actionSubmitId`
- `output` + `outputType.properties.selectedDiscipline: String` (shorthand form works)

## Wiring Clinical Analysis / Multi-Discipline
Allowed post-SASC additions (does **not** violate "don't change CA grounding"):
1. `SendActivity` of the report (CA previously ended with **no SendActivity** — silent topic risk)
2. Gated `BeginDialog` to DisciplineClinicalDeepDive
3. `EndDialog clearTopicQueue: true`

**Do not change:** CA `applyModelKnowledgeSetting: false`, SearchSpecificFiles list, or trigger phrase expansion (eval regression -11pp history).

Keep SASC `variable: Global.Answer` on CA (original). Do **not** reassign to `Global.Answer.Text` without re-validating types.

## Global.Answer typing (Fallback vs CA)
On this bot, Fallback SASC uses `variable: Global.Answer.Text` and display:
```yaml
activity: "{Global.Answer.Text}"
```
**Not** `{Global.Answer.Text.Content}` — platform error: "The '.' operator cannot be used on Text values" when Text is already a String.

If you need a string cache of the last report:
- `init:Global.LastCaseHistoryReport` in **exactly one** topic only (`DuplicateVariableInitializer` if multiple topics use `init:`)
- Other topics: `variable: Global.LastCaseHistoryReport` without `init:`, and only assign **strings**
- Assigning SASC FullResponse records into a String global fails publish (`IncorrectTypeError`)

Often safer: skip the global cache; deep dive uses conversation context + user message.

## PATCH offset bug (FullResponse → FullRespon)
If you `re.sub` a longer replacement earlier in the YAML (e.g. `Global.Answer` → `Global.Answer.Text`) **then** slice with a match position computed **before** the sub, all later offsets shift. Result: `responseCaptureType: FullResponse` becomes `FullRespon` and publish fails with "not a recognized option".

**Rule:** recompute regex match positions after every length-changing edit, or rebuild from backup + append tail only.

## Trigger phrases (standalone)
- discipline clinical deep dive
- PT / OT / SLP deep dive
- more PT|OT|SLP clinical detail
- what does this mean for PT|OT|SLP evaluation
- all three discipline deep dives

## Test checklist
1. Shift+Reload Studio
2. Paste full case history / eval-prep request → report → card or text hint
3. Choose SLP → deep dive with precautions, not restatement only
4. Short med/lab Q → no card (gate), only text path or other topics
5. Confirm `publishedon` advanced; status Succeeded
