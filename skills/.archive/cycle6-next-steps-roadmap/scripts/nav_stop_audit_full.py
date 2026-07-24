"""Nav Stop Audit — full pipeline with detailed DD trace.

Usage: python research/nav_stop_audit_full.py

Loads hourly data, aggregates to daily, joins feature cache,
computes all signals (trend/vol/regime/funding/OI), simulates
pass 1 (no stop) and pass 2 (with stop), traces DD state machine.
"""
import sys, json, os, numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\kevin\Desktop\freqtrade")
sys.path.insert(0, str(ROOT))
from research import cycle6_backtest as c6, cycle5_backtest as c5

DD_HARD_STOP = 0.40; DD_STOP_THRESHOLD = 0.25; DD_SCALE_DOWN = 0.50
DD_RECOVER_THRESHOLD = 0.10; PRIMARY_COST = 0.0020; MAX_CONCENTRATION = 0.40
BOX = ROOT / "research" / "generated" / "cycle5_features_combined.feather"
DATA_DIR = ROOT / "user_data" / "data" / "okx"
PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT"]
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"]
SYMBOL_TO_PAIR = dict(zip(SYMBOLS, PAIRS))
START = "2021-01-01 00:00"; END = "2024-12-31 23:00"

def load_ohlcv_panels(data_dir, pairs, start=None, end=None):
    daily_opens, daily_closes, daily_highs, daily_lows = {}, {}, {}, {}
    for pair in pairs:
        path = data_dir / f"{pair.replace('/', '_')}-1h.feather"
        frame = pd.read_feather(path)
        dates = pd.to_datetime(frame["date"], utc=True)
        if start: dates = dates[dates >= pd.Timestamp(start, tz="UTC")]
        if end: dates = dates[dates <= pd.Timestamp(end, tz="UTC")]
        filtered = frame.loc[dates.index].copy(); filtered["date"] = dates
        daily = c5.aggregate_hourly_to_daily(filtered)
        daily_opens[pair] = daily["open"]; daily_closes[pair] = daily["close"]
        daily_highs[pair] = daily["high"]; daily_lows[pair] = daily["low"]
    return (pd.DataFrame(daily_opens), pd.DataFrame(daily_closes),
            pd.DataFrame(daily_highs), pd.DataFrame(daily_lows))

daily_opens, daily_closes, daily_highs, daily_lows = load_ohlcv_panels(DATA_DIR, PAIRS, START, END)
import pyarrow.feather as feather
feature_cache = feather.read_table(BOX, memory_map=True).to_pandas() if BOX.is_file() else pd.DataFrame()

# Compute signals for all pairs
all_targets = []
for symbol in SYMBOLS:
    pair = SYMBOL_TO_PAIR[symbol]
    if pair not in daily_closes.columns: continue
    close = daily_closes[pair].dropna()
    if len(close) < 100: continue
    trend = c6.compute_trend_mom(close)
    high, low = daily_highs[pair].reindex(close.index), daily_lows[pair].reindex(close.index)
    parkinson_vol = c6.compute_parkinson_volatility(high, low)
    vol_scale = c6.compute_vol_scale_from_parkinson(parkinson_vol)
    regime_filter = c6.compute_regime_filter(parkinson_vol)
    if len(feature_cache) > 0:
        symbol_cache = feature_cache[feature_cache["symbol"] == symbol].copy()
        joined = c6.join_feature_cache_to_daily(symbol_cache, close.index)
    else: joined = pd.DataFrame(index=close.index)
    funding_col = f"funding_rate_{symbol}"; multi_fade = None
    if funding_col in joined.columns and joined[funding_col].notna().sum() >= 30:
        fade = c6.compute_funding_fade(joined[funding_col]).reindex(close.index).fillna(1.0)
        oi_multi_col = f"oi_change_{symbol}"
        oi_change_multi = joined[oi_multi_col] if oi_multi_col in joined.columns else None
        if oi_change_multi is not None and oi_change_multi.notna().sum() >= 30:
            funding_pctile = joined[funding_col].rolling(window=365, min_periods=60).rank(pct=True).reindex(close.index)
            multi_fade = c6.compute_multi_signal_fade(funding_pctile, oi_change_multi).reindex(close.index).fillna(1.0)
    else: fade = pd.Series(1.0, index=close.index)
    idx = close.index
    trend_aligned = trend.reindex(idx).fillna(False); vol_aligned = vol_scale.reindex(idx).fillna(0.0)
    regime_aligned = regime_filter.reindex(idx).fillna(1.0).clip(0,1); fade_aligned = fade.reindex(idx).fillna(1.0)
    multi_fade_aligned = multi_fade.reindex(idx).fillna(1.0) if multi_fade is not None else None
    oi_col = f"oi_change_{symbol}"
    oi_div = pd.Series(1.0, index=idx)
    if oi_col in joined.columns and joined[oi_col].notna().sum() >= 30:
        oi_div = c6.compute_oi_divergence_factor(trend, joined[oi_col])
    oi_div_aligned = oi_div.reindex(idx).fillna(1.0)
    targets = c6.build_targets_c6(trend_aligned, vol_aligned, fade_aligned,
        oi_divergence_factor=oi_div_aligned,
        multi_signal_fade=multi_fade_aligned if multi_fade is not None else None,
        regime_filter=regime_aligned)
    all_targets.append((pair, symbol, targets))

# Pass 1: no stop
pass1_results = []
for pair, symbol, targets in all_targets:
    opens = daily_opens[pair].reindex(targets.index, method="ffill")
    closes = daily_closes[pair].reindex(targets.index)
    pass1_results.append(c5.simulate_sleeves(targets, opens.to_frame(pair), closes.to_frame(pair), pair=pair, cost=PRIMARY_COST))

def _cap(df):
    d = df.ffill().bfill().fillna(1.0); t = d.sum(axis=1)
    w = d.div(t, axis=0).clip(upper=MAX_CONCENTRATION)
    w = w.div(w.sum(axis=1), axis=0); return (d * w).sum(axis=1)

nav1 = pd.DataFrame({f"s{i}": r["nav"] for i, r in enumerate(pass1_results)})
cnav1 = _cap(nav1); peak1 = cnav1.expanding().max(); dd1 = (peak1 - cnav1) / peak1.where(peak1 > 0, 1.0)
print(f"Pass 1: final NAV={cnav1.iloc[-1]:.2f}, maxDD={dd1.max()*100:.1f}%")

# Per-sleeve decomposition
for variant in ("a","b","c","p","pv"):
    sv = pd.DataFrame({f"s{i}": r[f"sleeve_{variant}"] for i, r in enumerate(pass1_results)})
    sv = sv.ffill().bfill().fillna(0.0); st = sv.sum(axis=1)
    sp = st.expanding().max(); sd = ((sp - st) / sp).max()
    print(f"  Sleeve {variant}: final={st.iloc[-1]:.2f}, maxDD={sd*100:.1f}%")

# State machine
dd_mult_vals = []; reduced = False
for d_val in dd1:
    if not np.isfinite(d_val): dd_mult_vals.append(1.0); continue
    if d_val > DD_HARD_STOP: reduced = True; dd_mult_vals.append(0.0)
    elif d_val > DD_STOP_THRESHOLD: reduced = True; dd_mult_vals.append(DD_SCALE_DOWN)
    elif reduced and d_val < DD_RECOVER_THRESHOLD: reduced = False; dd_mult_vals.append(1.0)
    elif reduced: dd_mult_vals.append(DD_SCALE_DOWN)
    else: dd_mult_vals.append(1.0)

dd_mult = pd.Series(dd_mult_vals, index=dd1.index)

# Pass 2: with stop
pass2_results = []
for pair, symbol, targets in all_targets:
    opens = daily_opens[pair].reindex(targets.index, method="ffill")
    closes = daily_closes[pair].reindex(targets.index)
    dd_a = dd_mult.reindex(targets.index).ffill().fillna(1.0)
    pass2_results.append(c5.simulate_sleeves(targets, opens.to_frame(pair), closes.to_frame(pair), pair=pair, cost=PRIMARY_COST, dd_multiplier_series=dd_a))

nav2 = pd.DataFrame({f"s{i}": r["nav"] for i, r in enumerate(pass2_results)})
cnav2 = _cap(nav2); peak2 = cnav2.expanding().max(); dd2 = (peak2 - cnav2) / peak2.where(peak2 > 0, 1.0)
print(f"Pass 2: final NAV={cnav2.iloc[-1]:.2f}, maxDD={dd2.max()*100:.1f}%")
