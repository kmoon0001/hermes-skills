---
name: agent-optimizer
description: Eval-driven optimization loop for a Copilot Studio agent — adapted from Kiro's copilot-agent-optimization steering into the Hermes harness. Use when improving an agent's evaluation pass rate, fixing eval failures, or hardening topics. Bakes in pac auth (not az), the editor-render gate (prevents the file[] freeze), live-UI verification, and the File+Text dual-input rule. Pair with agent-builder for net-new work.
---

# agent-optimizer (Hermes-adapted, from Kiro)

Iteratively improve a Copilot Studio agent's quality (eval pass rate, conversation
quality, compliance) by: read live state → diagnose → plan → fix → deploy → verify.
This is the IMPROVE path. For greenfield builds use `agent-builder`.

## When to use
- "Optimize <agent>" / "Get <agent> to 95%"
- "Fix the eval failures on <agent>"
- "Harden the <topic> topic"
- Post-eval remediation

## Rebuild vs Optimize Decision Tree
Before starting optimization, determine whether the agent CAN be optimized or NEEDS a full rebuild (use `agent-builder-orchestrator` instead):

### OPTIMIZE (surgical fixes) when:
- Agent has a **sound architecture** (clear intent boundaries, Card-based or SASC-based flow, no structural anti-patterns)
- Issues are **identifiable and fixable**: missing `responseCaptureType`, `SearchSpecificFiles`, `FilePrebuiltEntity`, "under 4 sentences", variable scope mismatches, missing `clearTopicQueue`
- **clearTopicQueue rate > 80%** on EndDialogs
- **No SearchSpecificFiles** or SearchSpecificKnowledgeSources (or only 1-2)
- Fewer than 5 P0 structural issues
- Agent has a **clear purpose and good instructions** (just needs refinement)
- **Baseline eval > 20%** — agents below 20% likely have deeper issues

Examples from this session: Case History Reviewing Agent (24-36% baseline → 43% after 6 surgical fixes), TheraDoc Workbench (45 topics, all structural — just needed responseCaptureType and variable scope fixes).

### REBUILD (use agent-builder-orchestrator) when:
- **Structured-Intake-Only anti-pattern**: 85+ Question nodes, 0 AdaptiveCards, users must type everything
- **clearTopicQueue rate < 40%** — systemic structural rot
- Agent has **severe live/local drift** (overlapping topics, orphan nodes, corrupted YAML)
- **Architecture is fundamentally wrong**: too many topics (>15 for a simple agent), wrong patterns (pure Question-flow for what should be SASC), no routing logic
- **Scoring < 20%** with no clear single fix — the agent is failing everywhere, not in identifiable patterns
- **Missing primary directive**: agent instructions don't define what it IS and IS NOT
- User says "redo it like [working agent]" or "fill this agent"

### The Two-Round Rule
Always start with Round 1 (surface-level fixes): responseCaptureType, variable scope, SearchSpecific restrictions, model name typos, unconditional format bans, FilePrebuiltEntity. Then re-evaluate. If Round 1 improves scores by <10pp, the remaining issues are architectural — switch to rebuild. If Round 1 improves by 10pp+, continue optimizing into Round 2 (instructions conditioning, KB optimization, flow validation).

## Hard rules (non-negotiable)
1. **Auth = `pac` not `az`.** See copilot-studio-common-reference §Auth Patterns.
2. **Never ship `inputType: file[]` / `turn.uploadedFiles`** — breaks editor.
   Use File+Text dual-input (copilot-studio-common-reference §File+Text Dual-Input Pattern).
3. **Commit before change.** git backup before any PATCH.
4. **Live UI = source of truth.** Run editor-render gate after deploy
   (copilot-studio-common-reference §Editor-Render Gate).
5. **Additive only** unless approved.

## Optimization loop (repeat until gate met)

### 1. Pull live state (read-only, `pac`)
```
pac auth create --environment https://pccapackage.crm.dynamics.com/
pac copilot list                       # get bot GUID
# FetchXML to query.xml:
#   <fetch><entity name="botcomponent"><attribute name="data"/>
#     <filter><condition attribute="botcomponentid" operator="eq" value="<topicId>"/></filter></entity></fetch>
pac org fetch -xf query.xml > live_topic.xml
```
Parse the returned YAML. Confirm current structure (no file[] surprises).

### 2. Run / read evals
- If a test set exists: `pac`/UI eval run, or load `copilot-studio-run-eval`.
- Triage failures with `eval-triage-framework` (SHIP / ITERATE / BLOCK).
- Prioritize: security/compliance → config → KB → topics → flows → instructions.

### 3. Plan the fix (systemic, not one-off)
Apply Kiro's optimization standards where relevant:
- **Instructions format:** markdown `#` headers, `-` bullets, `**bold**` for rules;
  structure Constraints → Response Format → Guidance; <8000 chars; role identity
  first line; explicit "out" paths for ambiguous input.
- **Knowledge:** SharePoint folders > file uploads; every source has a detailed
  description ("Use this source for [X]. Reference when [Y]."); Official toggle on
  gov/standards; DO NOT use `SearchSpecificFiles` (restricts retrieval → cite failures);
  DO NOT use `knowledgeSources: kind: SearchAllKnowledgeSources` (invalid field).
- **Settings (healthcare):** Content Moderation = Medium (High false-positives on
  clinical language); Model Knowledge ON; Semantic Search ON; File Analysis ON;
  Latency Messages OFF (confuses the grader).
- **Topics:** ≥5 trigger phrases; OnError handler; Adaptive Card buttons for bounded
  choices; no duplicate triggers; classify-and-route intake topic.
- **Adaptive Cards:** schema 1.5, single-column, unique `actionSubmitId` per button,
  no PHI in JSON.

### 4. Fix (edit YAML, commit, deploy) — Iterative publish pattern
- Fix the highest-impact issues first (missing dialogs, Power Fx errors, variable scope).
- **Publish after each round** — some errors mask others. Fix one layer, publish, see the NEW error set emerge.
- Common masking sequence in card-based agents: `AuditExistingNote` → `ComplianceAuditV2` not found → `Topic.Answer`/`Global.Answer` mismatch → `OutputType`/`errorMessage` → Output binding errors → `InfiniteLoopInBotContent`. Each layer must be resolved before the next becomes visible. See `copilot-studio-common-reference §references/managed-flow-publish-blocker.md`.
- **SASC variable scope is the #1 blocker after structural fixes.** Every SASC node needs a `variable:` field matching the SendActivity reference. If SASC writes to `variable: Global.Answer`, SendActivity must read `{Global.Answer}` — NOT `{Topic.Answer}`. Mismatch causes 19+ publish errors. Fix: add `variable: Topic.Answer` at the CORRECT indent (same as responseCaptureType, not nested under it).
- **Managed flow detection** (see G14 in agent-qa-gate). Before final publish round, run orphan flow detection. Managed flows in solutions block publish with Output binding + InfiniteLoopInBotContent errors. Can't delete via API — need Power Platform admin.
- **Publish cache reset** (see managed-flow-publish-blocker.md). If `pac copilot publish` shows `Failed []` with empty diagnostics, sync status is stale. Reset via PATCH `bots({id})/synchronizationstatus`.
- Edit local YAML (from step 1 backup).
- `git commit` the plan.
- PATCH live `data`. NEVER file[].
- `pac copilot publish --bot <guid> --environment https://pccapackage.crm.dynamics.com/`
- Verify `synchronizationstatus.lastFinishedPublishOperation.status == "Succeeded"`.

### 5. EDITOR-RENDER GATE (prevents freeze)
See copilot-studio-common-reference §Editor-Render Gate. Do NOT skip.

### 6. Re-evaluate
Re-run eval / re-send test scenarios. Loop until ≥93% (fleet gate) or the user's
target. Stop when marginal gains < effort (tell the user).

## Deliverables per loop
- git commit of the fix.
- publish status (real, from synchronizationstatus).
- editor-render confirmation (canvas not blank).
- before/after eval numbers.

## Pitfalls (real incidents)
Common pitfalls: copilot-studio-common-reference §Common Pitfalls.
- **`file[]` → blank canvas freeze.** Dual-input instead.
- **`az` 401 → `pac auth create`.**
- **`pac copilot list` stale** → check synchronizationstatus.
- **Latency Messages ON** → grader confusion → lower scores. Turn OFF.
- **Content Moderation High** → clinical-language false positives. Use Medium.
- **SASC variable scope mismatch** — Topic.Answer vs Global.Answer. #1 blocker after structural fixes on multi-SASC agents. Every SASC node must output to the variable the next step reads from. Fix: add `variable: Topic.Answer` at correct indent level.
- **Managed flow blocks publish silently** — flow in managed solution can't be deleted via API. Publish fails with Output binding errors + InfiniteLoopInBotContent. Detection: query workflows table for `ismanaged=True`. Fix: Power Platform admin removes flow from parent solution.
- **Publish cache never cleared** — `pac copilot publish` returns `Failed []` but actual publish succeeded. Reset sync status via API PATCH. See common-reference §references/managed-flow-publish-blocker.md.

## Relationship to Full Pipeline
`agent-optimizer` is for **quick optimization iterations** on existing agents (read → diagnose → fix → verify). For a **full end-to-end rebuild or new build** (requirements → all topics → QA gate → deploy → test → iterate), load `agent-builder-orchestrator` instead — it chains architect → crafter → QA gate → deploy → eval in one shot.

## References
- Kiro source: `.codex/worktrees/3170/my agents copilot studio/.kiro/steering/copilot-agent-optimization.md`
- Common Knowledge Graph: `C:/Users/kevin/.kiro/memory/memory.jsonl` (shared Hermes ↔ Kiro via MCP)
- `eval-optimization-loop` — detailed eval runner (launch, poll, analyze, fix)
- `eval-triage-framework` — SHIP/ITERATE/BLOCK failure triage
- `agent-qa-gate` — 18-gate verification (run BEFORE deploy after optimization)
- `agent-builder` — for net-new topics alongside optimization
- `agent-builder-orchestrator` — full end-to-end pipeline (for complete rebuild scenarios)
