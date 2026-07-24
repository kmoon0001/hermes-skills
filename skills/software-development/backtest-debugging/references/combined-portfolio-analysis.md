# Combined Portfolio Analysis — Analytical Estimation

When you have standalone backtest metrics (CAGR, Sharpe, MaxDD) for two strategies but no daily NAV series aligned on the same grid, you can estimate combined portfolio metrics analytically. This is fast (<1 second) and accurate enough for feasibility analysis before committing to a full combined backtest.

## Technique

Given:
- Strategy A: CAGR_a, Sharpe_a → vol_a = CAGR_a / Sharpe_a
- Strategy B: CAGR_b, Sharpe_b → vol_b = CAGR_b / Sharpe_b
- Estimated correlation ρ (from historical data or domain knowledge)

Combined portfolio with weights w_a, w_b:
```
CAGR = w_a × CAGR_a + w_b × CAGR_b
Variance = w_a² × σ_a² + w_b² × σ_b² + 2 × w_a × w_b × ρ × σ_a × σ_b
Sharpe = CAGR / sqrt(Variance)
Est_DD = w_a × DD_a + w_b × DD_b  (conservative — actual DD will be lower from diversification)
```

## When to use

- Quick feasibility check: "should we even run a combined backtest?"
- Comparing multiple allocation splits (50/50, 60/40, 70/30) without re-running backtests
- The standalone backtests used different calendars (crypto 365 vs stocks 252) and aligning NAVs would require a grid-intersection fix (see Cross-Frequency NAV Combination in the parent skill)

## When NOT to use

- When daily NAV series ARE available — run the real combined backtest instead
- When correlation is unknown or changes regimes (crypto-stock correlation can spike during crashes)
- For final deployment decisions — this is a screening tool, not a substitute for actual combined backtest

## Example

```python
crypto = {"cagr": 0.178, "sharpe": 1.04, "dd": -0.250, "vol": 0.178/1.04}
stocks = {"cagr": 0.088, "sharpe": 0.70, "dd": -0.275, "vol": 0.088/0.70}
rho = 0.2

for wc in [0.3, 0.4, 0.5, 0.6, 0.7]:
    ws = 1 - wc
    cagr = wc * crypto["cagr"] + ws * stocks["cagr"]
    var = wc**2 * crypto["vol"]**2 + ws**2 * stocks["vol"]**2 + 2*wc*ws*rho*crypto["vol"]*stocks["vol"]
    vol = np.sqrt(var)
    sharpe = cagr / vol
    est_dd = wc * crypto["dd"] + ws * stocks["dd"]
    print(f"{wc:.0%}/{ws:.0%}: CAGR={cagr:.1%} Sharpe={sharpe:.3f} EstDD={est_dd:.1%}")
```

## Verification

After estimating, run the real combined backtest with aligned NAV series and compare. The analytical estimates should be within ±2pp CAGR and ±0.1 Sharpe of the real result. If they differ by more, the correlation assumption was wrong, or the NAV grids need the cross-frequency fix.
