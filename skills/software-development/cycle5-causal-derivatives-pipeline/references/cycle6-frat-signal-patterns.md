# Cycle 6 FRAT Signal Functions Reference

Standalone signal functions in `research/cycle6_backtest.py` that extend the Cycle 5 backtest engine. Each can be plugged into `build_targets_c6()` or the new `build_targets_c7()`.

## TS MOM Trend

```python
compute_trend_mom(closes, windows=(20, 50, 100), vote=2) -> pd.Series
```

Multi-lookback TS MOM vote. Each lookback: vote = 1 when `close > SMA(w)`. Trend on when votes >= vote. Returns boolean `trend_morn`.

**Warm-up:** 100 days. Warm-up is False (cash).

## Parkinson Volatility

```python
compute_parkinson_volatility(high, low, window=21) -> pd.Series
compute_vol_scale_from_parkinson(parkinson_vol, target=0.40) -> pd.Series
```

Parkinson HL: `σ = sqrt(1/(4*ln(2)*n) * Σ ln(high_i/low_i)^2) × sqrt(365)`. ~5x more efficient than std dev.

**Warm-up:** 21 periods. Returns NaN. Scale clipped to [0, 1].

## Funding Fade

```python
compute_funding_fade(funding_series, percentile=0.80, window=60, min_history=30) -> pd.Series
```

Percentile-rank funding fade. Above P80: `fade = max(0, 1 - (pct - 0.80) / 0.20)`. Returns [0, 1].

**Data unavailable:** Returns 1.0 when < 30 non-NaN values.

## Feature Cache Join

```python
join_feature_cache_to_daily(feature_df, decision_dates, decision_time_str="00:10") -> pd.DataFrame
```

Queries funding (age ≤12h), premium (age ≤2h), OI change (24h ratio) per symbol at each decision date.

## Target Builders

```python
build_targets_c6(trend_mom, vol_scale, funding_fade=None, oi_divergence_factor=None, multi_signal_fade=None) -> pd.DataFrame  # A, B, C, P, PV
build_targets_c7(trend_mom, vol_scale, oi_divergence_factor=None, multi_signal_fade=None) -> pd.DataFrame  # A, B, C, D, P, PV
```

- C6: `funding_fade` and `multi_signal_fade` are mutually exclusive — when multi_signal_fade is provided, it replaces funding_fade (since multi-signal fade already incorporates funding regime info). `oi_divergence_factor` is multiplicative on top of whichever fade is active.
- C7: target_c = B × oi_divergence_factor, target_d = C × multi_signal_fade. No funding_fade param — C7 uses multi-signal fade as the only fade mechanism.

## OI Divergence

```python
compute_oi_divergence_factor(trend_mom, oi_change, reduction=0.50) -> pd.Series
```

Aligned (both same direction): factor=1.0. Misaligned: factor=0.50.

## Multi-Signal Conditional Fade

```python
compute_multi_signal_fade(funding_pctile, oi_change=None, upper_pctile=0.80, lower_pctile=0.20) -> pd.Series
```

- Funding > upper + OI up → strong fade (0.50)
- Funding > upper + OI not up → weak fade (0.80)
- Funding < lower + OI down → boost (1.25)
- Otherwise → 1.0

## simulate_sleeves Warning

**The independent-NAV bug** — each variant (a, b, c) MUST track its own `variant_nav[t]` independently. If you compute `prev_nav = result['nav'].iloc[t-1]` and then add each variant to the same `result['nav']`, later variants get a larger base. This caused a false +6.3% C-minus-B that was entirely artifact.

**Prevention**: before computing any C-minus-B, set the differentiating feature to neutral (fade=1.0) and verify C === B to machine precision.
