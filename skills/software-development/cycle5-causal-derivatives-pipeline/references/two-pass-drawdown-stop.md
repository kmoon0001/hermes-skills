# Two-Pass NAV-Based Drawdown Stop

## Problem

The Cycle 6 TS MOM strategy has ~93% max drawdown on 2021-2024 data. The strategy stays long through crashes because SMA(20/50/100) lookbacks are too slow to flip during a bear market.

## Goal

Cap portfolio max drawdown to ~40-50% by exiting positions when real NAV losses exceed a threshold.

## The Circular Dependency

Drawdown protection requires tracking NAV to detect losses, but NAV depends on the position targets that the drawdown stop is supposed to modify. You can't compute the stop multiplier without knowing the NAV, and you can't compute the NAV without the stop multiplier.

## Solution: Two-Pass Simulation

### Pass 1: Simulate Without Protection

Compute the full experiment once with `simulate_sleeves(dd_multiplier_series=None)`. Collect the combined portfolio NAV from all pairs.

```python
# First pass: no drawdown protection
all_results_pass1 = []
for pair, symbol, targets in all_targets:
    pair_opens = daily_opens[pair].reindex(targets.index, method="ffill")
    pair_closes = daily_closes[pair].reindex(targets.index)
    pr = simulate_sleeves(
        targets, pair_opens.to_frame(pair), pair_closes.to_frame(pair),
        pair=pair, cost=PRIMARY_COST,
    )
    all_results_pass1.append(pr)

# Compute combined NAV from pass 1
nav_df_1 = pd.DataFrame({f"s{i}": r["nav"] for i, r in enumerate(all_results_pass1)})
combined_nav_1 = _cap(nav_df_1)
```

### Compute dd_multiplier from Actual Drawdown

```python
peak = combined_nav_1.expanding().max()
dd = (peak - combined_nav_1) / peak.where(peak > 0, 1.0)

dd_mult_vals = []
reduced = False
for d_val in dd:
    if not np.isfinite(d_val):
        dd_mult_vals.append(1.0)
        continue
    if d_val > DD_HARD_STOP:
        reduced = True
        dd_mult_vals.append(0.0)
    elif d_val > DD_STOP_THRESHOLD:
        reduced = True
        dd_mult_vals.append(DD_SCALE_DOWN)
    elif reduced and d_val < DD_RECOVER_THRESHOLD:
        reduced = False
        dd_mult_vals.append(1.0)
    elif reduced:
        dd_mult_vals.append(DD_SCALE_DOWN)
    else:
        dd_mult_vals.append(1.0)

dd_mult_series = pd.Series(dd_mult_vals, index=combined_nav_1.index, name="dd_mult")
```

### Pass 2: Simulate With Protection

Re-run `simulate_sleeves` with the dd_multiplier applied:

```python
all_results = []
for pair, symbol, targets in all_targets:
    pair_opens = daily_opens[pair].reindex(targets.index, method="ffill")
    pair_closes = daily_closes[pair].reindex(targets.index)
    dd_aligned = dd_mult_series.reindex(targets.index).ffill().fillna(1.0)
    pair_result = simulate_sleeves(
        targets, pair_opens.to_frame(pair), pair_closes.to_frame(pair),
        pair=pair, cost=PRIMARY_COST,
        dd_multiplier_series=dd_aligned,
    )
    all_results.append(pair_result)
```

### simulate_sleeves Signature Change

Add an optional `dd_multiplier_series: pd.Series | None = None` parameter to `simulate_sleeves()`. When provided, each day's `target_alloc` is multiplied by the corresponding value:

```python
dd_mult = dd_multiplier_series.iloc[t - 1] if dd_multiplier_series is not None else 1.0
target_alloc = targets[target_key].iloc[t - 1] * dd_mult
```

## Cost

- `compute_per_pair_signals()` (expensive, 5-8 min): runs ONCE
- `simulate_sleeves()` (cheap, <10s per pass): runs TWICE
- Total: ~5-8 min per experiment (same as before for single-pass)

## Results with 25% / 40% / 10% Thresholds

| Metric | Without DD Stop | With DD Stop | Change |
|--------|-----------------|--------------|--------|
| CAGR | +108.7% | +106.4% | -2.3pp |
| Sharpe | 0.759 | 0.786 | +0.027 |
| Max DD | 93.5% | 92.0% | -1.5pp |
| C-B | +0.29% | -0.08% | -0.37pp |

## Why Improvement is Marginal

The 25% entry threshold means the portfolio has already lost 25% before the stop fires. The 50% scale-down still leaves half the capital exposed to further losses. In a 94% crypto crash, the NAV continues to drop even at reduced exposure because:
1. 25% loss is already locked in
2. Remaining 50% exposure continues to lose
3. The 40% hard stop fires at 40% loss, but by that point significant damage is done

To meaningfully cap DD (e.g., to 30-40%), thresholds would need to be:
- `DD_STOP_THRESHOLD = 0.15` (reduce at 15% DD)
- `DD_HARD_STOP = 0.30` (exit at 30% DD)
- `DD_SCALE_DOWN = 0.10` (reduce to 10% exposure)
- `DD_RECOVER_THRESHOLD = 0.05` (restore at 5% recovered)

But these would trigger on every normal crypto dip (10-20% corrections happen frequently), eating CAGR substantially.

## Key Pitfall: DON'T Use Target Proxy

Do NOT use the average target_b as a proxy for portfolio NAV to compute drawdown. The targets stay HIGH during a crash because the SMA(20/50/100) trend vote is slow to flip — it can take 3-6 months for enough daily closes to cross below the SMAs. By the time targets drop, the NAV has already lost 90%+. The proxy shows zero drawdown while the portfolio is being destroyed.

Always use the ACTUAL combined NAV from a first-pass simulation.

## Implementation History

- Initial attempt: per-variant drawdown stop in `simulate_sleeves` — didn't help because P and PV sleeves (40% of capital) were unprotected
- Second attempt: portfolio-level DD from target proxy — didn't work because targets don't reflect NAV
- Third attempt (final): two-pass simulation with real NAV — marginal improvement, confirms TS MOM drawdowns are structural and hard to mitigate programmatically
