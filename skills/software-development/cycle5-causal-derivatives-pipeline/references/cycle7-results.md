# Cycle 7 Full Stack Results Reference

## Signal Stack

```
A = trend_mom (TS MOM 20/50/100d vote ≥2)
B = trend_mom × vol_scale (Parkinson 21d, 40% target)  
C = B × oi_divergence_factor (0.50 reduction when trend ↔️ OI disagree)
D = C × multi_signal_fade (conditional: strong/weak/boost based on funding + OI)
```

## Results (2021-2024, equal-weight 5-symbol portfolio)

| Metric | C6 (OI+Multi) | C7 (Full D) |
|--------|---------------|-------------|
| CAGR | +63.9% | +56.1% |
| Sharpe | 0.67 | 0.64 |
| Max DD | 87.6% | 85.9% |
| D-minus-B CAGR | -5.6% | -5.6% |
| D-minus-C CAGR | — | **+0.68%** |

## Key Findings

1. **OI divergence (0.50 reduction) is too aggressive** — fires on 46-50% of trading days in 2024. In strong trends, the signal is too sensitive. Suggested: 0.70-0.80 reduction for the next cycle.
2. **Multi-signal fade adds +0.68% on top of OI divergence** (D-minus-C). While small, this is positive — the conditional fade (funding extreme + OI confirmation) is in the right direction.
3. **Neither CAGR nor Sharpe is statistically significant** (95% CI spans zero on 4-year sample).
4. **87% max DD is high** — the 40% vol target may be too aggressive. Consider 25-30%.

## Bootstrap CIs (20k block replicates)

C6 CAGR: point +63.9%, 95% CI [-24.6%, +250.1%], SE 71.5%
C6 Sharpe: point 0.67, 95% CI [-0.37, 1.72], SE 0.54
C7 CAGR: point +56.1%, 95% CI [-24.5%, +219.4%], SE 63.4%
C7 Sharpe: point 0.64, 95% CI [-0.39, 1.70], SE 0.54

## Experiment Runners

- `research/run_cycle6_experiment.py` — main C6 experiment (OI+multi wired, bootstrap inline)
- `research/run_cycle7_experiment.py` — C7 experiment with D sleeve, D-minus-B and D-minus-C comparisons
- Both use combined 2021-2024 cache at `research/generated/cycle5_features_combined.feather`
- Both run 20000 block bootstrap replicates inline
- Block size = ⌈n^{1/3}⌉ per Politis & White (2004)
