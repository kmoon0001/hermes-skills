# Evaluation Triage: Instruction-Level vs Topic-Level Root Causes

## The Critical Diagnostic Question

When an evaluation fails with "refuses to help by showing an error message,"
the first diagnostic question is: **Is this the same error for ALL failing cases,
or specific to certain question types?**

## The Instruction-Level vs Topic-Level Filter

| Grader Feedback | Likely Root Cause |
|-----------------|-------------------|
| "In the third response, the agent refuses to help by showing an error message" — **same for ALL failing cases** | **Topic-level bug** — one topic errors out on follow-up turns. Most common fix: add `EndDialog` with `clearTopicQueue: true` to the topic handling follow-up queries (General Clinical Inquiry, Fallback, or the specific intent topic). |
| "In the third response, the agent refuses to help..." — **only some cases** | **Topic-specific error** — different topics have different bugs. Check each failing case's triggered topic. |
| Generic "Top 3 findings" checklist response — ALL cases | **Instruction-level** — "do NOT ask for document" or missing RESPONSE FORMAT |
| Truncated/short responses — ALL cases | **Instruction-level** — unenforceable character limit |
| `[^1_2^]` or `cite:1` tags in output — ALL cases | **Instruction-level** — citation tag preservation |
| Fluctuates between runs | Topic routing — duplicate handlers |
| One score improves, another regresses after fix | Instruction/topic conflict — fix was wrong root cause |

## Case Study: PT_Specialist 80% Conversation (4/20 Failed)

All 4 failures had identical grader feedback: *"In the third response, the agent refuses
to help by showing an error message."*

Despite the failures being on different question types (caregiver education, missing
elements, general clinical inquiry, caregiver competency), they ALL shared the same pattern —
topic error on turn 3. This pointed to a **single topic bug**, not four separate issues.

**Root cause found:** The `General PT Clinical Inquiry` topic (a `SearchAndSummarizeContent`
topic) had NO `EndDialog` after its action. When follow-up questions hit this topic:
1. Turn 1-2: Works fine (first topic activation)
2. Turn 3: Topic queue builds up → Copilot Studio throws internal error

**Fix applied:** Added `EndDialog` with `clearTopicQueue: true` to the topic YAML.

**Key lesson:** When ALL failures share the same grader feedback, look for a single
root cause — even if the failing questions seem unrelated. A topic that fires on
follow-up turns affects every conversation that hits it.
