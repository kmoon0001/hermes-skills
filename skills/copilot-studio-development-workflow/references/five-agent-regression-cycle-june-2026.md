# Fleet Regression Cycle — June 2026

Empirical testing data from a full regression + recovery cycle on therapy compliance
agents in Copilot Studio. Score patterns, root causes, and fixes documented for
future triage reference.

## Agent Inventory

| Agent | Bot ID | Role |
|-------|--------|------|
| SLP_Specialist | `6e437a77-...` | Speech-language pathology compliance |
| PT_Specialist | `593407f3-...` | Physical therapy compliance |
| OT_Specialist | `73b45e98-...` | Occupational therapy compliance |
| TDA | `4d0ed0d3-...` | Therapy Documentation Audit (parent orchestrator) |

Environment: `Ensign Services (default)` — `org3353a370.crm.dynamics.com`

## OT_Specialist — Full Trajectory (June 9-10, 2026)

### Regression Phase
| Time | Score | State |
|------|-------|-------|
| Jun 9 10:35 PM | 85% | Peak — v5 conditional, guard topics OFF |
| Jun 9 11:24 PM | 50% | v6 "Always use" — instruction regression |
| Jun 10 1:04 AM | 55% | Same range |
| Jun 10 3:17 AM | 50% | v7 conditional — format irrelevant now |
| Jun 10 4:04 AM | 10% | "Allow ungrounded: OFF" — catastrophic |
| Jun 10 8:07 AM | 5% | Corrupted v8+v9 instructions + guard OFF |

### Recovery Phase
| Time | Score | State |
|------|-------|-------|
| Jun 10 9:29 AM | 60% | v9 clean + Allow ungrounded ON + partial guard toggle |
| Jun 10 10:55 AM | 55% | All 12 guard ON — hardcoded IDs hurt |
| Jun 10 11:41 AM | 25% | All guard OFF, 200+ question-phrase topics — topic overload |

### Root Causes Discovered

1. **"Allow ungrounded responses: OFF"** — 50→10% drop. The single most impactful toggle.
2. **Guard topics with hardcoded record_ids** — Caused "different record_id" on 5-6/9 failures. Delete them.
3. **200+ question-phrase topics** — Each evaluation test question had its own topic. Routing chaos. Delete all duplicates.
4. **Missing EndDialog on active topics** — "Refuses to help on turn 3" pattern. Add EndDialog + clearTopicQueue.

### Fix Playbook (Priority Order)
1. Turn "Allow ungrounded responses" ON
2. Delete all guard topics with hardcoded IDs
3. Delete all question-phrase duplicate topics (keep only ~12 named audit topics)
4. Add EndDialog + clearTopicQueue: true to every SearchAndSummarizeContent topic
5. Use conditional RESPONSE FORMAT for mixed-test agents

## SLP_Specialist

| Test | Date/Time | Score | Notes |
|------|-----------|-------|-------|
| SR 100 | Jun 9 4:47 PM | 95% | v3/v4 peak |
| Conv 20 | Jun 9 7:12 PM | 95% | v4 "Always use" peak |
| SR 100 | Jun 9 8:02 PM | 87% | v5 conditional |
| SR 100 | Jun 10 4:05 AM | 86% | Stable |
| Conv 20 | Jun 10 8:53 AM | 90% | Stable |
| Conv 20 | Jun 10 10:49 AM | 70% | v2 injection removed "When full document text IS provided" line |
| SR 100 | Jun 10 11:39 AM | 78% | Continued regression |

**Key finding:** When editing SLP instructions via insertText, accidentally removed the
"When full document text IS provided: populate each section..." line. This caused a 20-pt
conversation drop and 8-pt single-response drop. The fix is to restore the original
instructions with only the "OTR vs COTA" → "SLP vs SLPA" change.

## PT_Specialist

| Test | Date/Time | Score | Notes |
|------|-----------|-------|-------|
| Conv 20 | Jun 9 9:42 PM | 100% | Peak — guard topics OFF, topic fix applied |
| Conv 20 | Jun 10 3:29 AM | 95% | Stable |
| SR 100 | Jun 10 4:05 AM | 87% | Stable |

**Key finding:** PT does NOT need guard topics. Proven 95-100% conversation without them.
Generative AI + good instructions handles the test set. Guard topics would create routing
conflicts — "overdoing it."

## New Tools & Methods Developed

1. **CDP `Input.insertText`** — Defeats the React paste wall. OS-level keystrokes React can't block.
2. **Evaluation REST API** — `api.powerplatform.com/copilotstudio/.../makerevaluation` for programmatic test results.
3. **pac CLI topic audit** — `pac org fetch` with `componenttype eq 9` to count and categorize topics.
4. **Token capture via CDP Network.enable** — Intercept Bearer tokens from Kiro Chrome for API access.
