---
name: copilot-studio-preflight
description: Run a soft preflight gate BEFORE any Hermes action that touches a Microsoft Copilot Studio agent (PATCH topic, edit instructions, change KB, publish, start eval). Validates against MS Learn docs, local skills, downloaded GitHub repos, eval failure history, and the additive-only rule. WARN + explain — never hard-block except destructive ops. Use this skill before every mutating Copilot Studio call to catch unsound prompts/actions before they reach the LLM or the agent.
---

# Copilot Studio Preflight Gate

A soft execution gate that runs BEFORE any action that mutates a Copilot Studio agent.
It checks the planned prompt/action against authoritative sources and returns GO /
WARN / BLOCK. On WARN, explain and proceed (per user preference: warn + explain, not hard-block).
On BLOCK, only for destructive ops (delete/unpublish/overwrite-prod/remove-capability).

## Hard constraint (NEVER violate)
- ADDITIVE-ONLY: do not remove or downgrade any existing agent capability, topic, flow, KB, or
  response path. All fixes must add alongside, never delete. If a change looks like it removes
  something, BLOCK and ask the user.

## Prerequisite: Run Comprehensive Inspection First

Before running this preflight gate, you MUST have loaded and run `agent-comprehensive-inspection` first. The preflight gate validates changes AGAINST the inspection findings. Running preflight without inspection first risks missing structural issues that the gate doesn't re-check.

## When to run preflight

Run it BEFORE any of these mutating actions:
- PATCH a topic (botcomponents data field) — check YAML validity, SendActivity/EndDialog presence,
  responseCaptureType, unquoted-colon YAML crashes, trigger-phrase overlap. **CRITICAL: check SASC node isn't empty (must have userInput + fileSearchDataSource/customDataSource).** **CRITICAL: Dataverse data uses \\r\\n line endings.** If using Python str.replace(), convert with `.replace("\\r\\n", "\\n")` first, then back.
- PATCH instructions (componenttype 15) — GATE FIRST: confirm the component's `_parentbotid_value`
  equals the target bot. Then check for harmful restrictions ("No headers", "under N
  sentences", "no tables"), length < ~6000 chars, DIRECT ANSWER pattern present. **Check model name:** `modelNameHint: GPT55Chat` is a known typo (should be `GPT5Chat`). Also check for `Sonnet35` vs `Sonnet46` etc.
  Watch for INTERNAL CONTRADICTIONS (e.g. one line says "provide review framework" while another forbids "framework").
- Add/rename/mark KB (componenttype 14) — check source is authoritative.
- pac copilot publish — require a checkpoint first; warn if last eval < 95%.
- Start eval (makerevaluations POST) — warn if already InProgress.

Do NOT preflight read-only calls (GET topic, poll eval, read instructions).
Run it before ANY of these mutating actions:
- PATCH a topic (botcomponents data field) — check YAML validity, SendActivity/EndDialog presence,
  responseCaptureType, unquoted-colon YAML crashes, trigger-phrase overlap, **empty SASC node**
- PATCH instructions (componenttype 15) — GATE FIRST: confirm the component's `_parentbotid_value`
  equals the target bot (filter `_parentbotid_value eq <botguid> and componenttype eq 15`; a bare
  `botid` filter returns 400). Then check for harmful restrictions ("No headers", "under N
  sentences", "no tables"), length < ~6000 chars, DIRECT ANSWER pattern present, **model name typo (GPT55Chat, Sonnet35)**. Watch for INTERNAL
  CONTRADICTIONS (e.g. one line says "provide review framework" while another forbids the word
  "framework" — that contradiction is itself an abstention trigger).
- Add/rename/mark KB (componenttype 14) — check source is authoritative (CMS/AHRQ/ASHA/APTA/AOTA),
  name has no ".pdf", marked Official where appropriate
- pac copilot publish — require a checkpoint (backup) first; warn if last eval < 95%.
  SYNTAX: `pac copilot publish --environment https://<org>.crm.dynamics.com --bot <botguid>`.
  The `--environment` flag needs the full URL or GUID (short org name like `orgbd048f00` is rejected);
  `--bot <guid>` is required (no default).
- Start eval (makerevaluations POST) — warn if a run is already InProgress; confirm test set exists

Do NOT preflight read-only calls (GET topic, poll eval, read instructions). Those are safe.

## 5-step procedure
1. PARSE — extract intent + target component + the exact change (old→new string or new YAML).
2. RETRIEVE — gather from:
   - mcp__microsoft_learn (search docs for the exact node/kind/field)
   - skill_view on matching copilot-studio-* skill (topic-yaml-fixes, agent-instructions,
     add-knowledge, run-eval, validate, agent-comprehensive-inspection)
   - local cloned GitHub repos under D:/my agents copilot studio/ (pattern reference)
   - eval_history.jsonl failure signatures (does this change match a past failure mode?)
3. VALIDATE — check:
   - Schema/field correct per MS Learn (e.g. SendActivity before EndDialog; responseCaptureType:
     FullResponse for SASC answer topics; no unquoted colon in YAML activity lines)
   - Source authoritative (KB from CMS/AHRQ/ASHA/APTA/AOTA — not random web)
   - Matches skill prescription (topic-yaml-fixes, agent-instructions)
   - Additive-only (nothing removed/downgraded)
   - Eval risk (does it touch a known grader-ceiling area: abstention wording, upload-no-text)
4. VERDICT — GO / WARN(reasons) / BLOCK(reasons, destructive only)
5. PROCEED — on GO or WARN, run the action. On BLOCK, stop and ask user.

## Output format (always show user)
  PREFLIGHT: <target> — <GO|WARN|BLOCK>
  - Check: <what was verified>
  - Source: <MS Learn url / skill / repo / eval_history entry>
  - Note: <explanation if WARN/BLOCK>

## MS Learn facts confirmed (use as gates)
- Topics are AdaptiveDialog YAML; node kinds: Question, ConditionGroup, SendActivity, EndDialog,
  SearchAndSummarizeContent. (learn.microsoft.com/microsoft-copilot-studio/visual-studio-code-extension-edit-agent-components)
- SendActivity sends the message; EndDialog ends the topic. A topic that answers should have
  SendActivity before EndDialog, else raw Power Fx / no output.
- responseCaptureType: FullResponse required on topics whose final node is SearchAndSummarizeContent
  answer output, or the answer is truncated.
- Evaluation "General quality" scores on 4 criteria (Relevance, Groundedness, Completeness,
  Abstention); failing ANY one fails the case. (analytics-agent-evaluation-overview)
- Reducing KB count is NOT guaranteed to improve grading. (do not delete KBs to "reduce noise")
- Prompt Advisor scores prompt confidence 0-100; rubrics refine grading to domain standards.

## Pitfalls (from PCCH history)
- Unquoted colon in `activity: text: more` breaks YAML parse → Fallback topic crash.
- Instructions "No headers or markdown" + "under 4 sentences" caused 54% eval crash.
- Response starting with "framework/DRAFT/checklist/structure" reads as ABSTENTION to grader.
- INTERNAL CONTRADICTION in instructions is an abstention trigger too: PCCH line 28 said
  "provide review framework" while line 36 forbade the word "framework". Remove the contradiction
  by rewording the trigger line (additive reword, not deletion) — this targeted 5 abstention fails.
  Scan for any "do X" vs "do NOT use word/phrase X" pairs before patching.
- Upload-no-text test cases fail Completeness because agent asks instead of answering.
- pac publish reruns validation each call; "Failed [timestamp]" is last result, not cache.
- Never put API keys/tokens in YAML or chat — use [REDACTED].
- VALIDATED END-TO-END (PCCH 2026-07-12): soft WARN preflight → PATCH instructions (reword the
  contradiction line) → `pac copilot publish` → headless SR re-run via `powervamg` gateway. The
  reword was additive and safe but did NOT by itself lift SR (80% vs prior 83% — grader-instance
  variance, see evaluation-rest-api). Lesson: abstention-reword alone is necessary-but-not-sufficient
  for 95%; pair with KB/test-set work (S2/S4/S3 in copilot-studio-eval-loop). When re-reading the
  re-run result, read `aggregatedGraderResults`, never `testResults` (empty on this gateway).

## Verification after action
After the mutating call, re-read the component (GET) to confirm the change landed, then note it in
eval_history.jsonl with the preflight verdict.
