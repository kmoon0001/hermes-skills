---
name: case-history-agent-fix
description: Use when fixing, comparing, or disambiguating Case History family agents in Copilot Studio (Reviewing Agent vs Case_History_Assistant vs Case Historian). Systematic diagnosis of auth gate, Fallback missing SASC, Conversational boosting missing SendActivity, and missing clearTopicQueue. Proven +3pp on a 31% baseline, validated 2026-07-15 across 5 eval runs.
category: copilot-studio
---

# Case History Agent Fix Protocol

## Overview
Systematic fix loop for Case History Reviewing Agents (acute hospital record → SNF therapy evaluation prep) failing Copilot Studio evaluations. These agents typically have a working Clinical Analysis topic but suffer from catch-all path defects. **The key lever is the Fallback/ConvBoosting catch-all, NOT the specific matched topic.**

## When to Use
- Agent is called "Case History Reviewing Agent", **Pacific Coast Case History Reviewing Agent**, or similar acute-to-SNF documentation review
- User says "Case History Assistant" / `Case_History_Assistant` — confirm bot ID; may mean Reviewing Agent (voice typo) OR the separate timeline bot
- User asks similarities/differences among Case History family agents
- SR eval scores below 50%
- Fallback just says "I'm sorry" — no SearchAndSummarizeContent
- Conversational boosting computes Topic.Answer but never displays it
- User wants friendly/scannable report formatting, PT/OT/SLP discipline-lensed insights, or Generative AI Responses rewrite/inject
- User wants **post-report Adaptive Cards / buttons** for PT/OT/SLP clinical deep dives (finding → meaning → eval precautions), knowledge-grounded

## Live identity matrix (Therapy AI Agents Dev — orgbd048f00)
**Three different bots.** Confirm `botid` before any PATCH/publish/eval. Full comparison: `references/agent-identity-and-comparison.md`.

| Agent | Bot ID | Schema | Mission (one line) |
|-------|--------|--------|--------------------|
| **Pacific Coast Case History Reviewing Agent** (primary for this skill) | `f19e1c40-f07e-f111-ab0e-70a8a5b24e56` | `cr917_CaseHistoryReviewingAgent` | Acute hospital record → SNF **PT/OT/SLP eval prep** synthesis |
| **Case_History_Assistant** | `aed96eb7-dd80-f111-ab0e-70a8a59d4e65` | `cr917_CaseHistoryAssistant` | Hospital-stay **timeline + intake** compiler (not discipline eval prep) |
| **Pacific Coast Case Historian V2** | `ad635500-cf47-f111-bec5-70a8a5b1c3a3` | `auto_agent_XRF5I` | Fleet **longitudinal** SBAR / MDS / IDT / denial-risk (connected agents) |

### Reviewing Agent (default fix target)
| Field | Value |
|-------|--------|
| Display name | Pacific Coast Case History Reviewing Agent |
| Bot ID | `f19e1c40-f07e-f111-ab0e-70a8a5b24e56` |
| Instructions component (type 15) | `cc349f24-eccc-4952-a9ce-366561520185` |
| Schema GPT | `cr917_CaseHistoryReviewingAgent.gpt.default` |
| Auth | Integrated (2); Sign-in topic **inactive** (statecode=1) |
| Discipline deep dive topic | `4f5099b3-ab81-f111-ab0e-70a8a59d4e65` / `cr917_CaseHistoryReviewingAgent.topic.DisciplineClinicalDeepDive` (live 2026-07-16) |

### Case_History_Assistant (do not treat as Reviewing Agent)
| Field | Value |
|-------|--------|
| Display name | Case_History_Assistant |
| Bot ID | `aed96eb7-dd80-f111-ab0e-70a8a59d4e65` |
| Type-15 | `568d5ddd-d9d7-485a-9884-7a6bfa252a50` / `cr917_CaseHistoryAssistant.gpt.default` |
| Auth | Integrated (2); Sign-in **active** (statecode=0) |
| Catch-all | Fallback is stock apology only (no SASC) — same class of defect this skill fixes |
| Output default | 2–3 bullets, under 800 chars, **no headers/markdown** (opposite of Reviewing Agent report standard) |
| Custom topics | Case History Collection, Hospital Stay Timeline, Timeline Synthesis |
| Knowledge | No type-14 files / type-16 packs like Reviewing Agent; thinner SSKS path |

## Char budgets + report format (user standard)
- Instructions body: under **7000**, prefer **~6000** — compress wording only; never drop features.
- Generative AI Responses / `responseInstructions`: under **500** chars.
- When the user expects injection, PATCH type-15 `data` (do not only paste into chat). Put structure detail in instructions; put a dense format skeleton in `responseInstructions` so the Responses override does not fight the body.
- **Always update BOTH fields when report structure changes.** If Responses lists a different section order than instructions, the override wins and silently undoes the rewrite.
- **Keep Timeline as its own early section.** Course-phase on passages is not a substitute. Timeline = scannable Date—Event—Source—Course phase—Follow-up bullets; Hospital course = narrative. Dropping Timeline to save chars was rejected — restore both.
- Full report shape (11 sections): Snapshot → **Timeline** → Referral → Hx → Course → Function/PLOF → Meds/Labs/Imaging → **separate PT / OT / SLP** (Insight + Significance + anchors each) → Clinical insights for eval/goals/POC → Gaps → 3–6 takeaways (safety first). Every fact `[Source — Date — value]`. Passages: finding + source + date + course phase + follow-up. Missing=`not found in record`. Footer: `DRAFT — CLINICAL REVIEW REQUIRED`.
- MS Learn rewrite shape for the instructions body: Role → Constraints → Guidance (data-rich vs sparse) → What to extract → Response format → Discipline lens → Regulatory → Safety. Action verbs; one place for each rule; give outs (`not found`, `To verify`).
- Templates: `references/response-format-under500.txt`, `references/instructions-mslearn-template.md`. Validated injects 2026-07-17 (final Timeline restore: body ~5535 / RI 489; PATCH 204 + publish Succeeded).
- Family identity + Assistant vs Reviewing comparison: `references/agent-identity-and-comparison.md`.
- Post-report PT/OT/SLP deep-dive (cards + knowledge-grounded SASC): `references/discipline-clinical-deep-dive.md`.

## Step 1: Diagnose

### Query live components
```
AZ = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
subprocess.run([AZ, 'account', 'get-access-token', '--resource', 'https://orgbd048f00.crm.dynamics.com/'], ...)
# Get all botcomponents for the bot via Dataverse API
```

### Check auth mode
- `authenticationmode: 2` (Integrated) → OnSignin fires on every conversation
- If Sign-in topic is `statecode: 1` (INACTIVE) → auth gate mitigated
- Flipping to `authenticationmode: 0` (None) breaks publish with `ManualAuthenticationInputNotEnabled` if topics use SearchSpecificFiles, FilePrebuiltEntity, or SharePoint KBs

### Check Fallback topic (OnUnknownIntent)
- **Must have:** `SearchAndSummarizeContent` + `SendActivity(=Topic.Answer)` + `EndDialog(clearTopicQueue:true)`
- If it only says "I'm sorry" → **HIGHEST IMPACT FIX**

### Check Conversational boosting (OnUnknownIntent, priority=-1)
- **Must have:** `SendActivity activity: =Topic.Answer` BEFORE the EndDialog
- If it computes Topic.Answer then ends without showing → FIX THIS

### Check system topic clearTopicQueue
- ConversationStart, Greeting, Goodbye — add `clearTopicQueue: true` to existing EndDialog

### Check test case query categories
- Query Dataverse: `componenttype eq 19` records contain test case queries
- Categorize to see what the test set asks about (meds/labs, discharge, safety, etc.)
- Map categories to which topic would catch them based on trigger phrases

## Step 2: Apply Fixes

### Fix #1: Fallback topic (HIGHEST IMPACT — +3pp)
Replace the generic apology with SASC + SendActivity + EndDialog:
```yaml
- kind: SearchAndSummarizeContent
  userInput: =System.Activity.Text
  additionalInstructions: |-
    Analyze the user's hospital-record or clinical-documentation request...
  allowLatencyMessage: false
  applyModelKnowledgeSetting: true
  responseCaptureType: FullResponse
- kind: SendActivity
  activity: =Topic.Answer
- kind: EndDialog
  clearTopicQueue: true
```
Keep the retry-count ConditionGroup for FallbackCount < 3 with the SASC.

### Fix #2: Conversational boosting
Add `SendActivity activity: =Topic.Answer` before the EndDialog inside the `!IsBlank(Topic.Answer)` condition.

### Fix #3: clearTopicQueue on system topics
Add `clearTopicQueue: true` to ConversationStart, Greeting, Goodbye EndDialogs.

### Fix #4: Clinical Analysis topic — DO NOT MODIFY grounding (validated regression)
The Clinical Analysis topic uses `applyModelKnowledgeSetting: false` + `SearchSpecificFiles` (16 specific files) + `SearchSpecificKnowledgeSources`. This is restrictive by design.

**Validated 2026-07-15:** Flipping `applyModelKnowledgeSetting: false → true` AND removing the `BeginDialog` to Multi-Discipline Summary AND expanding trigger phrases from 12 → 34 regressed score from 34% → 23% (-11pp).

**Why it regressed:** The topic was already working for its specific matched cases. Changes pulled more queries into the restrictive topic path instead of letting them fall to the better Fallback SASC. **Don't change working SASC configuration or trigger sets. The lever is the catch-all path.**

**Allowed after SASC (feature work, 2026-07-16):** `SendActivity` of the report (CA historically had **no SendActivity** — silent path risk), then gated `BeginDialog` to Discipline Clinical Deep Dive, then `EndDialog clearTopicQueue: true`. Do **not** put AdaptiveCardPrompt on Fallback (kills SR eval).

### Fix #5: Auth mode — keep Integrated if Sign-in is deactivated
If Sign-in topic is inactive (statecode=1), auth gate is already mitigated. Flipping to None will break publish if topics have auth-dependent nodes. Leave at Integrated.

### Fix #6: Post-report PT/OT/SLP clinical deep dive (user feature)
Full recipe: `references/discipline-clinical-deep-dive.md`.

Summary:
1. Create dedicated topic **Discipline Clinical Deep Dive** (card + SASC with same 16 files + 2 KBs, `applyModelKnowledgeSetting: true`).
2. After full reports on Clinical Analysis / Multi-Discipline: gate on long paste / keywords → `BeginDialog` to deep dive; else text hint with trigger phrases.
3. Fallback: **text offer only** after report (no card) so SR eval stays non-interactive.
4. Deep dive card options: PT | OT | SLP | ALL | SKIP → knowledge-grounded interpretation + precautions.
5. Publish must Succeed; verify `publishedon` advanced.

## Step 3: Publish & Evaluate
```bash
pac copilot publish --bot <bot-id> --environment "https://orgbd048f00.crm.dynamics.com"
```

Run SR eval via Gateway API:
```python
body = {'testSetId': '<guid>', 'runName': 'ITER_N'}
POST /environments/{env}/bots/{bot}/makerevaluations
```

Poll with `GET /makerevaluations?$top=5`. Token expires ~15-60 min — refresh with `refresh_eval_token.cjs`.

## Expected Results (validated 2026-07-15, Case History Reviewing Agent f19e1c40)

| Iteration | Fixes | Score | Delta |
|-----------|-------|-------|-------|
| Baseline | Original (no fixes) | 31% | — |
| **Iter 1 🏆** | Fallback SASC + ConvBoost SendActivity + clearTopicQueue | **34%** | **+3pp** |
| Iter 2 | + Clinical Analysis changes (reverted: -11pp regression) | 23% | ❌ |
| Iter 3 | + Fallback instructions expanded (no change) | 32% | ±0 |
| Latest | Same as Iter 1 (reverted CA) | ~34% | Winning |

**Conclusion:** +3pp is the ceiling for the catch-all fix layer. Architectural redesign (below) targets additional gains.

### Architectural Redesign Fixes (applied 2026-07-15)

| Fix | Topic | Change | Risk |
|-----|-------|--------|------|
| 1 | Document Intake | Added text-paste detection (Len > 100 chars → route to Clinical Analysis directly). File upload preserved as fallback. | Low |
| 2 | Conversational boosting | Added elseActions with capability redirect when answer is blank. Added additionalInstructions for general knowledge fallback. | Low |
| 3 | Clinical Analysis | Replaced unconditional BeginDialog to Multi-Discipline Summary with ConditionGroup (only routes on multi-discipline keywords like "multi", "cross", "PT, OT, SLP"). | Low |
| 4 | Conversational boosting | additionalInstructions directive to use general knowledge when KB results are thin. | Low |

### Remaining Ceiling Factors
1. Clinical Analysis `applyModelKnowledgeSetting: false` + SearchSpecificFiles — intentional design for groundedness, but limits answer scope. Changing caused -11pp regression.
2. Missing knowledge domains (pharmacology, lab reference, imaging guidelines) — 24+ test questions on these topics have no KB coverage.
3. Platform limitations (details endpoint 404, stuck runs, auth gate can't be fully removed).

## MS Learn References
- Evaluation triage: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-failure
- Implementation checklist: https://learn.microsoft.com/microsoft-copilot-studio/guidance/implement-checklist
- Authentication config: https://learn.microsoft.com/microsoft-copilot-studio/configuration-end-user-authentication
- "If a topic uses authentication variables, they become Unknown variables when auth is turned off."
- Topic management: https://learn.microsoft.com/microsoft-copilot-studio/authoring-topic-management
- Generative orchestration: https://learn.microsoft.com/microsoft-copilot-studio/advanced-generative-actions

## Common Pitfalls
1. **Auth flip blocks publish** — `authenticationmode: 0` causes `ManualAuthenticationInputNotEnabled` on topics with SearchSpecificFiles or FileUpload. Revert to 2.
2. **Stuck eval runs** — InProgress 0/0 for >30min = platform flake. Cancel not supported (405). Wait for timeout (~90min). Completed stuck run scores ARE valid.
3. **Details endpoint 404** — Per-case `/details` returns 404 in some regions. Use aggregate from list endpoint.
4. **Publish cache** — `pac copilot publish` caches FAILED status. Verify with Dataverse `bots/{id}?$select=publishedon`.
5. **Line ending gotcha** — Dataverse botcomponents data uses `\r\n` NOT `\r\r\n`. Wrong endings cause silent PATCH failure.
6. **Wrong agent** — Therapy AI Dev has **three** case-history family bots: Reviewing Agent (`f19e1c40`, type-15 `cc349f24`), Case_History_Assistant (`aed96eb7`), Case Historian V2 (`ad635500`). Voice/UI nicknames ("case history assistant", "PCCH") often collide. Confirm `botid` + display name before PATCH. See `references/agent-identity-and-comparison.md`.
7. **Never change working topics** — Clinical Analysis was passing its matched cases. Changes caused -11pp regression.
8. **Token expiry kills background polls** — Python background pollers need built-in token refresh (HTTP 403 handler + refresh_eval_token.cjs).
9. **Char-budget rewrite without feature loss** — Instructions ≤7000 (prefer ~6000); Responses ≤500. Never drop extract list, discipline lenses, Timeline, citations/course-phase/follow-up, CMS/Jimmo, or safety to hit budget — compress wording only.
10. **User expects inject, not paste-only** — Inject instructions/`responseInstructions` via Dataverse + publish when possible. `responseInstructions:` inside type-15 `data` is the Generative AI Responses content.
11. **Structure list indent in live YAML** — Under `instructions: |-`, numbered report sections are stored with a leading 2-space indent. Exact string replace must match that indent or the patch finds nothing.
12. **Do not drop Timeline to "align" a draft** — If a user paste omits Timeline but earlier requirements asked for medical-course timing / easy scan chronology, keep Timeline and re-number. Default is keep Timeline.
13. **Align Responses after every structure edit** — After instructions section-list changes, re-PATCH `responseInstructions` the same turn and publish once.
14. **Inject when asked** — PATCH type-15 + publish; read-back Timeline + RI length (do not stop at paste-only).
15. **Pacific local times** — Convert UTC `publishedon` before reporting.
16. **Post-report cards kill SR eval on Fallback** — Never AdaptiveCardPrompt on Fallback/ConvBoost catch-all. Put cards in a dedicated topic; Fallback advertises trigger phrases only.
17. **`init:Global.X` once only** — Multiple topics with `init:Global.LastCaseHistoryReport` → `DuplicateVariableInitializer` publish fail. One `init:`; others assign without init, strings only.
18. **Global.Answer.Text is often already String** — Prefer `{Global.Answer.Text}` not `.Content` when platform says "'.' operator cannot be used on Text values".
19. **Concatenate without bad Text()** — `Text(Topic.SelectedDiscipline)` / `Text(System.Activity.Text)` can fail publish ("Text has some invalid arguments"). Use bare `Topic.SelectedDiscipline` + `System.Activity.Text` in `Concatenate(...)`.
20. **Do not Concatenate FullResponse records** into deep-dive prompts — type errors. Use conversation context + user message text.
21. **Regex slice after re.sub shifts offsets** — Replacing `Global.Answer` → `Global.Answer.Text` then slicing with pre-sub match positions truncated `FullResponse` → `FullRespon` (enum error). Recompute matches after every length-changing edit; prefer backup + append tail.
22. **Required Adaptive Card inputs need errorMessage** — `isRequired: true` without `errorMessage` → `AdaptiveCardInputIsRequiredMissingErrorMessage`.
23. **CA SendActivity is not optional for product features** — When adding post-report UX, always Send the report before card/BeginDialog; EndDialog alone can hide FullResponse.
