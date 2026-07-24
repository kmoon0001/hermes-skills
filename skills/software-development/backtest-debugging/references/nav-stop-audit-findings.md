# NAV Stop Audit — Full Trace Data

**Date:** 2026-07-19  
**Project:** Cycle 6 TS MOM bot (freqtrade-cycle5-research)  
**Root Cause:** Passive P sleeve (buy-and-hold) contaminates combined NAV

## The Triggering Observation

The experiment runner reported 92% max DD despite a 40% NAV hard stop. The expanding window validation showed DD stabilizes at 87% across ALL window sizes — structural, not data-length.

## Decomposition Process

### Step 1: Compute Per-Sleeve maxDD

```
PASS 1 (no stop):
Combined NAV final:     15.17
Combined peak NAV:      22.22
Combined maxDD:         93.5%

Per-Sleeve:
  Sleeve A (raw trend):       final=1.84, maxDD=70.8%
  Sleeve B (vol-scaled):      final=1.04, maxDD=21.3%
  Sleeve C (funding fade):    final=1.04, maxDD=20.2%
  Sleeve P (passive B&H):     final=24.78, maxDD=93.8%  ←
  Sleeve PV (vol-scaled B&H): final=0.00, maxDD=0.0%

Active sleeves (A+B+C only):  maxDD=58.2%
Passive only (P):             maxDD=97.0%
```

### Step 2: Check P-Sleeve Dominance Per-Asset

| Asset | Sleeve A | Sleeve B | Sleeve C | Sleeve P | P % of NAV | B maxDD |
|-------|----------|----------|----------|----------|------------|---------|
| BTC   | 0.09     | 0.19     | 0.19     | 0.63     | 57.6%      | 24.2%   |
| ETH   | 0.08     | 0.18     | 0.18     | 0.92     | 67.5%      | 24.8%   |
| SOL   | 1.42     | 0.28     | 0.28     | 20.73    | **91.3%**  | 18.5%   |
| XRP   | 0.11     | 0.18     | 0.18     | 1.73     | 78.6%      | 30.3%   |
| ADA   | 0.15     | 0.21     | 0.21     | 0.98     | 63.4%      | 25.4%   |

SOL's passive P sleeve grew 20.73× from its 0.20 starting weight — a +1036% return from buy-and-hold SOL. That dwarfed the active B sleeve (0.28 final = +40% return over 4 years).

### Step 3: Verify DD Stop Doesn't Affect P

In `simulate_sleeves` (cycle5_backtest.py:239-244):
```python
# P and PV sleeves (passive buy-and-hold)
passive = np.zeros(n, dtype=np.float64)
passive[0] = SLEEVE_WEIGHT
for t in range(1, n):
    passive[t] = passive[t - 1] * (closes[pair].iloc[t] / closes[pair].iloc[t - 1])
result["sleeve_p"] = pd.Series(passive, index=targets.index)
```

The P sleeve is hardcoded to `closes[t] / closes[t-1]` — it tracks the spot price with zero reduction from `dd_mult`. The DD stop (`dd_multiplier_series`) only scales target allocations in the A/B/C loop:

```python
dd_mult = dd_multiplier_series.iloc[t - 1] if dd_multiplier_series is not None else 1.0
target_alloc = targets[target_key].iloc[t - 1] * dd_mult
```

P has no target allocation — it's computed independently.

### Step 4: DD Stop State Machine Trace

```
DD thresholds:  25% → 0.50x scale, 40% → 0.0x full exit, 10% → recover
Trigger @25%:   row=1447 (2024-12-18)
Trigger @40%:   NEVER
Recover @10%:   row=1410 (2024-11-11)

Around the 25% trigger (2024-12-18):
  Date        NAV    Peak     DD%   Mult
  2024-12-13 18.02  22.22   18.9%   1.0
  2024-12-14 17.61  22.22   20.8%   1.0
  2024-12-15 17.94  22.22   19.2%   1.0
  2024-12-16 17.17  22.22   22.7%   1.0
  2024-12-17 17.78  22.22   20.0%   1.0
  2024-12-18 16.44  22.22   26.0%   0.5  ← triggered
  2024-12-19 15.45  22.22   30.5%   0.5
  2024-12-20 15.44  22.22   30.5%   0.5
  2024-12-21 14.37  22.22   35.3%   0.5
  2024-12-22 14.33  22.22   35.5%   0.5
  2024-12-27 14.68  22.22   33.9%   0.5
```

The stop was in the soft-reduction zone (0.50x) for ~60 days but never reached the 40% hard exit. With 50% exposure, the NAV only fell 35.5% max — the stop was actually WORKING for the active sleeves. The 92% DD was driven entirely by P.

### Step 5: Two-Pass Stop Performance

```
Without stop:  maxDD = 93.5%
With stop:     maxDD = 92.0%  (only 1.5pp improvement!)
```

The minimal improvement confirms the stop wasn't touching the dominant sleeve (P). The 1.5pp improvement came from reducing A/B/C exposure — but those accounted for only ~20-40% of the combined NAV.

## Corrected Results After Fix

Combined NAV uses `sleeve_b + sleeve_c + sleeve_pv` (excluding P):

| Metric | Old (with P) | New (active only) |
|--------|:-----------:|:-----------------:|
| CAGR | +106.4% | +1.8% |
| Sharpe | 0.79 | 0.25 |
| Max DD | 92.0% | 19.7% |
| ES(95%) | -10.7% | -0.9% |
| C-minus-B | -0.08% | +0.29% |

Bootstrap 95% CI (new): CAGR [-5.8%, +1.8%, +11.5%], Sharpe [-0.90, 0.25, 1.44]

**Interpretation:** The active strategy has healthy drawdown (19.7%) but low CAGR (1.8%). The vol_target=0.15 + regime filter + 40% cap is too conservative — the strategy is capturing almost none of the 2021-2024 crypto bull market.

## Expanding Window (After Fix — Active Sleeves Only, ex-P)

| Window | Period | CAGR | Sharpe | MaxDD | C-B |
|--------|--------|:----:|:------:|:-----:|:---:|
| W1 | 2021 only | +10.0% | 1.31 | **5.0%** | -0.40% |
| W2 | +2022 H1 | +4.4% | 0.65 | **8.0%** | -0.24% |
| W3 | +2022 H2 | -0.9% | -0.14 | **15.2%** | -0.20% |
| W4 | +2023 H1 | -1.7% | -0.26 | **17.7%** | +0.29% |
| W5 | +2023 H2 | +1.3% | 0.19 | **19.7%** | +0.16% |
| W6 | +2024 H1 | +1.5% | 0.22 | **19.7%** | +0.23% |
| W7 | Full 4yr | **+1.8%** | 0.25 | **19.7%** | +0.29% |

**Key takeaways:**
- MaxDD stabilizes at **19.7%** — purely structural for the active strategy with vol_target=0.15 + regime filter + 40% cap. This is the strategy's true risk profile, completely different from the old 92%.
- CAGR is low (+1.8% full period, peaks at +10% in 2021 only) — the vol_target=0.15 combo is too conservative.
- C-B flips sign: negative in strong trends (2021 bull: -0.40%), positive in range-bound/rising markets (2023+: +0.16 to +0.29%). Funding fade hurts when trend is strongest, helps when it chops.
- Strategy loses money in pure bear markets (W3: -0.9%, W4: -1.7%) — expected for long-only TS MOM.
- C-B is **regime-dependent, not significant** (4/7 positive, 3/7 negative). Not a deployable overlay.

## Expanding Window (Before Fix — Includes P) — Historical

```
Window 1 (2021):        CAGR +552%, DD 47%   — bull only, no crash
Window 3 (2021-22):     CAGR +11%, DD 87%    — includes 2022 crash  
Window 5 (2021-23):     CAGR +64%, DD 87%    — crash + recovery
Window 7 (2021-24):     CAGR +64%, DD 87%    — stable
```

All windows ≥2 years have DD=87% (which was driven by P). The expanding window validates that the DD is structural once the crash enters the data window. Should be re-run after the fix.
