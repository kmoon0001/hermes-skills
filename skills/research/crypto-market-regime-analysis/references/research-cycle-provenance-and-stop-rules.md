# Frozen Research Cycles: Provenance, Staged Stops, and Runner Reliability

Use this reference when a historical crypto-strategy investigation has already tested several families and must decide whether to run one final hypothesis, stop, or open a sealed validation period.

## First: verify implementation fidelity before interpreting results

**Before any metric is computed, confirm that the engine actually executed the stated hypothesis.** A protocol may describe a mechanism that the implementation never exercises. Mechanical validity gates (no NaN NAV, sufficient data, all tests passing) do not guarantee hypothesis fidelity — the code may run cleanly while the intended signal path is dead code.

Specific checks at every decision point:

1. **Trace the causal path.** For each variant, confirm that the distinguishing parameter/switch actually reaches the allocation function. Run the experiment with a diagnostic that prints each variant's effective exposure alongside the raw signal values. If variant C's exposure equals B's at every timestep, the distinguishing mechanism (veto, filter, fade) was never engaged.

2. **Probe with synthetic edge cases.** Before running on real data, feed the engine a fabricated observation where the distinguishing signal is at its most extreme (e.g., funding at P99, OI doubling, premium at maximum). Verify that variant C diverges from B in that row. If it does not, the join or routing is broken.

3. **Staple a provenance trace into the result artifact.** The runner should record for each asset/decision whether each feature was available, stale, or missing, and — for conjunctive gates — which individual component fired. A reported "C ≡ B at every decision" with no explanation of why the distinguishing feature was always missing or always neutral is a red flag, not a valid NO-GO.

4. **Check for silent default/fallback chains.** A parameter defaulted to `None`, a missing file silently caught, or a feature-framework switch defaulting to `False` can bypass the entire signal path without raising an error. Audit every default value between the runner and the allocation function.

5. **Verify row counts.** If the implementation claims derivatives data was loaded but the experiment used spot-only features, the cache may have been read but never joined. Check that the number of joined rows approximates the number of decision dates × assets for the feature in question.

A cycle whose engine does not exercise the stated hypothesis is not evidence against that hypothesis. It is a failed implementation, not a valid experiment. The appropriate action is to fix the join or routing and re-run within the same development window — not to close the mechanism branch.

## One-cycle budget after repeated failures

After several economically distinct families fail, do not keep mining nearby variants. Permit at most one final hypothesis only when it:

- has a distinct mechanism rather than a new parameterization of a failed family;
- can be stated as one deterministic rule before reading development results;
- has a matched control that separates selection/timing from broad crypto beta and volatility scaling;
- uses a fixed universe, execution clock, cost schedule, and pass/fail gates;
- includes an explicit terminal rule: failure closes that data/mechanism branch.

A five-asset major-coin universe can test a rotation rule, but cannot establish a general cross-sectional factor. Treat positive results as universe-specific until independently replicated.

## Freeze in this order

1. Write the protocol, including hypothesis, controls, observation/decision/execution timestamps, costs, stress cases, diagnostics, gates, and stop rule.
2. Commit the protocol by itself.
3. Write deterministic tests before the engine: signal boundary, completed-bar timing, tie-breaks, missing-data behavior, exact turnover/cost arithmetic, final liquidation, contribution identity, and future truncation.
4. Commit the tested engine before inspecting development output.
5. Run development only and emit a machine-readable result artifact.
6. Write the human result report from that artifact.
7. Commit runner, result, and report; rerun once from a clean tree and freeze the resulting provenance fields.

This ordering makes it possible to prove that the specification preceded the implementation and that implementation preceded result inspection.

### Freeze formulas, not metric labels

A phrase such as “C minus B” is too ambiguous for a preregistration. Store exact estimands in a machine-readable protocol companion and test them before the engine exists. For example:

- economic improvement: `CAGR(C) - CAGR(B)` and `Sharpe(C) - Sharpe(B)`;
- incremental terminal P&L: `terminal_NAV(C) - terminal_NAV(B)` from equal starting NAVs;
- dependent-data bootstrap series: aligned daily arithmetic returns `r_C - r_B`;
- best-period deletion series: `log1p(r_C) - log1p(r_B)`;
- tail-risk comparisons: `max_drawdown(C) <= max_drawdown(B)` and signed `ES95(C) >= ES95(B)`.

Add contract tests for execution clocks, variants, costs, staleness, gates, sealed years, forbidden features, and estimand strings. If a source-field or formula ambiguity is discovered before parser code or result inspection, resolve it in a named clarification commit with a failing-then-passing contract test. Never silently reinterpret the protocol after results exist.

## Staged diagnostics and immediate stop

Separate gates into stages:

- **Primary:** excess CAGR/return versus the matched control, Sharpe improvement, drawdown, and chronological consistency.
- **Robustness:** costs, execution delays, leave-one-asset-out, concentration, and dependent-data bootstrap.
- **Advanced search correction:** random-signal placebos, DSR, SPA/Reality Check, or PBO.
- **Validation:** sequential sealed periods and independent exchange/temporal replication.

If a frozen primary or robustness gate fails, the cycle is already NO-GO. Advanced multiple-testing diagnostics may be skipped under an explicit immediate-stop rule; record them as “not run because a prior gate failed,” never as missing evidence or as an opportunity to rescue the candidate.

A positive absolute return does not override negative excess performance. Likewise, a volatility-scaled variant is not signal alpha when an identically scaled always-long control is better.

## Event-accounting details worth testing

For open-executed, close-marked hourly simulation:

- include prior-close to current-open gap P&L on pre-existing units;
- deduct rebalance costs at the executable open;
- accrue current-open to current-close P&L on post-trade units;
- charge a final liquidation at the last allowed close;
- allocate both rebalance and liquidation costs to asset contributions;
- assert per-row asset contributions sum to portfolio return.

Do not omit final liquidation merely because the study ends; doing so systematically favors high-turnover or concentrated terminal holdings.

## Reproducible experiment-runner pattern

The runner should emit:

- development boundaries and a `reserved_periods_opened` flag;
- frozen parameters and all controls;
- primary and sensitivity metrics;
- every gate as an explicit boolean;
- reasons for diagnostics intentionally skipped by the stop rule;
- source-data SHA-256 hashes;
- Git commit and clean-tree state;
- deterministic bootstrap seed and replicate count.

When logging through `tee`, enable pipeline failure propagation:

```bash
set -o pipefail && python -m research.run_experiment 2>&1 | tee research/run.log
```

Without `pipefail`, a crashed Python process can be reported as exit code 0 because `tee` succeeded.

Before JSON serialization, normalize NumPy scalar types rather than special-casing only floats or booleans:

```python
if isinstance(value, np.generic):
    value = value.item()
```

Then reject or convert non-finite floats explicitly. This prevents a completed computation from failing only while writing its artifact.

## Safe repository publication

Treat remote creation and push as the final research gate, not an early backup step. Before publishing:

1. Finish protocol, tested implementation, development result/report, and stop-rule decision.
2. Verify the Git tree and history, generated-artifact sizes, ignored files, and remote/auth state.
3. Scan **Git-tracked content and Git history**, not the entire working directory. A broad recursive scan can read ignored local configs and print their secret values into logs. Scanner output should contain only redacted path/line locations.
4. Confirm credential-bearing configs are ignored, currently untracked, and absent from history. Also inspect launchers, reports, and README files for local usernames, absolute home paths, private endpoints, or stale operational claims.
5. Keep raw archives, market-data caches, notebooks, backtest result directories, and generated feature caches ignored unless there is an explicit size/provenance decision to publish them.
6. If repository visibility was not specified, default to **private**. Create the remote only after the final scan, push, then verify the remote URL, visibility, default branch, and remote commit hash.

A disabled test placeholder may resemble a secret. Allowlist it only after confirming it is nonfunctional; never weaken the scanner globally.

## Final verification

Before reporting completion, assert programmatically that:

- development ends before every sealed period;
- the sealed-period flag is false;
- data hashes match current inputs;
- gate counts agree with the written report;
- the report contains the same headline metrics as the JSON artifact;
- relevant tests pass;
- the final Git tree is clean.

If the final cycle fails, close that mechanism branch. Further work requires a genuinely new information source or economic mechanism, not a new lookback, holding count, rebalance anchor, or regime filter on the same development sample.
