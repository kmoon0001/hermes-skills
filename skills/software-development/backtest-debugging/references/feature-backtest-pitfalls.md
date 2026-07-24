# Feature Backtest Pitfalls — July 2026

## P-Sleeve NAV Contamination

### The Bug

The `_simulate()` helper in `backtest_features.py` aggregates `result["nav"]` from `simulate_sleeves()`. This combined NAV includes ALL five sleeves (a, b, c, p, pv). The passive P-sleeve (buy-and-hold benchmark) grows to dominate portfolio weight during bull markets, inflating the combined NAV. Any feature tested against this baseline produces misleading comparisons.

**Real example (clean vs contaminated):**

| Feature | Contaminated Baseline | Contaminated Δ | Clean Baseline | Clean Δ |
|---------|:--------------------:|:--------------:|:--------------:|:-------:|
| correlation_sizing | 4.01% CAGR | -0.34% | **17.81%** | **-1.28%** |
| mtf_confirmation | 4.01% CAGR | -1.03% | **17.81%** | **-2.26%** |

The P-sleeve dominated the portfolio at 80%+ weight, compressing the baseline from 17.8% down to 4.0%. Feature comparisons against this compressed baseline were all wrong:
- Correlation sizing: accepted at -0.34% became rejected at -1.28%
- MTF confirmation: rejected at -1.03% became revisit-worthy at -2.26% (+0.13 Sharpe, -8pp DD)

### Detection

If a feature backtest shows baseline CAGR < 10% but the main experiment runner shows >15%, P-sleeve contamination is present. The signature: per-pair attribution shows P-sleeve at >50% of combined NAV weight.

### Fix

Replace all uses of `result["nav"]` with `result["sleeve_b"] / SLEEVE_WEIGHT` (B-only, normalized allocation). Also apply the same 40% concentration cap used in the main experiment runner for consistency:

```python
def _simulate(targets_dict):
    SLEEVE_WEIGHT = c5.SLEEVE_WEIGHT
    all_navs = []
    for pair in PAIRS:
        result = c5.simulate_sleeves(...)
        all_navs.append(result["sleeve_b"] / SLEEVE_WEIGHT)
    
    # Equal-weight with 40% concentration cap (matches experiment runner)
    df = pd.DataFrame({f"s{i}": s for i, s in enumerate(all_navs)})
    d = df.ffill().bfill().fillna(1.0)
    t = d.sum(axis=1)
    w = d.div(t, axis=0).clip(upper=0.40)
    w = w.div(w.sum(axis=1), axis=0)
    combined = pd.DataFrame({"nav": (d * w).sum(axis=1)})
    return c5.compute_metrics(combined)
```

## Expanding Window Validation for Feature DD Reduction

### The Pattern

When a feature shows DD improvement in a full-period backtest, the improvement may be concentrated in one market regime (e.g., the 2022 bear market). An expanding-window test determines whether the DD reduction is **structural** (present across all windows) or **regime-dependent** (only appears once a specific event enters the window).

### When to Run

- A feature shows ≥ 5 percentage point DD reduction vs baseline
- The DD reduction is the primary rationale for accepting the feature
- The backtest covers ≥ 3 years of data with distinct market regimes

### Script Pattern

```python
WINDOWS = [
    ("W1  (1yr)",   "2021-01-01", "2021-12-31"),
    ("W2  (1.5yr)", "2021-01-01", "2022-06-30"),
    ("W3  (2yr)",   "2021-01-01", "2022-12-31"),
    ("W4  (2.5yr)", "2021-01-01", "2023-06-30"),
    ("W5  (3yr)",   "2021-01-01", "2023-12-31"),
    ("W6  (3.5yr)", "2021-01-01", "2024-06-30"),
    ("W7  (4yr)",   "2021-01-01", "2024-12-31"),
]

for label, start, end in WINDOWS:
    baseline = _simulate_window(start, end)     # B-only baseline
    feature = _simulate_mtf_window(start, end)  # With feature applied
    cagr_delta = (feature["cagr"] - baseline["cagr"]) * 100
    dd_delta = (feature["max_drawdown"] - baseline["max_drawdown"]) * 100
    print(f"{label}: B={baseline['cagr']*100:+.1f}% DD={baseline['max_drawdown']*100:.1f}%  "
          f"MTF={feature['cagr']*100:+.1f}% DD={feature['max_drawdown']*100:.1f}%  "
          f"ΔCAGR={cagr_delta:+.1f}% ΔDD={dd_delta:+.1f}pp")
```

### Interpretation

| Pattern | Verdict |
|---------|---------|
| DD reduction appears in W1-W2 (bull-only) and persists through W7 | **ACCEPT** — structural |
| DD reduction only appears in W3+ (once bear market enters window) | **REJECT** — regime-dependent insurance, not signal quality |
| DD reduction is negative in some windows | **REJECT** — not even reliable |

### Real Case: MTF Confirmation Rejected

| Window | B CAGR | B DD | MTF CAGR | MTF DD | ΔCAGR | ΔDD |
|--------|:------:|:----:|:--------:|:------:|:-----:|:----:|
| 2021 bull | +35.3% | -9.4% | +13.5% | -9.9% | **-21.8%** | -0.5pp |
| +H1'22 | +19.9% | -12.1% | +7.7% | -13.6% | **-12.2%** | -1.5pp |
| +2022 | +6.7% | -23.8% | +2.3% | -16.9% | -4.4% | +6.9pp |
| +H1'23 | +5.3% | -24.3% | +3.2% | -17.1% | -2.1% | +7.3pp |
| 3yr | +18.7% | -25.0% | +14.1% | -17.1% | -4.7% | +8.0pp |
| 4yr | +17.8% | -25.0% | +15.6% | -17.1% | -2.3% | +8.0pp |

The -8pp DD improvement only appears once 2022 enters the window. In bull-only windows, MTF costs 12-22% CAGR for zero DD benefit. **REJECTED.**
