#!/usr/bin/env python3
"""Deterministic live probe for a BTC/ETH crypto market-regime assessment.

Prints timestamped JSON from public CoinGecko, Coinbase Exchange, and
Deribit endpoints. It does not make trading decisions or price forecasts.

Usage:
    python crypto_regime_probe.py
"""

from __future__ import annotations

import datetime as dt
import json
import math
import statistics
import time
from typing import Any

import requests

TIMEOUT = 30
HEADERS = {"User-Agent": "crypto-regime-research/1.0"}

# Common non-risk-asset entries found in the top-100 universe. Review and
# extend this set whenever the composition changes.
NON_RISK_IDS = {
    "tether", "usd-coin", "usds", "dai", "usd1-wlfi", "ethena-usde",
    "global-dollar", "hashnote-usyc", "blackrock-usd-institutional-digital-liquidity-fund",
    "paypal-usd", "tether-gold", "pax-gold", "ondo-us-dollar-yield",
    "ripple-usd", "usdd", "falcon-finance", "bfusd", "united-stables",
    "usdgo", "usdtb", "gho", "usual-usd", "usx", "ylds",
    "superstate-short-duration-us-government-securities-fund-ustb",
    "janus-henderson-anemoy-treasury-fund",
    "janus-henderson-anemoy-aaa-clo-fund",
}


def get_json(url: str, **params: Any) -> Any:
    response = requests.get(url, params=params or None, headers=HEADERS, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def trend(product: str) -> dict[str, Any]:
    url = f"https://api.exchange.coinbase.com/products/{product}/candles"
    rows = sorted(get_json(url, granularity=86400), key=lambda row: row[0])
    closes = [float(row[4]) for row in rows]

    # Latest row is the incomplete current UTC candle.
    completed = closes[:-1]
    current = completed[-1]
    result: dict[str, Any] = {
        "last_completed_utc": dt.datetime.fromtimestamp(
            rows[-2][0], dt.timezone.utc
        ).date().isoformat(),
        "completed_close": current,
        "incomplete_today_close": closes[-1],
    }

    for days in (7, 30, 90, 180):
        if len(completed) > days:
            result[f"return_{days}d_pct"] = (current / completed[-1 - days] - 1) * 100

    for days in (20, 50, 100, 200):
        if len(completed) >= days:
            sma = statistics.mean(completed[-days:])
            result[f"sma_{days}"] = sma
            result[f"vs_sma_{days}_pct"] = (current / sma - 1) * 100

    for days in (7, 30, 90):
        if len(completed) > days:
            window = completed[-1 - days :]
            log_returns = [math.log(window[i] / window[i - 1]) for i in range(1, len(window))]
            result[f"realized_vol_{days}d_ann_pct"] = (
                statistics.stdev(log_returns) * math.sqrt(365) * 100
            )
    return result


def volatility_index(currency: str) -> dict[str, Any]:
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - 7 * 86_400_000
    url = "https://www.deribit.com/api/v2/public/get_volatility_index_data"
    rows = get_json(
        url,
        currency=currency,
        start_timestamp=start_ms,
        end_timestamp=end_ms,
        resolution=3600,
    )["result"]["data"]
    latest = rows[-1]
    return {
        "latest_utc": dt.datetime.fromtimestamp(latest[0] / 1000, dt.timezone.utc).isoformat(),
        "latest_close": latest[4],
        "seven_day_low": min(row[3] for row in rows),
        "seven_day_high": max(row[2] for row in rows),
    }


def breadth() -> dict[str, Any]:
    url = "https://api.coingecko.com/api/v3/coins/markets"
    rows = get_json(
        url,
        vs_currency="usd",
        order="market_cap_desc",
        per_page=100,
        page=1,
        sparkline="false",
        price_change_percentage="7d,30d,1y",
    )
    screened = [row for row in rows if row["id"] not in NON_RISK_IDS]
    fields = {
        "24h": "price_change_percentage_24h",
        "7d": "price_change_percentage_7d_in_currency",
        "30d": "price_change_percentage_30d_in_currency",
    }
    result: dict[str, Any] = {
        "raw_count": len(rows),
        "screened_count": len(screened),
        "excluded_count": len(rows) - len(screened),
        "screen_note": "Review NON_RISK_IDS; top-100 composition changes over time.",
    }
    for label, field in fields.items():
        values = [float(row[field]) for row in screened if row.get(field) is not None]
        advancing = sum(value > 0 for value in values)
        result[label] = {
            "observations": len(values),
            "advancing": advancing,
            "declining": sum(value < 0 for value in values),
            "percent_advancing": advancing / len(values) * 100 if values else None,
            "median_return_pct": statistics.median(values) if values else None,
        }
    return result


def main() -> None:
    simple_url = "https://api.coingecko.com/api/v3/simple/price"
    live_prices = get_json(
        simple_url,
        ids="bitcoin,ethereum",
        vs_currencies="usd",
        include_market_cap="true",
        include_24hr_change="true",
        include_last_updated_at="true",
    )
    global_data = get_json("https://api.coingecko.com/api/v3/global")["data"]

    output = {
        "snapshot_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "live_prices": live_prices,
        "global": {
            "total_market_cap_usd": global_data["total_market_cap"]["usd"],
            "total_volume_usd": global_data["total_volume"]["usd"],
            "market_cap_change_24h_pct": global_data["market_cap_change_percentage_24h_usd"],
            "dominance_pct": global_data["market_cap_percentage"],
            "updated_at": global_data["updated_at"],
        },
        "trend": {
            "BTC-USD": trend("BTC-USD"),
            "ETH-USD": trend("ETH-USD"),
            "ETH-BTC": trend("ETH-BTC"),
        },
        "implied_volatility": {
            "BTC": volatility_index("BTC"),
            "ETH": volatility_index("ETH"),
        },
        "breadth": breadth(),
    }
    print(json.dumps(output, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
