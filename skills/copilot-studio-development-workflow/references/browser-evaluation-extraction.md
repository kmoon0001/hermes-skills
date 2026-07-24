# Browser-Based Evaluation Extraction Pattern

When programmatic evaluation APIs are unavailable, extract failed test cases from the Copilot Studio Evaluation page via browser snapshot + text parsing.

## Navigation

1. Navigate to `.../bots/<botId>/evaluation` — the page takes 15-30 seconds to render
2. Find the target run row in "Recent results" — look for the specific timestamp or score
3. Click the row to open the run detail page
4. Wait 10+ seconds for per-case results to render
5. Extract using `document.body.innerText` or snapshot parsing

## Pattern Matching on Failure Clusters

To identify the root cause, classify 5+ failures by response structure:

### Instruction-level (all failures look the same)
If every failed response starts with `"**Top Compliance Findings:**"` or `"**Top 3 critical requirements:**"`:
→ Instructions say "do NOT ask for the document; give 3-4 required elements" (SLP case)

If every failed response is unusually short/truncated:
→ Unenforceable character limit in instructions (e.g., "NEVER exceed 800 characters")

If every failed response contains `[^x_y^]` or `cite:1` tags:
→ Citation tag preservation instruction

### Topic-level (failures cluster by document type)
If only progress-note questions fail but evaluation questions pass:
→ Topic-level issue with the Analyze Progress Note topic

If only conversation (multi-turn) tests fail but single-response pass:
→ Queue management (missing clearTopicQueue) or instruction-level (agent behavior differs across turns)

### Random (no clear pattern)
→ Duplicate topic handlers, OnUnknownIntent conflicts, or grader inconsistency

## Score Trend Analysis

Reading from the recent-results grid, track by test type:

```
Single Response (100 tests):
  94% → 92% → 89% → 88% → 87% → 78%  (Declining — check instructions/knowledge)

Conversation (20 tests):
  95% → 75% → 80% → 95% → 70%         (Volatile — check topic queue/instructions)
```

When extracting scores from the UI, the "Pass: X%" text is in an `<img>` alt attribute:
```
<img alt="Pass: 78% (78 responses)">
```
