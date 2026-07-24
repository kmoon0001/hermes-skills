"""
Per-sleeve decomposition script for backtest debugging.
Run this when combined portfolio metrics seem implausible.
It decomposes the aggregate NAV into per-sleeve contributions
and identifies which sleeve drives the combined metric.

Usage: python p_sleeve_dominance.py
Requires: backtest engine with simulate_sleeves output
"""
import numpy as np
import pandas as pd
from pathlib import Path

def decompose_portfolio(
    results: list[pd.DataFrame],
    sleeve_names: list[str],
    max_concentration: float = 0.40,
) -> dict:
    """Decompose portfolio-level metrics per sleeve.
    
    Args:
        results: list of DataFrames from simulate_sleeves, one per asset
        sleeve_names: e.g. ['a', 'b', 'c', 'p', 'pv']
        max_concentration: per-asset weight cap (default 0.40)
    
    Returns:
        dict with per-sleeve and combined metrics
    """
    def cap_nav(df):
        d = df.ffill().bfill().fillna(1.0)
        t = d.sum(axis=1)
        w = d.div(t, axis=0).clip(upper=max_concentration)
        w = w.div(w.sum(axis=1), axis=0)
        return (d * w).sum(axis=1)
    
    report = {}
    
    # Per-sleeve metrics
    for sleeve in sleeve_names:
        sleeve_navs = pd.DataFrame()
        for i, r in enumerate(results):
            col = f"sleeve_{sleeve}"
            if col in r.columns:
                sleeve_navs[f"s{i}"] = r[col]
        if sleeve_navs.empty:
            continue
        sleeve_navs = sleeve_navs.ffill().bfill().fillna(0.0)
        sleeve_total = cap_nav(sleeve_navs)
        final_val = sleeve_total.iloc[-1]
        sleeve_peak = sleeve_total.expanding().max()
        sleeve_dd = ((sleeve_peak - sleeve_total) / sleeve_peak.where(sleeve_peak > 0, 1.0)).max()
        report[f"sleeve_{sleeve}"] = {
            "final_nav": float(final_val),
            "max_dd": float(sleeve_dd),
        }
    
    # Combined NAV (all sleeves)
    combined = sum(
        pd.DataFrame({f"s{i}": r.get(f"sleeve_{s}", 0) for i, r in enumerate(results)})
        for s in sleeve_names
    )
    combined = combined.ffill().bfill().fillna(1.0) if isinstance(combined, pd.DataFrame) else combined
    # Actually for per-sleeve combined we do it per-sleeve and sum the cap_nav results
    all_nav = sum(
        cap_nav(pd.DataFrame({f"s{i}": r.get(f"sleeve_{s}", 0) for i, r in enumerate(results)}))
        for s in sleeve_names
    )
    # Reinterpret total portfolio NAV  
    combined_nav = all_nav  # approximate
    combined_peak = combined_nav.expanding().max()
    combined_dd = ((combined_peak - combined_nav) / combined_peak.where(combined_peak > 0, 1.0)).max()
    report["combined"] = {
        "final_nav": float(combined_nav.iloc[-1]),
        "max_dd": float(combined_dd),
    }
    
    # Find worst sleeve
    worst_sleeve = max(report, key=lambda k: report[k]["max_dd"] if k != "combined" else -1)
    report["worst_sleeve"] = worst_sleeve
    report["diagnosis"] = (
        f"Sleeve '{worst_sleeve}' has {report[worst_sleeve]['max_dd']*100:.1f}% maxDD "
        f"vs combined {report['combined']['max_dd']*100:.1f}%. "
        f"If worst >> combined, that sleeve is contaminating the aggregate."
    )
    return report


def quick_p_check(result: pd.DataFrame, pair: str) -> dict:
    """Quick one-pair P-sleeve dominance check."""
    sleeves = {}
    for v in ('a', 'b', 'c', 'p', 'pv'):
        nav = result[f'sleeve_{v}']
        final = nav.iloc[-1]
        peak = nav.expanding().max().iloc[-1]
        dd = (peak - final) / peak if peak > 0 else 0
        sleeves[v] = {'final': float(final), 'peak': float(peak), 'dd': float(dd)}
    
    combined_nav = result['nav']
    pct_p = result['sleeve_p'].iloc[-1] / combined_nav.iloc[-1] * 100
    
    return {
        'pair': pair,
        'sleeves': sleeves,
        'p_pct_combined': float(pct_p),
        'diagnosis': (
            f"P sleeve = {pct_p:.1f}% of combined NAV. "
            f"B sleeve maxDD = {sleeves['b']['dd']*100:.1f}%. "
            f"{'CONTAMINATION DETECTED' if pct_p > 50 else 'No P dominance'}"
        ),
    }


if __name__ == "__main__":
    print("This script requires simulate_sleeves output DataFrames.")
    print("Import and call decompose_portfolio(results, sleeve_names=['a','b','c','p','pv'])")
    print("Or quick_p_check(result, pair='BTC/USDT') for a single-pair check.")
    print("\nSee references/nav-stop-audit-findings.md for a full worked example.")
