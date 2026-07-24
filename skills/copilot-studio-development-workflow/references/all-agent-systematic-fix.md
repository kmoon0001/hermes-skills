# All-Agent Systematic Fix Checklist

Follow Microsoft Learn evaluation triage in order:

## Layer 1.5 — KB Quality (MANDATORY FIRST)
- [ ] Descriptions populated and specific (not blank)
- [ ] Sources marked official/authoritative
- [ ] Content is fresh (recent modified dates)
- [ ] Sources cover the specific codes/standards evals test (CPT, ICD-10, LCD, etc.)

MS Learn: "Most accuracy issues come from the agent not having clean, complete, or interpretable content." Fix KB BEFORE touching agent config.

## Layer 2 — Evaluation Setup (fix before agent changes)
- [ ] **Grading method**: Switch failing test cases from "General quality" to "Compare meaning" at 0.50 threshold. This fixes wording-variance failures (citation-format false negatives, tool-instruction explanations, etc.)
- [ ] **Test case realism**: Do test cases use record_ids or simulate Dataverse lookups? These can't resolve in eval channel. Accept as limitation OR rewrite with inline text.
- [ ] **Grader reliability**: If same case flips pass/fail across runs (non-deterministic >10% variance), accept as grader ceiling — don't chase with agent changes.

## Layer 3 — Agent Configuration
- [ ] **CB additionalInstructions**: ≤4 bullets. "Cite when naturally applicable" — NOT "Must cite per response" (causes incomplete/ungrounded failures). Never force citations the model can't produce.
- [ ] **CB fallback activity**: One line, no commas, no question marks, no contractions. Provide compliance framework, not "I can help... say more." Test case refusal = agent not providing info = grader marks abstention.
- [ ] **SearchSpecificFiles**: NEVER in topics — restricts retrieval. Remove blocks entirely.
- [ ] **applyModelKnowledgeSetting**: Always `true` or omit. Never `false`.
- [ ] **webBrowsing**: `false` on ALL agents. File-based knowledge only.
- [ ] **Instructions audit**: Check sizes (PT/OT 3k-5.5k, SLP 1.8k-3k, TDA 4k-7k). Over upper range = duplicated/corrupted. Remove word "citation" if present.
- [ ] **Description vs Instructions**: Description = user-facing summary. Instructions = system prompt. Don't mix them.

## Per-Agent Architecture Notes

| Agent | CB | Primary Router | Special Rules |
|-------|-----|---------------|--------------|
| OT | ON | CB + guard topics | Guard topics must use SearchAndSummarizeContent |
| PT | OFF (OK) | Exact-match topics | Already 99% — minimal work needed |
| SLP | ON (REQUIRED) | CB (primary) | NEVER disable CB — crashes to 0%. Create guard topics for failing prompts. |
| TDA | ON | CB + guard topics | Child agent routing: verify botSchemaName matches |

## Evaluation Score Targets
- 80-90% = realistic per MS Learn
- 95%+ = requires clean agent config AND clean evaluation setup
- Non-deterministic 5-10% variance is normal — run 3x before calling a fix done
- "Compare meaning" at 0.50 is NOT a "50% accurate" measure — it's a semantic similarity threshold

## Key Failure Patterns by Signal

| Grader Signal | Root Cause | Fix |
|--------------|------------|-----|
| "refuses to help" | CB fallback has refusal, or SearchAndSummarizeContent missing | Fix CB activity + add SearchAndSummarizeContent |
| completeness: No | Model didn't provide enough substance | Increase knowledge quality OR improve CB additionalInstructions |
| groundedness: No | No knowledge source cited | KB gaps OR citations truncated at eval channel limit |
| relevance: No | Model answered wrong question | Topic routing mismatch — create guard topic with exact trigger |
| abstention: Yes | Model refused entirely | CB fallback needs compliance framework instead of "I can help..." |
