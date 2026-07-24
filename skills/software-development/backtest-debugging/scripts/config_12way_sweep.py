"""
12-way config sweep: 3 vol_targets x 2 regime filter states x 2 DD stop states.
Run this when you need to pick a final config for a vol-scaled TS MOM strategy.
Adapt the experiment function to match your backtest engine.
"""
import numpy as np, pandas as pd

def run_config(vol_target, use_regime, use_dd_stop):
    """Placeholder — replace with actual backtest engine call.
    Returns dict with CAGR, Sharpe, MaxDD."""
    # YOUR BACKTEST ENGINE CALL HERE
    # e.g.: c6.VOLATILITY_TARGET = vol_target
    #       port = compute_portfolio(vol_target, use_regime, use_dd_stop)
    #       return metrics(port)
    raise NotImplementedError("Replace with your backtest engine")

def metrics(port):
    log_r = np.log(port / port.shift(1)).replace([np.inf, -np.inf], np.nan).dropna()
    cagr = float(np.exp(np.mean(log_r) * 365) - 1)
    sharpe = float(np.mean(log_r) / np.std(log_r, ddof=1) * np.sqrt(365))
    peak = port.expanding().max()
    dd = ((peak - port) / peak).max()
    return {"cagr": cagr, "sharpe": sharpe, "dd": dd}

# Full factorial sweep
vol_targets = [0.20, 0.25, 0.30]
regime_options = [("no RF", False), ("RF on", True)]
dd_options = [("no DD", False), ("DD on", True)]

results = []
for vt in vol_targets:
    for rf_label, rf_val in regime_options:
        for dd_label, dd_val in dd_options:
            name = f"vt={vt:.2f} {rf_label} {dd_label}"
            m = run_config(vt, rf_val, dd_val)
            m["name"] = name
            results.append(m)
            print(f"{name}: CAGR={m['cagr']*100:.1f}% DD={m['dd']*100:.1f}% Sharpe={m['sharpe']:.2f}")

# Rank by Sharpe
results.sort(key=lambda r: r['sharpe'], reverse=True)
print("\nRank | Config | CAGR% | Sharpe | MaxDD%")
for rank, r in enumerate(results, 1):
    print(f"{rank:>4} | {r['name']:<30} | {r['cagr']*100:>6.2f} | {r['sharpe']:>5.2f} | {r['dd']*100:>6.1f}")
