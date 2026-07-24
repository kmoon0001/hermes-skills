# Fleet-Wide 4-Phase Sweep Pattern

Use this pattern when the user asks to debug, fix, or evaluate ALL agents in a Copilot Studio environment — not just one.

## Overview

```
Phase 0: ANALYSIS (parallel subagents)
  ↓
Phase 1: FIX (systemic bulk, worst-first)
  ↓
Phase 2: QA (verify, YAML validate, regressions)
  ↓
Phase 3: EVAL (CDP token capture → PPAPI → SPA scores)
  ↓
Loop back to Phase 1 if scores <95%
```

## Phase 0 — Fleet-Wide Analysis

1. Load all relevant skills (copilot-debug, copilot-studio-pipeline, therapy-fleet-agent-audit, agent-state-dumper)
2. Use delegate_task with tasks[] array to analyze 3-4 agents per subagent in parallel
3. Each analysis subagent reads ALL local topic YAMLs + agent.mcs.yml + settings
4. Check per topic: EndDialog+clearTopicQueue, ConditionGroup+Question, SearchSpecificFiles/SearchSpecificKnowledgeSources, trigger phrase count (5-10), boilerplate comments
5. Check instructions: size (<6K chars), contradictions, unconditional RESPONSE FORMAT, 800-char caps, no-caveat block, eval-safe section
6. Output P0 count (blocks eval) and P1 count (quality)
7. Write individual analysis-<agent-name>.md reports to audit-results/

## Phase 1 — Priority-Ordered Fix

1. Compile priority queue ordered by P0 count (most P0 first)
2. Dispatch fix subagents worst-first using delegate_task
3. Apply systemic bulk fixes per agent:
   - Backup files with .bak
   - Add EndDialog with clearTopicQueue: true to ALL custom topics
   - Remove SearchSpecificFiles/SearchSpecificKnowledgeSources blocks
   - Strip old "Microsoft Learn Platinum Standard" boilerplate comments
   - Add EVAL NO-CAVEAT STANDARDS CHECK + EVALUATION-SAFE ORCHESTRATION sections to agent.mcs.yml
   - Fix unconditional RESPONSE FORMAT (make conditional or remove)
   - Remove 800-char hard caps
   - Validate all YAML with js-yaml
4. Each fix subagent writes a report to audit-results/<agent>-loop1-fixes.md

## Phase 2 — QA Verification

1. Dispatch QA subagents per agent (can run in parallel with fixes)
2. Verify actual file contents vs .bak originals (no unintended changes)
3. Run js-yaml on ALL .mcs.yml files in workspace
4. Spot-check 5 random topics for EndDialog+clearTopicQueue
5. Check agent.mcs.yml has both eval sections
6. Check for regressions in unmodified files (YAML still parses, routing intact)
7. Assert qa-pass: true/false

## Phase 3 — Eval Score Validation

1. Launch Edge/Chrome with `--remote-debugging-port=9223`
2. Navigate to agent's evaluation page in Copilot Studio
3. Capture PPAPI Bearer token via CDP WebSocket:
   - Connect to `http://127.0.0.1:9223/json/list`
   - Find eval tab by URL containing `copilotstudio` + `evaluation`
   - Use `Fetch.enable` interception on request headers
   - Reload page to trigger PPAPI calls
   - Extract Authorization header from powerplatform.com requests
   - Save to `%USERPROFILE%\.copilot-studio-cli\test-agent-token.txt`
4. List test sets: `GET /makerevaluation/testsets` with Bearer token
5. Start draft eval run: `POST /testsets/{id}/run` with `{"runOnPublishedBot": false}`
6. Poll: `GET /testruns?$top=3&$orderby=startTime desc`
7. When Completed, read SPA page text via CDP `Runtime.evaluate` for score percentage
8. Report SR% + Conv%
9. If <95%, identify remaining patterns from failure reasons, loop back to Phase 1

## Priority Queue Template

```
## Fleet Priority Queue

| Rank | Agent | Bot ID | P0 | P1 | Status |
|:----:|-------|--------|:--:|:--:|:------|
| 1 | Worst Agent | `guid` | ~73 | 4 | 🔴 QUEUED |
| 2 | ... | ... | ... | ... | ... |
```

## Key Rules

- **Live UI is source of truth**, not local copies. Cross-reference Dataverse when files differ.
- **delegate_task max 3 concurrent** — batch analysis to 3 agents per subagent
- **SR and Conv must be sequential per agent** (one active run at a time), but DIFFERENT agents can run simultaneous evals
- **Token expires ~1 hour** — recapture via CDP when expired
- **PPAPI detail endpoint may 404** — fall back to SPA page text extraction for scores
- **Write audit-results/** reports to `pipeline/audit-results/` for persistence across sessions
