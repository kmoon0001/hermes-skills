# Freqtrade Simulation Engine Audit — July 2026

Full report at `audit_engine.md` in the freqtrade repo. This reference distills the methodology for the skill.

## Audit Scope

8-category systematic audit of freqtrade's simulation engine (`cycle5_backtest.py`, `cycle6_backtest.py`, `backtest_features.py`, `expanding_window.py`, `walkforward_validation.py`, `param_sweep.py`, `bootstrap_analysis.py`, `run_cycle7_experiment.py`).

## Key Findings

### MAJOR

| # | Finding | File:Line |
|---|---------|-----------|
| A5 | Duplicate `compute_metrics` in Cycle 9 — local copy diverges from canonical | `run_cycle9_experiment.py:219` |
| D1 | Module constant mutation via direct attribute assignment — non-reentrant | `expanding_window.py:56`, `walkforward_validation.py:38` |

**A5 details:** `run_cycle9_experiment.py` defines its own `compute_metrics_from_nav()` that is a near-identical clone of `cycle5_backtest.compute_metrics()`. This is the Pitfall 17 "duplicated function trap." A fix to the canonical version won't propagate to the local copy. Fix: delete the local copy and import from cycle5.

**D1 details:** `expanding_window.py` mutates `r6.START`, `r6.END`, `r6.BOOTSTRAP_REPLICATES` via attribute assignment. The script saves/restores values, but if `main()` throws between mutation and restore, the module stays mutated. `walkforward_validation.py` does the same WITHOUT restoring — permanently mutating `c6.cycle6_backtest.VOLATILITY_TARGET` for the process lifetime. Combined with `simulate_sleeves` reading module-level `SLEEVE_WEIGHT`, the simulation is non-reentrant. Fix: factory function pattern (pass params as function args, not setattr).

### MINOR

| # | Finding | File:Line |
|---|---------|-----------|
| A2 | Float equality for turnover check (`target_alloc != prev_target_alloc`) — fragile | `cycle5_backtest.py:231` |
| B3 | Funding fade `fillna(1.0)` — optimistic (no fade when derivatives data missing) | `cycle6_backtest.py:167` |
| B5 | `_cap()` `fillna(1.0)` — inflates early NAV for staggered-history portfolios | `run_cycle6_experiment.py:200` |
| MTF3 | Cycle 7 uses `result["nav"]` (all sleeves) instead of per-sleeve — cross-cycle comparison inconsistency | `run_cycle7_experiment.py:178` |

### Clean Bills of Health

These areas were verified as correct — useful to report so downstream readers know you checked them:

- **Cost handling:** Charged on turnover only, not daily full notional. Verified via cost=0 sanity check path. All active sleeves share identical cost logic.
- **RNG determinism:** All files use `np.random.default_rng(SEED)`. Zero legacy `np.random.seed()` calls. Fixed seeds guarantee reproducible bootstrap.
- **Timezone consistency:** UTC-aware enforced at every entry point via `_require_sorted_unique_datetime_index()`. No mixed tz-naive/tz-aware operations.
- **Index validation:** Sorted, unique, tz-aware checks at 10+ function boundaries (`compute_trend_mom`, `simulate_sleeves`, `build_targets`, etc.).
- **Two-pass DD stop:** Not active in production (disabled after testing). Archived code in `patch_twopass.py` (marked DANGER) and `test_dd_twopass.py` (marked STUB) — both documented as do-not-run.
- **Multi-timeframe alignment:** 4h filter in `backtest_features.py:211` uses `h4[h4.index <= date]` — no look-ahead. Correct causal alignment.

## Methodology Verification

This audit confirmed that the `backtest-debugging` skill's Pitfall catalog is comprehensive — every finding maps to an existing pitfall:

| Finding | Maps to |
|---------|---------|
| A5 (duplicate compute_metrics) | Pitfall 17 — duplicated function trap |
| D1 (setattr mutation) | Pitfall 10 — global state mutation |
| B3 (funding fade fillna) | Cat B — NaN fill policies |
| B5 (_cap fillna) | Pitfall 4 — _cap fillna artifacts |
| A2 (float equality) | New — not previously catalogued |
| MTF3 (nav field selection) | Pitfall 16 — NAV field selection |

**A2 (float equality for turnover)** is the one finding that doesn't map to an existing pitfall. The fix pattern: use `abs(delta) > 1e-12` threshold instead of `!=` for float comparisons in cost logic.

## Fix Priority Order

1. **D1 (MAJOR):** Refactor expanding_window/walkforward to use function parameters, not setattr
2. **A5 (MAJOR):** Delete local compute_metrics_from_nav, import canonical version
3. **A2 (MINOR):** Add tolerance to turnover float comparison
4. **B5 (MINOR):** Document fillna(1.0) policy; consider fillna(0.0) if adding staggered-history assets
