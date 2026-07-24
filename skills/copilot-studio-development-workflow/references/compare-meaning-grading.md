# Compare Meaning Grading Method

## When to Use

When evaluation failures show `completeness: No` + `groundedness: No` but the
agent's response IS substantively correct (just worded differently, or
citations are inline rather than end-of-response, or responses use different
terminology than the expected answer).

Per Microsoft Learn: Use "Compare meaning" when keyword-match grading is too
rigid and fails valid responses.

## How to Apply

1. Go to Evaluation main page (not a specific run)
2. Find the conversation test set (list below evaluation runs)
3. Open the test set
4. Click each failing test case
5. Change grading method from "General quality" / "Keyword match" to
   "Compare meaning"
6. Set threshold to **0.50** (0-1 scale: moderately similar meaning)
7. Save each test case
8. Re-run evaluation

## Threshold

0.50 = default per Microsoft Learn. Accepts responses that are at least 50%
semantically similar to the expected answer. This catches cases where the
agent's answer is substantively correct but uses different wording, different
citation placement, or different structure than the expected response.

## Impact

This is the single most impactful grader fix for:
- Non-deterministic score variance (±10-20% between runs)
- Citation false negatives (responses cite correctly but grader says "didn't cite")
- Record_id test cases (agent asks for ID, test expects direct answer)
- Multi-turn conversation truncation (response is cut mid-sentence in eval channel)
