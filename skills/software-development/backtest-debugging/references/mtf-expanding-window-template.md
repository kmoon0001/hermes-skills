# MTF Expanding Window Validation — Template

## When to use

After any overlay (MTF filter, regime filter, funding fade, OI divergence) shows
>2pp DD reduction in full-period results. Run expanding windows to verify the
DD reduction is structural (across ALL regimes) rather than concentrated in one crash event.

## Template script pattern

```python
"""<Overlay Name> — Expanding Window Validation."""
import sys, json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research import cycle6_backtest as c6
from research import cycle5_backtest as c5

# 7 expanding windows
WINDOWS = [
    ("W1  (1yr)",   "2021-01-01 00:00", "2021-12-31 23:00"),
    ("W2  (1.5yr)", "2021-01-01 00:00", "2022-06-30 23:00"),
    ("W3  (2yr)",   "2021-01-01 00:00", "2022-12-31 23:00"),
    ("W4  (2.5yr)", "2021-01-01 00:00", "2023-06-30 23:00"),
    ("W5  (3yr)",   "2021-01-01 00:00", "2023-12-31 23:00"),
    ("W6  (3.5yr)", "2021-01-01 00:00", "2024-06-30 23:00"),
    ("W7  (4yr)",   "2021-01-01 00:00", "2024-12-31 23:00"),
]

def main():
    for label, start, end in WINDOWS:
        # Compute B-only baseline for this window
        baseline = simulate_window(start, end)
        # Apply overlay to the same window
        overlay = apply_overlay(start, end)
        # Compare
        print(f"  {label}: B={baseline.cagr*100:+.1f}% DD={baseline.max_dd*100:.1f}%  "
              f"Overlay={overlay.cagr*100:+.1f}% DD={overlay.max_dd*100:.1f}%  "
              f"ΔCAGR={(overlay.cagr-baseline.cagr)*100:+.1f}% ΔDD={(overlay.max_dd-baseline.max_dd)*100:+.1f}pp")
```

## Decision rubric

| Pattern | Verdict |
|---------|---------|
| DD reduction > 2pp in bull-only windows (W1-W2) | Structural — ACCEPT |
| DD reduction < 2pp until crash enters (W3+) | Regime-dependent — REJECT (crash-timing one event) |
| DD reduction consistent across ALL windows | Structural — worth the CAGR cost |
| No DD reduction in any window | Noise — REJECT |

## Cycle 6 MTF example (2021-2024)

MTF 4h confirmation showed -2.3% CAGR, +0.13 Sharpe, -8pp DD in full-period. Expanding windows:

| Window | B CAGR | B DD | MTF CAGR | MTF DD | ΔDD |
|--------|:------:|:----:|:--------:|:------:|:---:|
| W1 1yr | +35.3% | -9.4% | +13.5% | -9.9% | -0.5pp |
| W2 1.5 | +19.9% | -12.1% | +7.7% | -13.6% | -1.5pp |
| W3 2yr | +6.7% | -23.8% | +2.3% | -16.9% | +6.9pp |
| W4 2.5 | +5.3% | -24.3% | +3.2% | -17.1% | +7.3pp |
| W5 3yr | +18.7% | -25.0% | +14.1% | -17.1% | +8.0pp |

**Verdict: REJECTED.** The entire -8pp DD reduction comes from the 2022 bear market. In bull-only windows (W1-W2), MTF provides zero DD benefit while destroying 12-22% CAGR. The DD reduction is not structural — it crash-times one event.
