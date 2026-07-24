# MS Learn Evaluation-Driven Triage Framework

Source: https://learn.microsoft.com/microsoft-copilot-studio/guidance/evaluation-triage-overview

## When to Use

Use this framework when:
1. An evaluation set scores below an expected threshold
2. Specific test cases fail and the root cause is unclear
3. Scores improve in one area but regress in another
4. Multiple evaluation sets fail and priorities are unclear
5. An agent's behavior changes unexpectedly after an update

## Key Principle

"Based on what you learn, you may decide to update a knowledge source, topic trigger, agent instructions, or other components. After each change, rerun the evaluation to confirm the fix and ensure no regressions occur."

This means instructions are NOT the only lever. Topics and knowledge sources are equally valid remediation paths.

## Remediation Decision Tree

```
FAILURE TYPE → REMEDIATION PATH

"refuses to help" / "error message"
  → Check "Allow ungrounded responses" toggle (Settings > Generative AI > Knowledge)

"incomplete" / "didn't cite knowledge sources"
  → Fix instructions (hedging removal, citation ban, conciseness)

"Question not answered" / "not grounded"
  → Check knowledge source descriptions (blank = random routing)
  → Add/fix topic triggers

Fails on ONE specific question category (e.g., caregiver)
  → Create/fix topic for that category
  → Check if passing agent has a topic the failing agent doesn't

Fails on MULTIPLE categories
  → Instruction-level fix (conciseness, citation, hedging)
```

## Incremental Change Rule

"The system treats agent instructions similar to code. The wrong code might break your system. Try removing your agent instructions and adding individual instructions back slowly. Test between each addition."

This applies to ALL changes: instructions, topics, knowledge sources. Never stack multiple changes without testing between each.

## Anti-Patterns

1. **Stacking fixes** — Adding 3+ instruction changes at once causes compounding regressions
2. **Generalizing across agents** — A fix proven on one agent may cause regression on another
3. **Using aggressive language** — CRITICAL, MANDATORY, NEVER cause model overcorrection
4. **Instruction-only thinking** — Topics and knowledge sources are valid remediation paths
5. **Not reading actual grader reasons** — Always click into failures to see the EXACT grader output
