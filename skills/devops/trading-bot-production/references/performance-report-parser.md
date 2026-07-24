# Performance Report — Parser Pattern

## The Bug

When `run_portfolio.py` calls the stock backtest subprocess and parses its output,
the naive parser grabbed ALL "CAGR:" / "Sharpe:" / "Max DD:" lines — including
the SPY benchmark section which comes AFTER the portfolio section. This produced
incorrect combined portfolio numbers (SPY's +8.3% CAGR instead of the strategy's
actual numbers).

## The Fix

Use **section-aware parsing**: detect the "PORTFOLIO (SMAxxx):" marker, then
stop at the "SPY BUY & HOLD:" marker. Only capture the FIRST occurrence of each
metric within the portfolio section.

```python
# BAD — grabs last match (usually SPY benchmark numbers)
for line in output.split("\n"):
    if "CAGR:" in line:
        metrics["cagr"] = float(line.split("+")[-1]...)

# GOOD — section-aware with first-match guard
in_portfolio = False
for line in output.split("\n"):
    if "PORTFOLIO (SMA" in line:
        in_portfolio = True
        continue
    if in_portfolio and ("SPY B&H" in line or "SPY BUY" in line):
        in_portfolio = False
        continue
    if not in_portfolio:
        continue
    if "CAGR:" in line and "cagr" not in metrics:  # first match only
        metrics["cagr"] = ...
    if "Sharpe:" in line and "sharpe" not in metrics:
        metrics["sharpe"] = ...
    if "Max DD:" in line and "max_dd" not in metrics:
        metrics["max_dd"] = ...
```

## Verification

After the fix, combined 70/30 portfolio correctly shows:
- Crypto: +17.5% CAGR (vt=0.40)
- Stocks: +8.8% CAGR (SMA252)
- Combined: +14.9% CAGR, Sharpe 1.028

Before the fix, it incorrectly showed:
- Stocks: +8.3% (SPY B&H numbers)
- Combined: +14.7% (using wrong stock input)

## Edge Cases Handled

1. **Single-snapshot stocks** (first week of paper trading): Shows equity but notes
   "Only 1 snapshot(s) — need more history for metrics" instead of crashing.
2. **Snapshots vs equity_history**: Stock data uses `snapshots` field, crypto uses
   `equity_history`. Parser handles both.
3. **Empty metrics**: If no data found, returns structured dict with "error" key.
