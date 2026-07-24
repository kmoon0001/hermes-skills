---
name: copilot-studio-qm-coach-v2
description: "Agent-specific rules for Pacific Coast QM Coach V2 (formerly SimpleLTC) — bot IDs, live inventory after 2026-07-17 Pattern L fix, eval set IDs. Use with agent-audit-protocol / eval-optimization-loop. Live Dataverse is source of truth."
version: 2.0.0
tags: [copilot-studio, qm-coach, therapy-agents, pacific-coast]
---

# Pacific Coast QM Coach V2 — Agent Rules

**Live identity:** Pacific Coast QM Coach V2 (not SimpleLTC / TheraDoc).  
**Authoritative surface:** Dataverse Web API `data` field (new-experience). Local D: `topic_templates/` and Jul 3 inventory are **stale** — do not treat as live.

## Key IDs

| Field | Value |
|-------|-------|
| Bot ID | `ea52ad9c-8233-f111-88b3-6045bd09a824` |
| Environment | `a944fdf0-0d2e-e14d-8a73-0f5ffae23315` (Therapy AI Agents Dev) |
| Dataverse | `https://orgbd048f00.crm.dynamics.com/` |
| Tenant | `03cc92c3-986c-4cf4-ae27-1478cf99d17f` |
| Instructions (ct=15) | `d45208e6-066f-4e9c-9a8f-18f7051108d0` |
| Fallback | `83492644-9856-f111-bec6-7ced8d3b6116` |

## Live topics (post-fix 2026-07-17)

**Pattern L SASC leaves** (FullResponse + `variable: Topic.Answer` + SendActivity + EndDialog clearTopicQueue):
- DoR Summary, FacilityTrendReporter, QM Action Plan, QM Data Upload & Decline Detection, QM Driver Analysis, Resident Outlier Analysis

**Other custom:** Escalate QM Concern, HIPAA Guardrail, SNF Clinical Intake Handoff Router  
**System:** Conversation Start (welcome + EndDialog), Fallback (SASC + capability list), On Error (no broken CrossAgentAuditLog invoke)

## Fixed 2026-07-17 — do not re-open as P0

| Was | Now |
|-----|-----|
| Instructions splice `analy##` + dup `##` sections | Clean rewrite, Pacific Coast identity |
| No markdown / under 4 sentences | Conditional format + EVALUATION CONTEXT |
| Fallback apology-only | SASC FullResponse + capability list |
| SASC missing FullResponse / no SendActivity | Full Pattern L on 6 leaves |
| Empty Ch15/AAPACN KB descriptions | Filled + isOfficial |
| SimpleLTC/TheraDoc in On Error/settings | Scrubbed |
| Duplicate Bot Files | Disabled non-canonical twins |
| Missing CrossAgentAuditLog action | Invoke removed |

**Repo artifacts:** `Pacific-Coast-Therapy-Hub/QMCOACH_AUDIT_REPORT.md`, `QMCOACH_FIX_PASS_2026-07-17.md`, `scripts/fix_qmcoach_v2.py`  
**Recipe:** `agent-audit-protocol` → `references/qm-coach-v2-new-exp-audit-fix-2026-07-17.md`

## Eval sets

- **SR SingleTurn 100 (prefer):** `0feaa8bf-d167-419e-92f5-d89bc4e93256` — "Evaluate Pacific Coast QM Coach V2"
- **Conv MultiTurn 20:** multiple still titled SimpleLTC — any 20-case MultiTurn OK; note name contamination

Foreign test-set titles (Compliance Analyzer / SimpleLTC) are P1 hygiene, not runtime identity.

## Baseline night 2026-07-17 (post Pattern L publish)
| Metric | Result |
|--------|--------|
| Conv avg (2×) | **94.8%** (100% + 89.5%) |
| SR avg (2×) | **94.5%** (94% + 95%) |
| Near 95% target | Fine-tune remaining fails; do not rebuild |

Runs/logs: `Pacific-Coast-Therapy-Hub/eval_baselines_tonight/BASELINE_REPORT.md`

## Domain rules

- Mission: facility QM coaching (trends, declines, drivers, 7-30-90, DoR, outliers) — not direct care / raw PHI
- Aggregate facility data preferred; record_id pointers only
- Conditional structure for audits; natural short answers for trivia
- End clinical outputs: Clinical review required

## Tier 1 live-ready WITHOUT SimpleLTC / Power BI / login redesign (2026-07-17)

When Kevin wants "as close to live as possible" **without** those integrations and without more agent rewrites:

| Gate | Status |
|------|--------|
| Publish | Succeeded; Provisioned / Synchronized |
| Channels | **Teams** + **Microsoft 365 Copilot** synchronized |
| Auth | Integrated (mode 2); app registration in tenant |
| Brain | Pattern L leaves + Fallback SASC; ~94.5% SR / ~94.8% Conv |

**Tier 1 mode:** paste facility QM rates/export snippets → coach. No auto SimpleLTC, no PBI in-chat.

**Remaining is distribution only:** pilot security group, Teams pin, paste SOP. Do **not** block pilot on SimpleLTC API, Power BI connector, or Dashboard auto-handoff.

**Go-live pack (no agent edits):** `Pacific-Coast-Therapy-Hub/QMCOACH_LIVE_READY_NO_INTEGRATIONS.md`  
**Class recipe:** `agent-audit-protocol` → `references/live-ready-without-integrations.md`

## Future change workflow

1. Web API `_parentbotid_value eq <botId>` — audit/PATCH **`data`**, not `content`
2. Commit only QM Coach audit/fix artifacts on dirty multi-agent repos
3. CRLF-normalize → PATCH → re-GET verify
4. Publish → verify `publishedon` + `lastFinishedPublishOperation.status` (Pacific); ignore stale pac CLI dates
5. Shift+Reload CS tab; 2× Conv + 2× SR baselines via `eval-optimization-loop`
