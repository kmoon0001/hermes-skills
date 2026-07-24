# RESPONSE FORMAT: Agent-Specific Impact (June 16, 2026)

## Confirmed Data

| Agent | Guard Topics | Before | After Unconditional | Result |
|-------|-------------|--------|-------------------|--------|
| OT | 2 (simple) | SR 97% | N/A (already unconditional) | ✅ |
| SLP | 17 (complex) | SR 86% | **SR 95%** | ✅ +9% |
| PT | 15 (intake) | SR 94% | **SR 82%** | ❌ -12% |
| TDA | 0 (routing) | SR 94% | **SR 92%** (added RF) | ❌ -2% |

## Why SLP Improved

SLP's 17 Conv Guard topics are designed for multi-turn conversation element checks. The unconditional RESPONSE FORMAT ensured consistent structured output even when guard topics intercepted general clinical questions. Without it, guard topics produced free-text responses the grader couldn't evaluate.

## Why PT Regressed

PT's 15 Eval Guard topics are **intake patterns** — they ask follow-up questions. The unconditional RESPONSE FORMAT told the model to always use the structured audit format, conflicting with the intake pattern. The model produced confused responses that were neither proper audits nor proper intake questions.

PT's conditional format ("Use for full document audits only") correctly tells the model: "For explicit audit requests → use format. For general questions → natural answer." This separation is critical for PT's guard topic architecture.

## Why TDA Regressed

TDA is a routing/hub agent. It delegates to OT/PT/SLP specialists. Adding RESPONSE FORMAT made TDA try to produce audit responses directly instead of routing. The model attempted to score/classify documents it wasn't designed to audit.

## Decision Framework

Before changing RESPONSE FORMAT:
1. Count guard topics (>10 = high risk of conflict)
2. Check if routing agent (TDA, hub) → no RESPONSE FORMAT needed
3. Check guard topic type: intake (ask follow-up questions) vs conv guard (element checks)
4. Test on ONE agent, verify with 2+ eval runs before applying to others
5. If reverting, verify instruction length matches original (PATCH can corrupt)

## Revert Pitfall

When reverting via Dataverse API `replace()`:
- The old/new text patterns may partially match
- This creates duplicates or malformed content
- PT grew from ~7200 to 8709 chars after conditional→unconditional→conditional revert
- Always check `rawData.length` before and after revert
- If corrupted, restore from the original data (not a second replace cycle)
