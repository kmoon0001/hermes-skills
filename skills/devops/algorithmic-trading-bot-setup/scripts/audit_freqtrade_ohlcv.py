#!/usr/bin/env python
"""Audit Freqtrade Feather OHLCV coverage and integrity.

Usage:
    python audit_freqtrade_ohlcv.py <data-dir> [--csv report.csv]

The audit is read-only. It reports per-file date coverage, SHA-256, duplicate or
nonmonotonic timestamps, gaps, missing values, and invalid OHLCV rows. Verify
coverage per timeframe before choosing an intrabar detail timeframe: lower-
timeframe files may start years later than strategy-timeframe files.
"""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import pandas as pd

TF_SECONDS = {"1m": 60, "3m": 180, "5m": 300, "15m": 900, "30m": 1800,
              "1h": 3600, "2h": 7200, "4h": 14400, "6h": 21600,
              "8h": 28800, "12h": 43200, "1d": 86400}
TF_PATTERN = re.compile(r"-(1m|3m|5m|15m|30m|1h|2h|4h|6h|8h|12h|1d)(?:-spot|-futures)?\.feather$")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit(path: Path) -> dict:
    match = TF_PATTERN.search(path.name)
    if not match:
        raise ValueError(f"Cannot infer timeframe from {path.name}")
    timeframe = match.group(1)
    expected = TF_SECONDS[timeframe]
    frame = pd.read_feather(path)
    required = ["date", "open", "high", "low", "close", "volume"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{path.name}: missing columns {missing}")

    dates = pd.to_datetime(frame["date"], utc=True)
    # Use timedelta arithmetic: datetime integer storage units vary by pandas build.
    seconds = dates.diff().dt.total_seconds()
    gaps = seconds[seconds > expected]
    prices = frame[["open", "high", "low", "close"]]
    invalid_ohlc = (
        (frame["high"] < prices[["open", "close", "low"]].max(axis=1))
        | (frame["low"] > prices[["open", "close", "high"]].min(axis=1))
    )
    return {
        "file": path.name,
        "timeframe": timeframe,
        "rows": len(frame),
        "first_utc": dates.min().isoformat(),
        "last_utc": dates.max().isoformat(),
        "duplicate_timestamps": int(dates.duplicated().sum()),
        "nonmonotonic_steps": int((seconds < 0).sum()),
        "irregular_steps": int(((seconds.notna()) & (seconds != expected)).sum()),
        "gap_events": int(gaps.size),
        "estimated_missing_bars": int(sum(max(round(gap / expected) - 1, 0) for gap in gaps)),
        "nan_ohlcv_rows": int(frame[required[1:]].isna().any(axis=1).sum()),
        "nonpositive_price_rows": int((prices <= 0).any(axis=1).sum()),
        "negative_volume_rows": int((frame["volume"] < 0).sum()),
        "invalid_ohlc_rows": int(invalid_ohlc.sum()),
        "sha256": file_hash(path),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("data_dir", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()

    files = sorted(args.data_dir.glob("*.feather"))
    if not files:
        raise SystemExit(f"No Feather files found in {args.data_dir}")
    result = pd.DataFrame(audit(path) for path in files).sort_values(["timeframe", "file"])
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        result.to_csv(args.csv, index=False)

    defect_columns = ["duplicate_timestamps", "nonmonotonic_steps", "nan_ohlcv_rows",
                      "nonpositive_price_rows", "negative_volume_rows", "invalid_ohlc_rows"]
    defects = int(result[defect_columns].to_numpy().sum())
    print(result[["file", "timeframe", "rows", "first_utc", "last_utc", "gap_events"]].to_string(index=False))
    print(f"files={len(result)} defects={defects} gaps={int(result['gap_events'].sum())} missing_est={int(result['estimated_missing_bars'].sum())}")
    raise SystemExit(1 if defects else 0)


if __name__ == "__main__":
    main()
