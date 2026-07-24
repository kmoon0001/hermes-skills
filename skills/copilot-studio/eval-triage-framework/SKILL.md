---
name: eval-triage-framework
description: Microsoft's formal eval triage framework — root cause diagnosis, remediation mapping, and SHIP/ITERATE/BLOCK verdicts for Copilot Studio agent evaluations. Use when interpreting eval results or debugging failing test cases.
---

# Eval Triage & Improvement Framework

Source: microsoft/eval-guide (eval-triage-and-improvement skill + eval-result-interpreter skill)

## Triage Decision Tree

For each failing test case, work through in order:

1. **Is the agent's response actually acceptable, even though it failed?**
   → YES = **Eval-setup problem** (grader, expected value, rubric, or method is wrong)

2. **Is the expected answer still current against the actual source/ground truth?**
   → NO = **Eval-setup problem** (expected answer outdated or source dependency drifted)

3. **Does the test case represent a realistic user input for this eval set?**
   → NO = **Eval-setup problem** (unrealistic or mis-scoped test case)

4. **Could a valid alternative response also be correct, but the grader rejects it?**
   → YES = **Eval-setup problem** (rubric/grader too rigid)

5. **Is the eval method appropriate for what you're testing?**
   → NO = **Eval-setup problem** (wrong method)

**ALL PASS** → Classify as **agent-quality problem**:

6. **Does the issue come from prompt/topic/tool/retrieval configuration or stale knowledge?**
   → YES = **Agent Configuration / Knowledge Issue** (agent-quality problem)

7. **Does the behavior persist after reasonable config/knowledge fixes plus re-run?**
   → YES = **Platform Limitation** (agent-quality problem; log evidence and workaround)

## Two Root Buckets

| Root bucket | Operational subtype | Who acts | What it means |
|------------|-------------------|----------|---------------|
| **Eval-setup problem** | Eval setup issue | Eval author | Response is acceptable or eval metadata/rubric/expected answer/method is wrong |
| **Agent-quality problem** | Agent configuration issue | Agent builder | Agent genuinely produced bad response |
| **Agent-quality problem** | Platform limitation | Platform team | Platform behavior causing issue, can't resolve through config |

## Quick Remediation Reference

### Eval-setup fixes
| Sub-Type | Fix |
|----------|-----|
| Outdated expected answer | Update to match current source content |
| Overly rigid grader | Switch to Compare Meaning, or broaden keyword set |
| Unrealistic test case | Rewrite input using actual user language |
| Wrong eval method | Change method to match eval-set purpose |
| Grader error/bias | Review rubric, add examples, consider deterministic method |

### Agent-quality fixes
| Failure pattern | Common Fix |
|----------------|-----------|
| Factual accuracy (wrong source) | Review knowledge source config, verify indexing, check vocabulary match |
| Factual accuracy (wrong extraction) | Add extraction guidance to system prompt |
| Hallucination (faithfulness failure) | Improve retrieval/chunking first; add refusal instruction |
| Wrong tool fires | Rewrite tool descriptions to differentiate; add negative examples |
| Tool doesn't fire | Review trigger conditions; check if tool is enabled and accessible |
| Wrong topic fires | Review trigger phrase overlap; adjust priority ordering |
| Lacks empathy | Add context-specific tone instructions to system prompt |
| Scope violation | Add explicit out-of-scope instruction |
| PII leakage | Add PII protection instruction; review authentication scope |

## Priority Order for Triage

1. Failed hard gates (especially trust & safety sets) — blocks deploy regardless of aggregate score
2. High-risk capability failures (accuracy, faithfulness, tool use) — direct impact on agent value
3. Lowest-scoring eval set failures — likely systemic, fixing one pattern resolves multiple
4. Recurring failures across baseline/re-runs — most diagnosable and regression-prone
5. Soft-target misses — important but non-blocking unless pattern worsens

## Non-Determinism Handling
- Establish baselines: Run 3+ times before treating score as definitive baseline
- Normal variance: +/-5% between runs. Investigate if >10%.
- Small eval sets (<30 cases): Single flip changes score by 3%+ — don't over-interpret

## Verdict Rules
| Any failed hard gate | → BLOCK |
| Capability set below hard floor | → ITERATE or BLOCK (by risk tier) |
| Soft target missed only | → SHIP WITH KNOWN GAPS / ITERATE |
| All hard gates + targets pass | → SHIP |
