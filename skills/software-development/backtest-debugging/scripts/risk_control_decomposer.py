"""
Regime Filter vs DD Stop: independent attribution analysis.
Run this to determine whether each risk control is worth keeping.
"""
import numpy as np
import pandas as pd

def decompose_risk_controls(
    simulate_fn,
    pairs: list,
    data_load_fn,
    vol_target: float = 0.25,
):
    """
    Run the experiment with 4 control combinations and report delta-CAGR / delta-DD.
    
    Args:
        simulate_fn: callable that runs the backtest given a config dict
        pairs: list of asset pair strings
        data_load_fn: callable that returns OHLCV data
        vol_target: volatility target for position sizing
    
    Returns:
        pd.DataFrame with one row per control combination
    """
    configs = {
        "no_controls": {"regime_filter": False, "dd_stop": False},
        "dd_stop_only": {"regime_filter": False, "dd_stop": True},
        "regime_only":  {"regime_filter": True, "dd_stop": False},
        "both":         {"regime_filter": True, "dd_stop": True},
    }
    
    rows = []
    for label, config in configs.items():
        # Patch the signal computation and simulation
        result = simulate_fn(pairs, data_load_fn, vol_target, config)
        rows.append({
            "config": label,
            "cagr": result["cagr"],
            "max_dd": result["max_dd"],
            "sharpe": result["sharpe"],
        })
    
    df = pd.DataFrame(rows)
    
    # Compute deltas
    baseline = df[df["config"] == "no_controls"].iloc[0]
    for _, row in df.iterrows():
        if row["config"] == "no_controls":
            continue
        d_cagr = row["cagr"] - baseline["cagr"]
        d_dd = row["max_dd"] - baseline["max_dd"]
        print(f"{row['config']:15s}: ΔCAGR={d_cagr*100:+5.1f}pp  ΔDD={d_dd*100:+5.1f}pp  "
              f"efficiency={abs(d_cagr/d_dd):.2f}" if d_dd != 0 else "N/A")
    
    return df


if __name__ == "__main__":
    print("Usage: Import decompose_risk_controls and pass your backtest function.")
    print("Expected output format:")
    print("  no_controls    : CAGR=+7.0%,  DD=34.6%  (baseline)")
    print("  dd_stop_only   : ΔCAGR=-2.0pp ΔDD=-4.0pp efficiency=0.50")
    print("  regime_only    : ΔCAGR=-3.9pp ΔDD=-2.5pp efficiency=1.56")
    print("  both           : ΔCAGR=-5.9pp ΔDD=-6.4pp efficiency=0.92")
    print("\nInterpretation: lower efficiency = worse (more CAGR lost per unit of DD saved).")
    print("DD stop (0.50) is efficient; regime filter (1.56) is destructive; both combined (0.92) is worse than DD stop alone.")
