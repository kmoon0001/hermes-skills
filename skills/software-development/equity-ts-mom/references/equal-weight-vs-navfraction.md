# Equal-weight vs NAV-fraction portfolio combination

**Verified 2026-07-20** against live yfinance data (8 ETFs: SPY, QQQ, IWM,
XLF, XLE, XLK, XLV, XLU; 2000-01-03 → 2026-07-17, 26.5y; cost 0.10%).

## The trap

`stocks/backtest.py:aggregate()` (and the `equity-ts-mom` skill's old
`aggregate_portfolio()`) combine sleeves by **NAV-fraction weighting**:

```python
df = df.div(df.iloc[0])
weights = df.div(df.sum(axis=1), axis=0).clip(upper=max_conc)
return (df * weights).sum(axis=1)
```

A sleeve that compounds faster gets a *larger* portfolio weight over time.
XLK grew ~15.9x vs XLV ~1.2x, so NAV-fraction silently tilts toward
winners — a momentum overlay dressed up as "equal-weight". This is why the
repo's headline `sma_252_binary` number is **+8.73%**, and why that number
is frequently mis-attributed as "SPY-only sma_252_binary".

A true single-ticker SPY `sma_252_binary` recomputed from scratch is
**+6.60%** — not +8.73%.

## Correct equal-weight (what "equal sleeve allocation" means)

```python
def combine_equal_weight(sleeves, max_conc=0.30):
    nav = pd.DataFrame(sleeves).ffill().bfill().fillna(1.0)
    nav = nav.div(nav.iloc[0])                       # rebaseline each to 1.0
    n = nav.shape[1]
    w = pd.DataFrame(1.0 / n, index=nav.index, columns=nav.columns)
    w = w.clip(upper=max_conc).div(w.sum(axis=1), axis=0)
    ret = nav.pct_change().fillna(0.0)
    wr = w.shift(1).reindex(ret.index).fillna(0.0)   # PRIOR-day weights
    combined_ret = (ret * wr).sum(axis=1)
    port = (1.0 + combined_ret).cumprod()
    port.iloc[0] = 1.0
    return port
```

Prior-day weights (`w.shift(1)`) matter: rebalancing to the current target
every day would charge a fictitious daily cost. Equal-weight is genuinely
1/N = 12.5% per sleeve for 8 tickers, so the 0.30 cap is inactive and
renormalization is a no-op — allocation is truly equal-weight.

## Verified baselines

| Combination                | CAGR   | Sharpe | MaxDD  | Calmar | Corr vs SPY (60d) |
|----------------------------|:------:|:------:|:------:|:------:|:-----------------:|
| Equal-weight (1/N)         | +6.16% | 0.587  | -18.6% | 0.331  | 0.875 |
| NAV-fraction (`aggregate`) | +8.73% | 0.622  | -27.5% | 0.317  | 0.881 |
| SPY-only sma_252_binary    | +6.60% | 0.566  | -28.7% | 0.230  | 1.000 |
| SPY B&H                    | +8.25% | 0.411  | -55.2% | 0.149  | 1.000 |

Equal-weight vs NAV-fraction confirmed to match a naive equal-weight
daily-return average (`ret.mean(axis=1).cumprod()`) to 0.01pp — so the
+6.16% is robust, not a recipe artifact.

## Honest takeaway for "equal sleeve allocation" tasks

- Report **+6.16% CAGR** for the 8-ETF equal-weight portfolio. It does
  **NOT** beat SPY B&H on CAGR (+8.25%), but beats it **2.2x on Calmar**
  and cuts max DD by **36pp** (-18.6% vs -55.2%).
- Only the NAV-fraction aggregate (+8.73%) beats SPY B&H on CAGR, and that
  is a different (momentum-tilted) methodology — never present it as
  equal-weight or as SPY-only.
- The repo's `results.json` "sma_252_binary +8.73%" and the
  `equity-ts-mom` skill's historical table +8.73% are METHOD A (aggregate),
  NOT SPY-only. Correct attribution matters when comparing strategies.

## Reproduction

`stocks/multiasset_sma252_run.py` (created this session) reuses
`backtest.py`'s `sig_sma_252_binary`, `simulate`, and `metrics`, applies
`combine_equal_weight`, and writes `stocks/multiasset_sma252_results.json`.
`_verify_combine.py` cross-checks the three combination methods. Run under
the venv: `stocks/.venv/Scripts/python.exe stocks/multiasset_sma252_run.py`.
