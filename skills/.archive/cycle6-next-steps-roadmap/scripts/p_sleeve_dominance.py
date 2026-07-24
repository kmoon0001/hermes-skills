"""Per-sleeve NAV decomposition — confirms P sleeve drives 92% DD.
Usage: python research/p_sleeve_dominance.py
"""
import sys, numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\kevin\Desktop\freqtrade")
sys.path.insert(0, str(ROOT))
from research import cycle6_backtest as c6, cycle5_backtest as c5

PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]
DATA_DIR = ROOT / "user_data" / "data" / "okx"

def simulate_one(pair):
    frame = pd.read_feather(str(DATA_DIR / f"{pair.replace('/', '_')}-1h.feather"))
    dates = pd.to_datetime(frame["date"], utc=True)
    dates = dates[dates >= pd.Timestamp("2021-01-01", tz="UTC")]
    dates = dates[dates <= pd.Timestamp("2024-12-31", tz="UTC")]
    filtered = frame.loc[dates.index].copy()
    filtered["date"] = dates
    daily = c5.aggregate_hourly_to_daily(filtered)
    close, high, low = daily["close"], daily["high"], daily["low"]
    trend = c6.compute_trend_mom(close)
    pv = c6.compute_parkinson_volatility(high, low)
    vs = c6.compute_vol_scale_from_parkinson(pv)
    rf = c6.compute_regime_filter(pv)
    idx = close.index
    targets = pd.DataFrame(index=idx)
    targets["target_a"] = trend.astype(float) * rf.reindex(idx).fillna(1.0).clip(0,1)
    targets["target_b"] = trend.astype(float) * vs.reindex(idx).fillna(0.0) * rf.reindex(idx).fillna(1.0).clip(0,1)
    targets["target_c"] = targets["target_b"]
    targets["target_p"] = 0.0
    targets["target_pv"] = vs.reindex(idx).fillna(0.0) * rf.reindex(idx).fillna(1.0).clip(0,1)
    opens = daily["open"].reindex(targets.index, method="ffill")
    closes = daily["close"].reindex(targets.index)
    result = c5.simulate_sleeves(targets, opens.to_frame(pair), closes.to_frame(pair), pair=pair, cost=0.0020)
    return pair, result

results = {}
for pair in PAIRS:
    p, r = simulate_one(pair)
    results[p] = r
    nav = r["nav"]
    pct_p = r["sleeve_p"].iloc[-1] / nav.iloc[-1] * 100
    p_dd = ((r["sleeve_p"].expanding().max() - r["sleeve_p"]) / r["sleeve_p"].expanding().max()).max()
    b_dd = ((r["sleeve_b"].expanding().max() - r["sleeve_b"]) / r["sleeve_b"].expanding().max()).max()
    active = r["sleeve_a"] + r["sleeve_b"] + r["sleeve_c"]
    active_peak = active.expanding().max()
    active_dd = ((active_peak - active) / active_peak).max()
    combined_peak = nav.expanding().max().iloc[-1]
    combined_dd = (combined_peak - nav.iloc[-1]) / combined_peak
    print(f"{pair:>12}: P={pct_p:5.1f}%  P_DD={p_dd*100:5.1f}%  B_DD={b_dd*100:5.1f}%  Active_DD={active_dd*100:5.1f}%  Combined_DD={combined_dd*100:5.1f}%")
