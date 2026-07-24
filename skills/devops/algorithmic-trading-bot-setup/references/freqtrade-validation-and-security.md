# Freqtrade Validation and Security Reference

Use this note for official-source research, setup review, or pre-live readiness checks. Reconfirm flags against the installed release; the examples below were verified against Freqtrade 2026.6.

## Authoritative sources

- Release: https://github.com/freqtrade/freqtrade/releases/
- Installation: https://www.freqtrade.io/en/stable/installation/
- Configuration: https://www.freqtrade.io/en/stable/configuration/
- Data: https://www.freqtrade.io/en/stable/data-download/
- Backtesting: https://www.freqtrade.io/en/stable/backtesting/
- Lookahead: https://www.freqtrade.io/en/stable/lookahead-analysis/
- Recursive: https://www.freqtrade.io/en/stable/recursive-analysis/
- Protections: https://www.freqtrade.io/en/stable/plugins/#protections
- API: https://www.freqtrade.io/en/stable/rest-api/
- FreqUI: https://www.freqtrade.io/en/stable/freq-ui/
- Exchange notes: https://www.freqtrade.io/en/stable/exchanges/

## Ordered validation gate

1. **Version/config:** verify `freqtrade --version`; keep Windows on Docker when practical; run `freqtrade show-config -c ...` without `--show-sensitive` and confirm `dry_run: true`, `initial_state: stopped`, realistic wallet/stake, and empty exchange credentials.
2. **Pairlist/data:** run `test-pairlist --print-json`, use a reviewed static pairlist for reproducible backtests, download every strategy/informative/detail timeframe, and confirm coverage with `list-data --show-timerange`.
3. **Backtest:** use explicit timeranges, realistic wallet/stake/fees, `--enable-protections`, exported trades, time breakdowns, and—when available—a smaller `--timeframe-detail`. Review drawdown, concentration, exposure, turnover, exit reasons, rejected signals, and stability; never rely only on profit or win rate. Avoid position stacking because it is not reproducible in dry/live operation.
4. **Lookahead:** run over enough history to trigger every signal. Require `has_bias: No`; widen the timerange when the minimum trade count is not met. Fix entries before exits. This command forces protections off and modifies wallet/order assumptions by design, so it is not a profitability test.
5. **Recursive:** analyze one liquid representative pair with at least roughly 5,000 candles and several startup-candle values. Choose a `startup_candle_count` whose remaining variance cannot move trading decisions across thresholds; exact zero is not always necessary for recursive indicators such as EMA.
6. **Protections:** test the same strategy with and without protections. Protections must be explicitly enabled in backtesting/hyperopt. For new `MaxDrawdown` setups, official docs recommend `calculation_mode: "equity"`. Tune lookback, trade minimum, and lock duration from adverse-period evidence.
7. **Dry-run:** use `freqtrade trade --dry-run ...` as a CLI safety override, no live keys, a separate dry-run database, and a stopped initial state. Forward-test across regimes and inspect fills, timeouts, locks, restart recovery, and rate-limit errors.
8. **UI/API verification:** restart after configuration changes; verify `/api/v1/ping`, FreqUI assets/login, exchange, strategy, pairlist, dry-run label, wallet, and stopped/running state. Confirm another LAN host cannot reach the service.
9. **Live promotion:** only after sustained dry-run; use a fresh database, new least-privilege exchange credentials, no withdrawal permission, and explicit user approval.

## Representative commands

```text
freqtrade show-config -c user_data/config.json
freqtrade test-pairlist -c user_data/config.json --print-json
freqtrade backtesting -c user_data/config.json --strategy YourStrategy --timerange YYYYMMDD-YYYYMMDD --dry-run-wallet 1000 --enable-protections --export trades --breakdown month weekday
freqtrade lookahead-analysis -c user_data/config.json --strategy YourStrategy --timerange YYYYMMDD-YYYYMMDD --minimum-trade-amount 20
freqtrade recursive-analysis -c user_data/config.json --strategy YourStrategy --timerange YYYYMMDD-YYYYMMDD -p REPRESENTATIVE/PAIR --startup-candle 199 499 999 1999
freqtrade trade --dry-run -c user_data/config.json --strategy YourStrategy
curl http://127.0.0.1:8080/api/v1/ping
```

Add `--timeframe-detail` only when the detail data exists and the detail timeframe is smaller than the strategy timeframe.

## Kraken historical-data constraint

Kraken spot exposes only 720 historic OHLCV candles through its API. For meaningful backtests, official Freqtrade guidance requires raw trade downloads with `--dl-trades` and conversion to OHLCV, or Kraken’s downloadable historical trade archives. Kraken Futures uses normal OHLCV downloads. Verify archive continuity because missing quarterly increments create incomplete data and invalid results.

## API/FreqUI security

- Native/local: bind to `127.0.0.1:8080`.
- Docker: the container may listen on `0.0.0.0`, but publish only `127.0.0.1:8080:8080`; avoid `8080:8080` or `0.0.0.0:8080:8080`.
- Use a unique API password, a random unique JWT secret of at least 32 characters, and a separate random WebSocket token.
- Keep `CORS_origins: []` and OpenAPI disabled unless specifically required.
- Never expose the control API directly to the internet. Prefer SSH tunnel or private VPN; TLS reverse proxy alone does not justify public exposure.

## Windows credential boundary

Freqtrade officially supports environment-variable overrides and split private config files. It does not document native integration with Windows Credential Locker/Credential Manager. Do not claim otherwise.

Applicable Microsoft guidance is general Windows/application security, not Freqtrade documentation:

- Credential Locker: https://learn.microsoft.com/windows/apps/develop/security/credential-locker
- Password storage and ACL guidance: https://learn.microsoft.com/windows/win32/secbp/threat-mitigation-techniques#storing-passwords
- General secrets practices: https://learn.microsoft.com/azure/security/fundamentals/secrets-best-practices

Operational implications:

- Do not store secrets in strategy code, Git, README files, screenshots, support messages, logs, shell history, or cloud-synced folders.
- A `.env` or private JSON file remains plaintext unless separately protected. If it is the fallback, exclude it from source control/sync, restrict NTFS ACLs, and protect the volume.
- Prefer an OS-managed credential store plus a trusted launcher that supplies values through a Freqtrade-supported input without logging them.
- Never use `show-config --show-sensitive` for routine diagnostics.
- State explicitly in research deliverables that Microsoft Learn does not document Freqtrade; Freqtrade docs remain authoritative for bot behavior.
