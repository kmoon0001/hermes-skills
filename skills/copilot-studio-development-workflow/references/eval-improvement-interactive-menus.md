# Eval Improvement: Interactive Menu Topics

Session: June 19, 2026 — QM Coach V2
Result: 71% → 95% single-response eval

## Pattern: Interactive Menu Topics Fail Single-Response Eval

Topics that return card-based menus, wizards, or interactive prompts instead of text answers consistently fail single-response evals.

**Why:** The eval grader expects a direct text answer. When the agent returns a menu card or interactive prompt, the grader sees it as "no answer" or "wrong format."

**Examples that failed:**
- Email Generator → returned email template selection menu
- Escalation Matrix → returned severity level selection card
- Workflow Menu → returned interactive workflow picker
- Severity Classifier → returned classification menu
- Intake Router → returned document type selection
- Driver Category → returned root cause category menu
- HITL Approval → returned approval workflow prompt

**Fix:** Either delete the topic (agent answers from general knowledge) or restructure with text answer first.

## Impact Analysis

| Change | Topics | SR Eval |
|--------|--------|---------|
| Before cleanup | 62 | 71% |
| After removing stubs + duplicates + menus | 30 | 95% |

**Primary factor:** Removing interactive menu topics (20 failures fixed)
**Secondary factor:** Removing stub topics (improved publish stability)
**Tertiary factor:** Removing duplicate topics (reduced routing confusion)

## Lesson

Fewer, cleaner topics beat more topics with stubs/duplicates/menus. The agent's general knowledge (grounded in knowledge sources) often gives better answers than structured topic workflows for open-ended questions.
