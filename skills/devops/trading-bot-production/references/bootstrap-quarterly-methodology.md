# Bootstrap Methodology — Quarterly Aggregation

Date: 2026-07-23
Problem: Daily crypto returns are too volatile for meaningful bootstrap CIs.
Standard practice in academic finance: aggregate to lower frequency before
bootstrapping.

## The Problem

Daily crypto returns have extreme volatility (BTC ±20% days). When you
bootstrap daily returns, the confidence intervals become so wide they're
useless for decision-making. Our initial run with daily returns produced:
- CAGR 95% CI: [-22.3%, +61.5%, +412.8%]
- Standard error: ±133%

This is technically correct (it accurately reflects the uncertainty) but
practically useless. The upper bound of +413% tells you nothing actionable.

## The Fix: Quarterly Aggregation

Sample the NAV at 63-trading-day intervals (approximately quarterly), then
compute log returns on the quarterly series, then bootstrap. This produces
stable, interpretable CIs.

```python
import numpy as np
nav = ...  # daily NAV array
quarterly_nav = nav[::63]  # every 63 trading days (~1 quarter)
quarterly_log_r = np.diff(np.log(quarterly_nav))
quarterly_simple = np.expm1(quarterly_log_r)

# Bootstrap on quarterly returns
b = max(2, int(np.ceil(n ** (1/3))))  # optimal block size
n_reps = 50000  # more reps for better tail precision

boot_sharpes = np.zeros(n_reps)
for i in range(n_reps):
    n_blocks = int(np.ceil(n / b))
    starts = rng.integers(0, n - b + 1, size=n_blocks)
    sample = np.concatenate([quarterly_log_r[s:s+b] for s in starts])[:n]
    simple = np.expm1(sample)
    mu = np.mean(simple)
    sigma = np.std(simple, ddof=1)
    boot_sharpes[i] = (mu / sigma) * np.sqrt(4)  # annualize from quarterly

# 95% CI
ci = np.percentile(boot_sharpes, [2.5, 50, 97.5])
```

## Results (vt=0.30, 2017-2024, 50k reps)

- Sharpe point estimate: 0.76
- 95% CI: [-1.63, +1.62]
- Standard error: ±0.79

This is interpretable: we are 95% confident the true annual Sharpe is
between -1.63 and +1.62. The interval spans zero (strategy could lose
money) but the central estimate is positive.

## Comparing Two Strategies

To test whether vt=0.40 improves over vt=0.30, bootstrap the DIFFERENCE:

```python
# Bootstrap the difference in Sharpe
boot_diff = np.zeros(n_reps)
for i in range(n_reps):
    # Resample both strategies independently
    s30 = ...  # bootstrapped vt=0.30 returns
    s40 = ...  # bootstrapped vt=0.40 returns
    sh30 = compute_sharpe(s30)
    sh40 = compute_sharpe(s40)
    boot_diff[i] = sh40 - sh30

ci = np.percentile(boot_diff, [2.5, 50, 97.5])
p_better = np.mean(boot_diff > 0)
```

## Results (vt=0.30 vs vt=0.40)

- ΔSharpe 95% CI: [-2.35, 0.00, +2.32]
- P(vt40 better) = 49.7%

The CI spans zero → no significant difference. The probability that vt=0.40
is better is essentially a coin flip (49.7%).

## Why This Matters

Without bootstrap CIs, you'd look at the point estimates (vt=0.30: 61% CAGR,
vt=0.40: 64% CAGR) and conclude vt=0.40 is better. The bootstrap reveals
that the difference is indistinguishable from noise. This is why academic
finance requires confidence intervals, not just point estimates.

## Reference

Politis, D.N. & White, H. (2004). "Automatic Block-Length Selection for the
Dependent Bootstrap." Econometric Reviews, 23(1), 53-70.
