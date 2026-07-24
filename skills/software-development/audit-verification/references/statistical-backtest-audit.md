# Statistical Backtest Audit Checklist

Use this reference when verifying a preregistered trading experiment, robustness report, or promotion decision. The goal is to distinguish a correct **no-go/pass decision** from overconfident interpretation of diagnostics.

## 1. Reconstruct the decision hierarchy

- Identify the binding preregistration; distinguish it from earlier memos or recommendations.
- Map each declared gate to code and output.
- Separate **gates** from **diagnostics**. A diagnostic added in code after preregistration must not be described as a frozen gate, even if it is stricter.
- Distinguish an intermediate aggregate such as `pass_before_search_adjustment` from a final promotion decision.
- If DSR, SPA, Reality Check, PBO, or another declared search correction is absent, do not infer a final search-adjusted pass. If upstream gates already fail, state that the omission cannot rescue promotion.

## 2. Bootstrap and inference

- Verify the exact method name: moving-block, circular-block, stationary, and IID bootstrap are not interchangeable.
- Confirm blocks resample complete cross-asset date vectors together, or that the portfolio difference was aggregated by date before resampling.
- Check whether block lengths plausibly cover dependence induced by signal holding periods and regimes. Two nearby block lengths are sensitivity checks, not independent confirmations.
- A percentile lower confidence bound above zero can implement a superiority gate. The fraction of bootstrap draws above zero is **not** a Bayesian posterior probability and generally is not a p-value.
- If a two-sided interval includes zero and positive effects, the defensible conclusion is “superiority was not demonstrated,” not “the true edge is negative.”
- Check whether the statistic being bootstrapped matches the stated estimand (for example, daily log-return difference versus CAGR difference).

## 3. Temporal slices

- Derive the effective return start after signal/volatility warm-up. Do not count a nearly empty first half-year or year equally with complete periods without explicit disclosure.
- Label partial calendar slices and report their observation counts.
- Annual and half-year slices are nested and dependent; their sign counts are robustness summaries, not independent replications.
- For future protocols, preload warm-up history before the evaluation start or gate only complete eligible slices.

## 4. Portfolio accounting, costs, and latency

- Reconstruct the self-financing accounting identity for every bar: starting NAV, trade notional, cost, market P&L, ending NAV. Add a machine assertion that per-asset P&L minus costs reconciles to total NAV change.
- If the protocol declares independent fixed-capital sleeves, initialize each sleeve separately and compound it from its own NAV. Never rebuild sleeve holdings as a fraction of pooled portfolio NAV; that transfers winners’ gains to losers and creates hidden equal-weight rebalancing.
- Test the independence invariant with a synthetic winner and flat asset: after the winner appreciates, an unchanged sleeve target must not transfer its gain or generate cross-sleeve turnover.
- In leave-one-out tests, verify whether the omitted sleeve remains cash or remaining sleeves are renormalized. Preserve cash when the frozen rule declares fixed sleeve capital.
- Confirm one-way/two-way terminology, turnover basis, and whether costs apply to every actual trade. A target based on post-cost NAV may require solving trade notional self-consistently rather than subtracting cost after setting holdings; test the exact one-trade solution.
- Include initial NAV as the first high-water mark in drawdown calculations. Otherwise a loss on the first observed return can disappear from maximum drawdown.
- Retain the declared evaluation window unless the protocol explicitly authorizes trimming. During signal or volatility warm-up, record cash returns rather than discarding dates; report the number and boundaries of actual open-to-next-open observations.
- Do not cross into a sealed period merely to obtain a terminal next-open price. State the final return boundary explicitly when preserving the seal omits the last nominal day’s forward return.
- Verify monotonic behavior across cost scenarios and explain differing cost drag through differing turnover.
- Delay every matched comparison cell consistently. Confirm “one day” means one calendar/trading bar rather than merely the next surviving complete-case row.
- A sensitivity grid is not a break-even analysis unless the break-even cost is actually calculated.

## 5. Benchmark and exposure effects

- A matched benchmark should share the same universe, risk scaler, execution timing, and costs, differing only in the intended signal switch.
- Report realized exposure and volatility ratios. Lower drawdown or expected shortfall from a much lower-exposure strategy is absolute risk reduction, not evidence of timing skill.
- Use risk/exposure-matched diagnostics if claiming alpha independent of cash allocation. Sharpe comparisons and unscaled ablations can help, but state exactly what each comparison identifies.
- Distinguish relative terminal wealth, `(1 + R_strategy)/(1 + R_benchmark) - 1`, from the percentage-point difference in cumulative returns and from CAGR difference.

## 6. Breadth and leave-one-out

- Per-asset attribution used for breadth gates must be additive in a common wealth/currency unit. Do not sum daily return contributions normalized by two strategies’ different NAVs and call the result terminal incremental P&L.
- Reconcile per-asset attributions to the portfolio-level wealth difference before using signs or concentration shares.
- Verify whether leave-one-out keeps the omitted sleeve in cash or renormalizes remaining sleeves; either can be valid, but it answers a different question and must match the frozen allocation rule.
- Leave-one-out runs from correlated assets are dependent diagnostics, not independent replications.

## 7. Missing and stale data

- Verify the implementation matches the declared policy. Complete-case dropping a date across the entire universe is not equivalent to forcing only the affected sleeve to cash.
- Confirm explicit stale-price detection if the protocol promises it; a complete timestamp grid alone does not detect repeated stale values.
- Determine whether a latent implementation defect affected the realized sample before declaring results invalid. A full calendar row count can show that missing-day handling was dormant, while stale handling may remain unverified.

## 7b. Comparison integrity (candidate vs baseline)

When the task is "is candidate X an improvement over baseline Y / is it production-ready," the comparison itself must be clean before any metric delta means anything.

- **Requested/claimed metric must exist in source.** If the task asks to compare a specific metric (Sortino, Calmar, information ratio) verify the codebase actually computes it before reporting. If `compute_metrics` (or equivalent) returns only a subset — e.g. CAGR/Sharpe/MaxDD/ExpectedShortfall and no Sortino — report the missing metric as `NOT_COMPUTED`. Never fabricate, estimate, or silently substitute a metric that the engine does not produce. Note that adding it would require an engine change first.
- **Comparison-window mismatch.** Confirm candidate and baseline are computed on the SAME sample window before comparing CAGR or Sharpe. A candidate measured on a 1-year OOS slice is not comparable to a baseline measured on a 4-year expanding window — CAGR and Sharpe both scale with sample composition and length. If a same-window baseline artifact exists (e.g. `*_results_2024.json` alongside the 4-year `*_results.json`), use it; otherwise flag the mismatch explicitly and downgrade the comparison to "rough context, not like-for-like."
- **Confounded multi-feature swaps.** A candidate is only evidence for feature F if it differs from the baseline in F alone. If the candidate also simplified the engine (dropped shorts, funding fade, regime filter; switched long-only; changed concentration caps), the metric delta is confounded and cannot be attributed to F. State that the comparison does not isolate the new feature, and describe what a clean matched comparison would require (same engine + F toggled).
- **Sample-adequacy on trade count.** Before crediting a sleeve/strategy with an edge, check how many trades actually fired. A handful of trades (single digits), or trades clustered in one short window, cannot validate alpha regardless of their individual returns — flag high over-fit / regime-specificity risk. "Each trade cleared >2× cost" over 3 trades is not evidence of a durable edge.
- **Absence of a significance test.** If the candidate result JSON has no bootstrap CI (while sibling baselines do), note that no statistical-significance test exists for the candidate's edge — a point estimate alone cannot support a production-ready verdict.

## 8. Reporting language

- A correct final NO-GO does not excuse incorrect accounting or statistics. If an audit defect is material, add a failing regression test, correct the implementation without changing the frozen hypothesis, rerun development only, and mark the old numerical results superseded.
- Commit executable code before regenerating evidence so the artifact can record the exact code commit. Preserve input hashes, sealed-period flags, attribution reconciliation error, gate counts, and a clean-tree verification.
- Distinguish the correction’s effect on the numbers from its effect on the decision (for example, “figures changed materially; NO-GO was unchanged and strengthened”).

Prefer:

- “The candidate failed promotion.”
- “Observed performance was negative, but the interval does not establish a negative population edge.”
- “The tail-risk component passed in absolute terms but is confounded by lower exposure.”
- “This was a diagnostic, not a preregistered gate.”
- “Sortino was requested but the engine does not compute it; reported as NOT_COMPUTED.”
- “Candidate is 1-year OOS, baseline is 4-year — not a like-for-like comparison.”
- “The candidate also changed the engine, so the delta does not isolate the new sleeve.”
- “Three trades in one window is insufficient to validate an edge.”

Avoid:

- Treating bootstrap draw fractions as posterior probabilities.
- Calling lower drawdown “alpha” without exposure normalization.
- Calling an intermediate pre-search gate a final pass.
- Presenting nested slices or leave-one-out portfolios as independent confirmations.
