---
name: cycle5-causal-derivatives-pipeline
description: End-to-end 14-task Cycle 5 causal derivatives filter pipeline — protocol freeze, feature cache, engine, experiment, and publication. For repeating or adapting the full pipeline on a new hypothesis.
category: software-development
---

# Cycle 5 Causal Derivatives Filter Pipeline

Use this skill when starting a new Cycle (e.g. Cycle 6) that follows the same 14-task structure: protocol freeze → derivatives normalization → feature cache → causal engine → experiment → gates → publication.

## Architecture Overview

```
Protocol (frozen JSON/MD)
  → Archive enumeration + audit
    → Normalized funding/OI/premium parsers + causal selectors
      → Immutable feature cache (4,499 archives, 1.3M rows)
        → Engine: daily SMA200 trend + volatility scale + targets
          → Runner: load OHLCV, compute per-pair, aggregate portfolio
            → Metrics: CAGR, Sharpe, drawdown, ES, bootstrap
              → Validity gates + promotion gates
                → Result report + sealed reserved data
                  → Secret scan + private GitHub publication
```

## Repository Structure

All code lives under `research/` and `tests/` in the freqtrade repo:
- `research/cycle5_feature_cache.py` — Tasks 2-6: schema, normalizers, selectors, cache builder
- `research/cycle5_backtest.py` — Tasks 7-9: aggregation, trend, volatility, targets, sleeve simulation
- `research/run_cycle5_experiment.py` — Task 10: OHLCV loader, portfolio simulator, metrics, gates
- `research/cycle6_backtest.py` — Cycle 6/7 signals: TS MOM, Parkinson vol, funding fade, OI divergence, multi-signal fade, feature cache join, target builders C6/C7
- `research/run_cycle6_experiment.py` — C6 experiment runner with OI divergence, multi-signal fade, and inline bootstrap CI
- `research/run_cycle7_experiment.py` — C7 experiment runner with D sleeve, D-minus-B and D-minus-C comparisons
- `research/build_2024_cache.py` — Incremental 2024 cache build + combine + signal test script
- `research/cycle5_protocol.json` — Task 1: machine-readable frozen protocol
- `research/CYCLE67_RESULTS.md` — Final Cycle 6/7 documentation
- `tests/test_cycle5_feature_cache.py` — Tasks 2-6 tests
- `tests/test_cycle5_backtest.py` — Tasks 7-9 tests
- `tests/test_run_cycle5_experiment.py` — Task 10 tests

## The 14 Tasks

### Task 1: Lock the protocol
- File: `research/cycle5_protocol.json` + `CYCLE5_PROTOCOL.md`
- Freeze every constant, symbol list, time gate, cost, seed, and exclusion as testable JSON
- Commit pattern: `git add research/cycle5_protocol.json research/CYCLE5_PROTOCOL.md tests/test_cycle5_protocol.py docs/plans/*.md`

### Task 2: Normalized feature schema
- Files: `research/cycle5_feature_cache.py`, `tests/test_cycle5_feature_cache.py`
- Explicit dataclass row schema with UTC-aware timestamps, unique increasing measurement times
- Accept rows within 2021-2024; filter out rows outside via `normalize_open_interest_records` year check and `_require_development_timestamp`
- Commit pattern: `git add .gitignore research/cycle5_feature_cache.py tests/test_cycle5_feature_cache.py`

### Task 3: Funding normalization
- Parse settled Binance funding, `available_at=fundingTime`, strict `< decision_time`, 12h staleness
- Reject `nextFundingTime`, preserve source lineage
- [Reference: `research/derivatives_source_semantics.json`]

### Task 4: OI normalization
- `available_at=create_time+5m`, 10min current-age limit, exact 288-interval lag
- Exact-payload dedup, conflicting-payload invalidation, pair-specific inception masks

### Task 5: Premium pressure
- Parse hourly premium-index closes, `available_at=close_time`, 2h staleness
- Support both headerless (legacy) and headed (newer) Binance archive formats

### Task 6: Build and freeze feature cache
- Run: `python -m research.cycle5_feature_cache --build --start 2021-01-01 --end 2024-12-31 --workers 12`
- Validates: all manifests hashes, zero outside-window rows, monotonic features, cache SHA-256
- Independent review of tree + patch SHA-256 before commit
- **Incremental 2024 build** (when 2021-2023 cache already exists): `python -B research/build_2024_cache.py` — downloads 1950 2024-only archives across all 5 symbols, normalizes, writes `cycle5_features_2024.feather`, then combines with existing cache and tests OI divergence + multi-signal fade in one shot (see `scripts/build-2024-cache.md`)

### Tasks 7-9: Causal engine
- `research/cycle5_backtest.py`: daily aggregation, SMA200 trend, 60-day volatility scale
- Build targets A (trend+vol), B (trend only), C (B under derivatives veto), P (passive), PV (vol-timed passive)
- Independent 20% NAV sleeve simulation with T-close→T+1-open execution delay

### Task 10: Runner, metrics, bootstrap
- `research/run_cycle5_experiment.py`: load OHLCV, compute per-pair, aggregate, compute metrics
- `compute_metrics`: CAGR, annualized Sharpe, max drawdown, expected shortfall
- `block_bootstrap`: deterministic block bootstrap with exact seeds
- `validity_gates`: sufficient data, no NaN NAV, positive NAV
- Commit before inspecting results: `git add research/run_cycle5_experiment.py tests/test_run_cycle5_experiment.py research/cycle5_backtest.py tests/test_cycle5_backtest.py`

### Task 11: Pre-result independent audit
- Protocol-diff checks (compare runner constants against `cycle5_protocol.json`)
- Run all focused tests, syntax/whitespace checks, verify clean tree
- 2024 data is now authorized and cache-extendable via `_DEVELOPMENT_END = 2024-12-31`
- 2025 data remains sealed holdout — do not access

### Task 12: Run development experiment once
- Execute `python research/run_cycle5_experiment.py` from clean committed tree
- Record machine-readable result to `research/cycle5_results.json`
- Apply promotion gates mechanically — NO-GO if any fail

### Task 13: Reserved period gate
- If promotion passes: open 2024 first, then 2025 only after unchanged 2024 pass
- If promotion fails: seal permanently, do not open 2024/2025

### Task 14: Secret scan and publication
- Inventory tracked files, scan for credentials (`git grep` for api_key/password/token patterns)
- Verify `user_data/config.json` is gitignored
- Create private repo: `gh repo create kmoon0001/freqtrade-cycle5-research --private --push --source .`
- Verify: `gh repo view kmoon0001/freqtrade-cycle5-research --json name,url,visibility`

## Testing Pattern

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -B \
  -m pytest tests/test_cycle5_feature_cache.py tests/test_cycle5_backtest.py \
     tests/test_run_cycle5_experiment.py tests/test_cycle5_protocol.py \
     tests/test_derivatives*.py -q -p no:cacheprovider
```

## Cycle 6 FRAT Signals (reference)

When adapting the pipeline for a new cycle, see `references/cycle6-frat-signal-patterns.md` and `references/binance-2024-oi-data-format-changes.md`
in this skill for reusable signal functions:

- **TS MOM trend** — multi-lookback (20/50/100d) vote, replaces SMA200
- **Parkinson volatility** — high-low estimator (21d), replaces 60d std dev
- **Funding fade** — continuous P80+ percentile-rank reduction
- **Feature cache join** — queries funding/OI/premium by `available_at < decision_time`

These were implemented as `research/cycle6_backtest.py` (standalone module that reuses `cycle5_backtest.py` helpers).

### Cycle 6 Results (full 2021-2024 with OI divergence + multi-signal fade)

Cycle 6 fixed the Cycle 5 bug (cache → join → strategy **was traced and confirmed**) and tested a continuous P80+ funding-rate percentile fade + OI divergence + multi-signal conditional fade on top of TS MOM trend + Parkinson vol scaling. See `research/CYCLE67_RESULTS.md` for the full report.

| Metric | C6 (FRAT+OI+Multi, 2021-2024) | B reference (TS MOM + vol only, 2021-2024) |
|--------|-------------------------------|-------------------------------------------|
| **CAGR** | **+63.9%** | +68.4% (implied: C-minus-B = -5.6%) |
| Sharpe | 0.67 | ~0.67 |
| Max DD | 87.6% | ~87.6% |
| D-minus-C (multi-signal fade on top of OI) | **+0.68%** | — |

**Key finding:** C-minus-B is -5.6% — the combined fades reduce CAGR vs the pure TS MOM + vol baseline. In 2024's strong bull market, reducing exposure during extreme funding/OI divergence cost more than the risk reduction provided. The multi-signal fade adds a small positive contribution (+0.68% D-minus-C) when applied on top of OI divergence alone.

**Bootstrap 95% CI** (20k block replicates): CAGR [-24.6%, +250.1%], Sharpe [-0.37, 1.72] — neither reaches statistical significance on 4 years of high-variance crypto data.

**Critical bug discovered in Cycle 6:** `simulate_sleeves()` in `cycle5_backtest.py` computed each variant's sleeve allocation from the running total NAV (which included previously added variants). Variant "c" received a progressively larger base allocation than "a" and "b", creating a systematic upward bias for later-named variants. This caused a false positive C-minus-B (+6.3%).

**Fix:** Each sleeve now tracks its own independent cumulative NAV via `variant_nav[t]`. All variants start with SLEEVE_WEIGHT (0.20) and compound independently. Total NAV = sum of all 5 independent sleeve NAVs. Verified: when funding fade = 1.0 (no effect), C and B produce identical sleeve values to machine precision.

**Interpretation (post-bugfix):** The TS MOM (20/50/100) + Parkinson 21d vol baseline is genuinely strong at +63.8% CAGR over 2021-2023. The funding fade reduces performance by -5.7% C-minus-B. Economic interpretation: in persistent crypto trends, reducing exposure during extreme funding costs more than the mean-reversion benefit provides. 2024 (now authorized) may flip this if funding extremes are more frequent in bull markets.

### Consumed signals

The combined feature cache (`cycle5_features_combined.feather`, 1.9M rows) now drives three active signal paths:

| Signal | Cache | Engine | Status |
|--------|-------|--------|--------|
| Funding rate fade | Yes | `build_targets_c6(funding_fade=...)` | Tested (C6 FRAT baseline) |
| **OI divergence** (price + OI disagree → reduce) | Yes | `build_targets_c6(oi_divergence_factor=...)` | **Wired and tested** — D-minus-C +0.68% |
| **Multi-signal conditional fade** (funding extreme + OI confirm) | Yes | `build_targets_c6(multi_signal_fade=...)` | **Wired and tested** — replaces funding_fade when active |
| Premium duration | Yes | Not consumed | Untested |
| Two-sided funding (boost on extreme -) | Yes | Partial via multi-signal fade | Built into multi-signal fade |
| OI velocity (24h/7d/30d acceleration) | Needs rolling calc | No | Untested |
| P75/P85/P90 sensitivity | Yes | No (hardcoded 0.80) | Untested |

Signal stacking in the C7 target builder:

```
A = trend_mom (TS MOM vote)
B = trend_mom × vol_scale  (baseline)
C = B × oi_divergence_factor  (OI divergence overlay)
D = C × multi_signal_fade  (conditional fade, replaces funding_fade when provided)
```

## Cycle 7 Results (2021-2024)

Final experiment results in `research/CYCLE67_RESULTS.md`:

| Metric | C6 (FRAT+OI+Multi) | C7 (Full Stack D) |
|--------|---------------------|-------------------|
| CAGR | +63.9% | +56.1% |
| Sharpe | 0.67 | 0.64 |
| Max DD | 87.6% | 85.9% |
| C/D-minus-B | -5.6% | -5.6% |
| D-minus-C | — | **+0.68%** |

Neither CAGR nor Sharpe reaches 95% statistical significance (20k bootstrap CI spans zero on 4-year sample).

Key takeaway: OI divergence threshold (0.50) is too aggressive — fires ~46-50% of trading days in 2024. Multi-signal fade adds marginal positive value (+0.68%). See `references/cycle7-results.md`.

### Data boundaries (as of July 2026)

| Period | Status | Use permission |
|--------|--------|----------------|
| 2021-01 to 2023-12 | Development (fully consumed) | Only for NEW hypotheses, not Cycles 1-6 retunes |
| **2024-01 to 2024-12** | **Cache extendable** | **First genuine out-of-sample validation** |
| 2025-01 to 2025-07 | Sealed holdout | Never inspected — do not access |
| 2025-07 to 2026-07 | Exploratory (previously viewed) | Known post-holdout stress only |

### Priority hypotheses for next cycle

1. **Two-sided funding with OI confirmation** — extends the C-minus-B diagnostic to a two-sided funding signal (fade on extreme +, boost on extreme -). ~60 LOC.
2. **OI divergence trend confirmation** — reduce exposure when price and OI move opposite. ~40 LOC from existing cache.
3. **Multi-signal conditional fade** — funding fade only when OI also confirms crowding. ~50 LOC.

## Cycle 6 Production Pipeline

After research validation, the Cycle 6 strategy was deployed as a daily production pipeline with P&L tracking, monitoring, and alerting:

### Architecture

```
Daily cron (10:00 PT) — production/run_cycle6_full.sh
  → generate_signals.py
      1. Downloads latest 1d OHLCV from OKX via `freqtrade download-data`
      2. Imports research.cycle6_backtest functions directly (not duplicated formulas)
      3. Computes TS MOM trend + Parkinson vol scale at target 0.15
      4. Writes targets to production/signals.json
  → execute_trades.py
      1. Reads signals.json
      2. Positions sized from total equity (20% per-position cap)
      3. Dry-run: logs intended trades. Live: would execute via CCXT
  → trade_logger.py
      1. Reads positions.json, compares against last known state
      2. Detects new entries and exits, records trade P&L
      3. Tracks running equity curve in production/trade_history.json
      4. Idempotent — re-running same day skips duplicates
  → check_alerts.py
      1. Drawdown thresholds: Warning at 25%, Critical at 30%
      2. Signal change detection (new entries, exits, vote shifts)
      3. Stale data check (signals > 36h old)
      4. Outputs status suitable for cron delivery

Monitor cron (every 6 hours) — check_alerts.py standalone
  - Runs check_alerts.py as no_agent script
  - Delivers output to local job log every 6 hours
```

### Files

- `production/generate_signals.py` — Daily signal computation
- `production/execute_trades.py` — Position sizing and execution
- `production/trade_logger.py` — Trade history and equity tracking
- `production/check_alerts.py` — Drawdown/signal/staleness alerts
- `production/monitor_status.py` — Dashboard (equity, drawdown, P&L)
- `production/run_cycle6_full.sh` — Full daily pipeline script
- `production/strategies/` — Strategy module with BaseStrategy.
strategies/tsmom.py
- `production/trade_history.json` — Running equity curve
- `production/alert_log.json` — Rolling alert log

### Why not a Freqtrade-native strategy?

The research portfolio uses 20% NAV sleeves with continuous rebalancing. Freqtrade simulates individual trades with entry/exit prices, slippage, and $50 stake increments. These are fundamentally different simulation engines — the Freqtrade backtest on the same period showed -22.9% while the research pipeline showed +33.5% CAGR. The daily signal generator preserves the research methodology faithfully.

### Live trading readiness

- Dry-run: fully functional (signals + position sizing + monitoring)
- Live: needs CCXT trade execution wired in `execute_trades.py`
- Pre-flight checklist before going live:
  - Freeze one canonical research commit
  - Add stale-signal checks and failed-download handling
  - Add portfolio-level exposure cap enforcement
  - Run 2+ weeks dry-run with logged expected-vs-actual positions

## Independent Review Pattern
- Before each gated commit, dispatch two independent subagents:
  1. Specification/causality reviewer — verifies against frozen protocol
  2. Code quality/adversarial reviewer — finds logic errors, security concerns
- Both must return APPROVE for the exact staged tree + patch SHA-256
- Any source change invalidates the review — re-dispatch after fixes

## Parameter Optimization Approach

When tuning strategy parameters (vol target, OI divergence, funding fade thresholds), use this approach:

1. **Directly edit the constants in the source file**, then run the experiment once in-process. This is faster and more reliable than subprocess sweeps on Windows.

2. Do NOT use `setattr(module, 'CONSTANT', value)` for parameter sweeps in a single process — the experiment runner has internal state that corrupts between runs.

3. Do NOT use subprocess-based sweeps (`subprocess.run(['python', ...])`) on Windows — each subprocess pays a ~30s cold-import penalty (pandas, numpy, pyarrow) and the total time for a 13-run sweep becomes prohibitive.

4. **Python mutable-default-arg pitfall:** When functions use module-level constants as default parameter values — e.g. `def compute_funding_fade(funding_series, percentile: float = FUNDING_FADE_PERCENTILE)` — the constant is EVALUATED AT FUNCTION DEFINITION TIME, not at call time. So `setattr(module, 'FUNDING_FADE_PERCENTILE', new_value)` before calling the function does NOT affect the default. The fix: change the signature to `percentile: float | None = None` and add `if percentile is None: percentile = FUNDING_FADE_PERCENTILE` inside the function body, so the module attribute is looked up at call time. See `references/parameter-sweep-approach.md` for the full recipe and code.

5. **Optimization results (July 2026):** The winning one-shot config uses `VOLATILITY_TARGET = 0.20` and `OI_DIVERGENCE_REDUCTION = 1.0` (disabled). This produced the first positive C-minus-B ever at +0.17% (vs -5.6% at default vol=0.40/OI=0.50). CAGR was essentially unchanged at +64.1%. The OI divergence signal at 0.50 was the primary drag — it fires ~46-50% of trading days and the reduction cost exceeded the risk reduction benefit in 2024's strong trend. Lower vol target reduces the opportunity cost of funding fade. Results saved to `research/cycle6_results.json` (commit 524c0f4).

6. **Per-symbol concentration cap (MAX_CONCENTRATION = 0.40) was the single biggest improvement.** The dropout test showed SOL drove ~73% of portfolio returns (CAGR dropped 64% → 17% when SOL was removed). Adding a concentration cap in the portfolio aggregation (`run_cycle6_experiment.py`'s `_cap()` function) capped any single symbol at 40% of NAV and renormalized the remaining weight. Result: CAGR improved from +64% to +110%, Sharpe from 0.678 to 0.753. Implementation: a `_cap(df)` function that clips per-symbol weights, renormalizes, and applies via weighted sum — applied to both the combined NAV and the C-minus-B sleeve comparison.

7. **Hysteresis regime filter replaces binary threshold.** The original binary filter (2x threshold → 0 or 1) never fired. Replaced with a hysteresis version with four parameters:
   - `threshold_entry = 1.3` — vol ratio at which exposure reduces
   - `threshold_exit = 1.1` — vol ratio at which exposure restores
   - `scale_down = 0.50` — exposure multiplier during elevated vol
   - `scale_crash = 0.25` — exposure multiplier when ratio exceeds 2.0
   - The filter uses Python state machine (enter reduced when >1.3, stay reduced until <1.1, crash at >2.0)
   - Note: the Python for-loop is slow (~2x longer experiment runtime on Windows). If performance matters, vectorize with pandas.

8. **Final proven config (all findings integrated):**
   | Parameter | Value | Rationale |
   |-----------|-------|-----------|
   | VOLATILITY_TARGET | 0.15 | Lower vol = smaller positions, less DD |
   | OI_DIVERGENCE_REDUCTION | 1.0 (disabled) | OI divergence was net negative at any threshold |
   | MAX_CONCENTRATION | 0.40 | Per-symbol cap prevents SOL dominance |
   | REGIME_FILTER | Hysteresis (enter=1.3, exit=1.1) | Partial reduction, not binary shutdown |
   | MULTI_SIGNAL_FADE | Active | Wired in build_targets_c6, adds marginal +0.68% |
   | CAGR (2021-2024) | +108.7% | Post-optimization |
   | Sharpe | 0.759 | Post-optimization |
   | Max DD | 93.5% | Remains the critical weakness |
   | C-B | +0.294% | Confirmed: C overlay is noise across IS/OOS/filter tests |

9. **C overlay (funding fades, OI divergence) is not confirmed as additive.** Across three validation tests, C-B was never consistently positive:
   - Walk-forward (2024 OOS): C-B = -1.60% (inconclusive within ±2% noise band)
   - Expanding window: C-B positive in only 4/7 windows (improving trend from 2023 onward)
   - Multiple thresholds tested (OI=0.50, 0.85, 1.0): none produced reliable positive C-B
   - Bootstrap CI (95%): CAGR [-25.9%, +489.7%] — crosses zero, not statistically significant
   - **Production runs the B sleeve only** (trend + vol), which is the proven edge

10. **Codex analysis final verdict: NEEDS FIXES.** Codex identified 4 actionable issues after reviewing all results:
   - Vol target too high → reduced from 0.20 to 0.15
   - Binary regime filter ineffective → replaced with hysteresis
   - Production duplicated formulas → switched to research imports
   - Position sizing too simple → switched to equity-based

11. **Two-pass NAV-based drawdown stop** — portfolio-level drawdown protection using real NAV (not target proxy). First pass runs simulate_sleeves WITHOUT protection; combined NAV drawdown is computed from the first pass; dd_multiplier series is generated with hysteresis (25% reduce/40% exit/10% recover); second pass re-runs simulate_sleeves WITH dd_multiplier. Result: marginal DD reduction (93.5% → 92.0%) — TS MOM in crypto has 90%+ drawdowns inherent to the strategy. Target-proxy DD (average target_b) does NOT work because SMAs stay high during crashes. See `references/two-pass-drawdown-stop.md`.

12. **Subagent timeout limit for long experiments** — delegate_task subagents have a 600s (10 min) hard timeout. Experiments running 5-8+ min per run will time out. Workaround: run experiments directly as background terminal processes instead of dispatching as subagents.

13. **Consistent import paths for research package** — the experiment runner uses mixed `from research import` (package) and `from run_cycle5_experiment import` (relative) styles. Add `research/__init__.py` and use the `research.` prefix everywhere to allow importing from the project root without chdir tricks.

## Pitfalls
- **Derivatives feature cache must be joined into the engine — building it is not enough.** Cycle 5's cache (4,499 archives, 1.38M rows) was fully built but never passed to `build_targets()`, so `veto_active` was always None and C ≡ B. Always trace the data flow: cache loaded → cache filtered → cache joined to decision timestamps → derived signals computed → fed into `build_targets*()` as a Series.
- **Independent variant NAV in simulate_sleeves — do NOT share cumulative NAV.** Each variant (a, b, c) must track its own separate cumulative NAV. If you compute `prev_nav = result['nav'].iloc[t-1]` and then add each variant's sleeve_value to the same `result['nav']`, later variants get progressively larger base allocations. This creates a systematic upward bias for C vs B that produces false positive C-minus-B signals. Fix: each variant computes its own `variant_nav[t] = sleeve_value` independently, then Total NAV = sum of all 5 independent sleeve NAVs at the end. Verify: when all targets are identical, all sleeve values must be identical to machine precision.
- **False positive detection rule:** Before computing any C-minus-B metric, verify that when the differentiating feature (funding fade, veto flag, etc.) is set to its neutral value (fade=1.0, veto=False), C and B produce identical sleeve values. A non-zero C-minus-B with neutral features is a bug, not a signal.
- **OI divergence and multi-signal fade are now wired and tested** — `build_targets_c6()` in `cycle6_backtest.py` accepts `oi_divergence_factor` and `multi_signal_fade` as optional Series params. Both are computed in `run_cycle6_experiment.py:compute_per_pair_signals()` and `run_cycle7_experiment.py:compute_per_pair_signals_c7()`. The `join_feature_cache_to_daily()` returns `oi_change_{symbol}` columns consumed by both. Premium duration remains the only untested signal.
- **Binance 2024 OI archives have timestamp seconds drift** — about 9% of daily archives (across all 5 symbols) have OI `create_time` values with 1-5 second offsets (e.g. `02:10:01` instead of `02:10:00`). `_parse_metrics_create_time` in `cycle5_feature_cache.py` now truncates seconds/microseconds to zero instead of raising `ValueError`. If you add a new parser for Binance daily archives, handle the seconds drift similarly — only the 5-minute minute alignment is semantically meaningful.
- **Binance 2024 daily OI archives may include records from adjacent days** — some daily ZIPs contain records whose `create_time` falls on the next calendar day (e.g. 2024-09-02 records inside the 2024-09-01 archive). `normalize_open_interest_records` now `continue`s past these instead of hard-erroring, since the correct day's archive will produce identical rows on its own build. This is a 2024-only behavior change — 2021-2023 archives always have single-day records.
- **Binance 2024 OI data uses `0E-16` instead of `0E-8` for some zero OI entries** — `_parse_open_interest` had an exact match `value != "0E-8"` that rejected `0E-16`. Switched to regex `r"0E-\d+"` to accept any zero-exponent notation. Both `Decimal("0E-16")` and `float("0E-16")` produce `0.0` correctly — this is purely a string-pattern match issue, not a semantics change. Test: `_parse_open_interest("0E-16") == 0.0`.
- **Date-boundary skip must precede year/timestamp validation** — when a daily archive has cross-date records (e.g. a 2025-01-01 timestamp in the 2024-12-31 archive), the date-boundary check (`measurement_time.date != source_archive_date → continue`) MUST run BEFORE `_require_development_timestamp`. Otherwise a next-year record gets rejected by the year check before the skip can filter it. In `normalize_open_interest_records`, the order is now: (1) `_parse_metrics_create_time`, (2) date comparison + continue, (3) `_require_development_timestamp`. Apply this pattern in any new parser that filters records by source-archive date.
- **Full-cache builder (`_build_cycle5_feature_cache_locked`) refuses to overwrite existing artifacts.** If a 2021-2023 cache already exists, you cannot run `--build --end 2024-12-31` directly — it will raise `FileExistsError`. Use the incremental approach via `python -B research/build_2024_cache.py` — builds 2024 into a separate feather file, combines with the existing cache, and tests signals in one pass.
- **2024 extension breaks ~12 tests in `test_cycle5_feature_cache.py`** — extending `_DEVELOPMENT_END` from 2023 to 2024 causes test failures in a predictable pattern. Every test that hardcodes year=2024 as "out of range" or uses `available_at` boundary-crossing timestamps (e.g. 2023-12-31 23:55 → available_at = 2024-01-01) needs updating. The fix pattern: change 2024 to 2025 in parametrized year lists, and update cross-window timestamps to push into 2025. Also update `_metrics_source_url(year=2024)` → `year=2025` in tests that expect URL rejection. The total source archive count increases from 4,499 to 6,449 (added 2024 funding/premium: +60 each, OI: +1,830). Run `python -m pytest tests/ -x --ignore=tests/test_cycle2_mtf_strategies.py` to catch all.
- **`compute_multi_signal_fade()` expects its first argument to be a funding percentile (0-1), not the raw funding rate.** The parameter is named `funding_pctile` to signal this, but it's easy to accidentally pass the raw `funding_series` (values like 0.0001). If you do, threshold comparisons like `funding_pctile > 0.80` will always be False and the function silently returns all 1.0s (no effect). Compute the percentile via `funding_series.rolling(window=365, min_periods=60).rank(pct=True)` before passing.
- **`simulate_sleeves()` now discovers sleeve variants dynamically** from `target_*` columns instead of hardcoding `("a", "b", "c")`. Any target column (except `target_p` and `target_pv`) gets its own sleeve. This is backward-compatible for C6 (a/b/c) and automatically supports C7's `target_d`. If you add a new target variant in the future, it will be simulated without modifying `simulate_sleeves` — just ensure the variant column is present in the targets DataFrame and the NAV sum includes it.
- **Bootstrap Sharpe must be annualized with `np.sqrt(365)` for comparability with point estimates.** The block bootstrap returns daily log returns. Computing `mean / std` on daily returns gives the daily Sharpe (~0.03 for this strategy), not the annualized Sharpe (~0.67). Without `np.sqrt(365)`, the bootstrap CI will be ~20x too narrow, implying false statistical significance. Apply the `np.sqrt(365)` factor AFTER computing the per-replicate daily Sharpe.
- Symbol path convention: OKX data uses underscore (`BTC_USDT-1h.feather`), not hyphen (`BTC-USDT`)
- Data extends past 2023 — must explicitly filter to development period
- Non-retryable transport failures (certificate, permanent DNS, EINVAL) must not be retried
- HTTPError response bodies must be closed via `exc.close()`, not just discarded
- Lock files must catch BaseException (not just OSError) to handle KeyboardInterrupt
- Temp files in `_atomic_write_bytes` need `Path(temporary.name)` assigned before write operations
- `assert x is True/False` fails on pandas np.True_/np.False_ — use `bool(x)` or `==`
- `pd.date_range` is tz-naive by default — must pass `tz='UTC'`
- `ChainedAssignmentError` in pandas Copy-on-Write — use `.loc[row, col]` not `[col].iloc[row]`
- **Python for-loops over pandas Series are 10-100x slower than vectorized operations on Windows.** The hysteresis regime filter uses `for value in ratio:` to implement state-machine logic (entry=1.3, exit=1.1, with crash detection). On 1461 daily rows × 5 symbols, this adds ~2-5 minutes per experiment run. On Linux/macOS this is less noticeable. If the experiment runtime becomes a bottleneck, rewrite the state-machine with `np.select()` or `pd.cut()` and boolean masks. If max drawdown is the primary metric, accept the slower Python version until the filter is validated.
