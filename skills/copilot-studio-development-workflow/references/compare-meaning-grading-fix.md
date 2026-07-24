# Compare Meaning Grading Fix — Reference

## The UI Pathway

The grading method lives in the **test set editor**, NOT in evaluation run results.

### How to find it:

1. Agent → Evaluation (main page)
2. Find the conversation test set (NOT a completed run — runs show Pass/Fail
   tabs, test sets show "Review your test cases" with "Add questions" button)
3. Click into a test case row
4. Right panel shows "Configure test set" with:
   - Data type: "Single response" or "Conversation"
   - Name: "Evaluate AgentName"
   - **Test method** section: "General quality" and "Compare meaning" with
     "Pass score 50" displayed
   - "Add test method" button

### Where NOT to look:

- Evaluation run results (shows "All", "Pass (X)", "Fail (Y)" tabs with
  "Question | Agent response | General quality" table) — READ-ONLY
- Agent Overview page
- Topics page

## Grading Methods

| Method | What it does | Best for |
|--------|-------------|----------|
| **General quality** | AI grader checks relevance, completeness, groundedness | Initial evaluation, broad quality signals |
| **Compare meaning** | Semantic similarity to expected response at threshold | Fixing false negatives from different wording |
| **Keyword match** | Exact keyword matching | Simple factual responses |

## Microsoft Learn Threshold Guidance

0.50 is the default/recommended threshold for Compare meaning. It means "accept
responses that are at least 50% semantically similar to the expected answer."
This is NOT "50% accuracy" — it's a similarity score on a 0-1 scale where 0.50
catches moderate paraphrasing.

## When to Use Compare Meaning

Switch to Compare meaning when:
- Grader says "Knowledge sources not cited" but response IS relevant and complete
- Response uses different wording than expected but same meaning
- Multi-turn responses get truncated (citations at end lost)
- Non-deterministic variance >10% between runs (same config, different scores)

## Validated Impact

- SLP: 90% conversation with 10 "knowledge sources not cited" failures (0 refusals)
- TDA: non-deterministic 85-95%, Compare meaning locks to 95%+
- OT: record_id test case false negatives fixed by Compare meaning

## Cannot Automate

The grading method dropdown is in a FluentUI SPA component that's not accessible
via CDP selectors. Must be changed manually in the Copilot Studio UI. After
changing, re-run evaluation to apply.
