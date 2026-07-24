# 800-Character Limit Regression Cascade

## The Pattern

Multiple Copilot Studio topic YAMLs contain `Keep response under 800 characters` in their `SearchAndSummarizeContent.additionalInstructions`. This unenforceable limit causes the model to produce truncated/incomplete responses. When you fix ONE topic (remove the limit), the conversation flow changes — the follow-up now routes to OTHER topics that STILL have the limit. Result: **the total failure count stays the same or increases** because new topics become the failures.

## Evidence

**June 14, 2026 — SLP_Specialist conversation evaluation:**
- Before fix: 18/20 (90%) — 2 failures: "Analyze SLP Evaluation Report" + "Caregiver Cognitive Capacity"
- Fixed: Removed 800-char limit from "Analyze SLP Evaluation Report" topic YAML
- After fix: 17/20 (85%) — "Analyze SLP Evaluation Report" NOW PASSES but 3 NEW topics failed:
  1. "Can you check my SLP progress note for missing elements"
  2. "Can you review my SLP daily note for objective metrics"
  3. "Can you review my SLP progress note for baseline comparison"
- Root cause: All 3 new failures had the SAME 800-char limit in their topic YAMLs

## Detection

After each fix + evaluation pass, check TWO things:
1. Did the failure COUNT decrease? (should go down)
2. Did the failing TOPICS change? (if they changed, regression cascade)

If the same number (or more) tests fail but different topics are involved, the fix was correct but incomplete — batch-remove the 800-char limit from ALL topics.

## Fix

**Batch fix — remove from ALL topics at once:**
```
Scan every SearchAndSummarizeContent topic's additionalInstructions for "800"
Remove the entire line (usually: "Keep response under 800 characters.") 
Replace with nothing or: "Be concise but complete — prioritize accuracy and actionable findings over strict length limits."
```

Do NOT fix one topic at a time and re-test between each — the regression cascade will mask the improvement. Fix all topics, THEN re-test.

## Tools

- Python recipe in `references/batch-fixes.md` for bulk YAML edits
- Manual: open each topic in code editor, find "800", delete the line, save
- After fixing all topics: publish agent, trigger evaluation, compare to pre-fix baseline
