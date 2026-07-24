# Freqtrade Windows paper-mode implementation notes

## Proven setup shape

- Use a dedicated Python 3.11+ virtual environment, not the agent/runtime environment.
- Install stable Freqtrade, then validate imports through real commands rather than relying on pip’s success message.
- Generate `user_data` with the CLI so directory structure and official sample strategy match the installed release.
- Use an officially supported exchange and public endpoints; empty API credentials are valid in dry-run.
- Select a small static spot pair list and conservative simulated stakes.
- Install FreqUI and bind its API to `127.0.0.1` only.

## Validation evidence to capture

A complete handoff should preserve concise evidence of:

1. Freqtrade, Python, and CCXT versions.
2. `pip check` success.
3. Resolved config with `dry_run` enabled.
4. Strategy status `OK`.
5. Exchange identified as officially supported.
6. Pairlist output containing the intended pairs.
7. Worker log showing dry-run mode, strategy load, API startup, and heartbeat.
8. `/api/v1/ping` returning `{"status":"pong"}`.
9. Root URL returning FreqUI HTML.

## Dependency/runtime repair pattern

A successful wheel install can still expose a missing runtime import. Use the traceback to identify the module, install the compatible dependency into the same venv, rerun the failing command, and finish with `pip check`. Do not encode a particular missing module as permanently required unless it is still declared by the current release.

## Windows async DNS diagnostic split

Apply the resolver fallback only when all are true:

- Windows system DNS resolves the exchange hostname.
- Direct HTTPS access succeeds.
- Freqtrade/CCXT fails specifically through `aiodns`/`pycares` with a DNS-server-contact error.

Retain required packages and switch aiohttp’s default to its threaded/system resolver inside that isolated venv. Verify both dependency integrity and exchange access afterward. Preserve an idempotent repair helper for package upgrades.

## Strategy language

Say: “official maintained educational starter” or “compatibility-safe baseline.”

Do not say: “best,” “most successful,” “profitable,” or “optimized” unless backed by reproducible backtests, bias checks, fees/slippage assumptions, and forward dry-run results.

## Exchange historical-data caveat

Exchange support for live public candles does not imply Freqtrade can download historical OHLCV directly. Check exchange-specific documentation before promising backtesting. Some exchanges require `--dl-trades` and local candle reconstruction, which can be slow.
