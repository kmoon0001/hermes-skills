# Non-Deterministic Scoring in General Quality Evaluations

## Pattern

The same agent (same instructions, same topics, same published version) can produce different scores across consecutive evaluation runs with NO code changes between runs.

## Observed Variance (June 14, 2026)

**SLP_Specialist Conv (20 test cases):**
- Run 260614_0514: 90%
- Run 260614_1136: 85%
- Run 260614_1231: 85%
- Run 260614_1617: 95%
- Run 260614_1657: 85%

All runs used the same published agent version. Score range: 85-95% (10-point swing).

**OT_Specialist Conv (20 test cases):**
- Run 260614_0152: 75%
- Run 260614_0417: 100%
- Run 260614_1152: 85%
- Run 260614_1539: 90%

## Root Causes

1. **Non-deterministic LLM responses** — The underlying GPT model produces different responses to the same prompt on different runs. Multi-turn conversations amplify this because each turn introduces variance that compounds across 6+ turns.

2. **Grader non-determinism** — The General Quality grader (also an LLM) applies criteria slightly differently each time. A borderline "complete" response might pass on one run and fail on another.

3. **Topic routing variance** — If the agent has multiple topics with overlapping triggers (e.g., "General Inquiry" vs "Evaluate"), different runs may route the same question to different topics, producing different response structures that the grader evaluates differently.

## Mitigation

1. **Re-test 2-3 times** before attributing a score to a code change. A score that improves from 85% to 90% on a single run might just be natural variance.

2. **Look at the trend, not individual runs.** If 3 out of 5 runs show 90%+ and 2 show 85%, the agent is probably at ~90% and the 85% runs are variance.

3. **Run SR evaluations for stable baselines.** SR (100 test cases) has much lower variance than Conv (20 test cases) because the larger sample size smooths out individual response variance.

4. **Don't chase single-run regressions.** If SLP scores 95% then 85% with no changes, DON'T immediately start fixing code. Run it again first.

## Decision Rule

| Runs below target | Recommended action |
|-------------------|-------------------|
| 1 of 3 | Variance — no action needed |
| 2 of 3 | Likely real issue — investigate |
| 3 of 3 | Confirmed problem — fix required |

## Key Insight

The user observed SLP going from 95% back to 85% "for some reason unknown to me." This is natural non-deterministic variance, not a regression. The agent didn't change — the LLM just produced different responses on different runs.
