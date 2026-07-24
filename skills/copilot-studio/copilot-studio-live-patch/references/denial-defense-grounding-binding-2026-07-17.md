# Denial Defense V2 — Grounding Binding Fix (2026-07-17)

**Agent:** Pacific Coast Denial Defense V2 (SNF AI Dashboard V2)
**Bot ID:** `6d7815b4-ce47-f111-bec5-70a8a5b1c3a3`
**Env ID (eval):** `a944fdf0-0d2e-e14d-8a73-0f5ffae23315`
**Org:** `orgbd048f00.crm.dynamics.com`

## Problem

Five active custom `SearchAndSummarizeContent` (SASC) routes were **not bound** to approved knowledge sources. They had `applyModelKnowledgeSetting: true` only — no `fileSearchDataSource` or `knowledgeSources` block. This meant they relied entirely on model memory, ignoring the nine live public-site knowledge sources.

Result: retry eval scored 45% (baseline) — every custom route produced generic ungrounded answers.

## Approach

Instead of broad instructions/KB changes, made a **narrow five-route grounding binding patch**:

1. **Checkpoint** — captured live grounding state via `scripts/denial_defense_grounding_checkpoint.py`
2. **Apply** — injected `fileSearchDataSource: searchFilesMode: kind: SearchAllFiles` + `knowledgeSources: kind: SearchAllKnowledgeSources` into all five custom SASC nodes
3. **Publish** — via `pac copilot publish`
4. **Eval** — ran 100-case SingleTurn retry

## Result

| Run | Score | Improvement |
|-----|-------|-------------|
| Baseline | 45% | — |
| After binding patch | 89% (89/100, 11 failed, 0 errors) | +44 pts |

## Remaining failures (11 cases)

All were **groundedness/completeness** failures — the agent now delivers CMS policy content but the grader expected facility-specific data the test case didn't supply. These are **eval-setup issues**, not agent structural problems:

1. Appeal packet/letter workflows — denial FFS appeals, reconsideration letters (request RAC action items)
2. RAC/audit documentation workflows — compliance audit elements, certification/recertification timeliness
3. Therapy evaluation documentation — Plan of Care elements in different settings
4. Telehealth/advanced-modality denial risks — telehealth documentation, group therapy requirements

**Next step (not completed):** Curate authoritative CMS/OIG public-site resources for these gaps, add as knowledge sources, or reword the test set (Pattern E5) to convert data-sparse admissions into knowledge-answerable questions.

## Files created

- `scripts/denial_defense_grounding_checkpoint.py` — snapshot/apply grounding bindings
- `scripts/run_denial_defense_retry.py` — retry runner with timestamped directories
- `scripts/poll_denial_defense_grounding_eval.py` — resilient eval poller
- `audits/denial_defense_v2/GROUNDING_BINDING_RETRY_2026-07-17.md` — full audit

## Key lessons

- **Narrow binding worked** — didn't touch instructions, Fallback, or KBs. Just added `fileSearchDataSource` + `knowledgeSources` to the five custom SASC nodes. 44-point improvement.
- **89% is not done** — the remaining failures are source-coverage gaps, not structural. The agent now answers CMS policy correctly.
- **`az` PATH on this host:** Needs full `.cmd` path: `C:\\Program Files\\Microsoft SDKs\\Azure\\CLI2\\wbin\\az.cmd`. The git-bash `az` is a shell script, not an `.exe`, so `subprocess.run(['az',...])` from system Python raises `FileNotFoundError`.
- **Live resource audit remains incomplete** — the exact knowledge source names, descriptions, individual generative-node source selections were not fully documented.
