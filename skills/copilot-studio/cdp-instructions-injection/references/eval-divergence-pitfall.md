# Conversation Eval vs Single-Response Eval Divergence

## The Problem

After topic deletions or major restructuring, conversation evals can return 0% (all "Error") while single-response evals improve dramatically. This is NOT an agent quality issue — it's a broken reference issue.

## Symptoms

- Single-response eval: 90%+ (agent works fine)
- Conversation eval: 0% with "Error" on ALL cases
- Agent response: "--" (empty, not a wrong answer)
- Eval grader: "Something went wrong while evaluating this test case"

## Root Cause

Conversation evals use multi-turn (3+ messages per test case). If the agent routes turn 1 to a topic that was deleted, it returns empty. The eval grader then errors because it has no response to grade. This cascades to ALL conversation test cases.

Single-response evals don't have this problem because each question is independent.

## Detection

```
Single-response: 90%+    Conversation: 0% (all Error)
→ Broken topic references, NOT agent quality
```

Compare this to:
```
Single-response: 70%     Conversation: 50%
→ Agent quality issues, fix instructions/topics
```

## Fix Sequence

1. Search remaining topics for references to deleted topic names/GUIDs
2. Common reference types to check:
   - Menu items (ClosedListEntity items)
   - BeginDialog calls
   - Condition blocks (`Topic.routeChoice = 'Deleted Topic'`)
3. Fix via Monaco code editor (manual paste)
4. Republish (critical — agent re-indexes on publish)
5. Re-run conversation eval

## Why Republishing Is Critical

The agent's topic index doesn't update until publish. Running evals against unpublished deletions means the agent still "sees" the deleted topics in its index but can't route to them, causing empty responses.

## Example (QM Coach V2, Jun 19, 2026)

1. Deleted 10 duplicate topics via Dataverse API
2. Single-response eval: 71% → 95% (+24 points!)
3. Conversation eval: 50% → 0% (all errors)
4. Found QM Orchestrator referenced deleted "QM Intake" topic
5. Fixed reference, republished
6. Conversation eval expected to recover

## Not Always Broken References

If conversation eval errors persist after fixing all references:
- Could be platform rate limiting (ran too many evals today)
- Could be connected agent failures (child agent unpublished)
- Wait 1 hour and retry before investigating deeper
