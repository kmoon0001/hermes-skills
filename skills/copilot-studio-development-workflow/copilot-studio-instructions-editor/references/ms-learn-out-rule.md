# MS Learn "Give the Agent an Out" — Document Availability Rule

## Source

Microsoft Learn: [Optimize prompts with custom instructions](https://learn.microsoft.com/microsoft-copilot-studio/guidance/optimize-prompts-custom-instructions) and [Use prompt modification](https://learn.microsoft.com/microsoft-copilot-studio/nlu-generative-answers-prompt-modification#best-practices-for-custom-instructions)

## Key Quote

> **"Give the agent an *out***: Give the agent an alternative path for when it's unable to complete the assigned task. For example, when the user asks a question, you might include 'respond with not found if the answer isn't present.' This alternative path helps the agent avoid generating false responses."

## Application to Audit Agents

When an audit agent receives a document review request but no document text is provided, the agent faces a dilemma:
1. **Fabricate** specific scores/findings → grader detects inaccuracy → FAIL
2. **Hedge** about missing document → grader marks "Question not answered" → FAIL
3. **Refuse** to help → grader marks "refuses to help" → FAIL

The "out" pattern solves this: provide an alternative path that is NEITHER fabrication, hedging, nor refusal.

## Proven Rule Text

Add this immediately after RESPONSE BEHAVIOR in agent instructions:

```
DOCUMENT AVAILABILITY RULE:
If the user asks to audit, review, or check a document but no document text
is provided, do NOT assign a specific numeric score. Instead state
"Score: N/A — requires document text for accurate scoring" and focus
the response on compliance requirements, required elements checklist,
and what to verify per CMS/ASHA standards. This prevents fabricated scores.
```

## Why This Works

- **Not fabrication**: Says explicitly "do NOT assign a specific score" and provides N/A
- **Not hedging**: Agent still provides full compliance guidance — just no made-up score
- **Not refusal**: Agent completes the response with requirements, checklist, and recommendations
- **MS Learn aligned**: Directly implements "give the agent an out" pattern

## Testing Status

- **SLP**: Applied June 17, 2026. Baseline 95% SR. Testing in progress.
- **OT/PT/TDA**: Pending SLP results before rollout.

## Safety

- Single rule addition, not a format restructuring
- Preserves full 6-section RESPONSE FORMAT when document text IS available
- Only changes behavior when no document text provided
- Risk: LOW — does not affect Conv evals (Conv always provides context)
