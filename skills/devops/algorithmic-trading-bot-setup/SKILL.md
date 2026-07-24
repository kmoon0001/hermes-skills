---
name: algorithmic-trading-bot-setup
description: Safely install, configure, validate, and hand off open-source algorithmic trading bots in paper/dry-run mode with no payment methods or exchange credentials. Covers authoritative-source selection, Freqtrade setup, exchange connectivity, strategy honesty, Windows launchers, UI verification, and a staged path toward any later live deployment.
---

# Algorithmic Trading Bot Setup

Use this skill when a user asks to install, configure, repair, or prepare a crypto/algorithmic trading bot, especially when they say “ready to go,” request the “best/most successful” setup, or require no payment method.

## Core contract

Deliver a working, exercised paper-trading installation—not only commands or a config draft.

Default to these safety boundaries unless the user explicitly changes them:

- Paper/dry-run mode only.
- No exchange API key, bank account, card, deposit, or payment method.
- Spot trading only; no margin, futures, leverage, or shorting.
- Localhost-only management UI.
- Conservative simulated wallet, position size, and maximum open trades.
- Bot starts in `stopped` state so the user deliberately starts paper trading.
- Never imply that a strategy is profitable, “best,” or “most successful” without reproducible evidence.

## 1. Establish the authoritative baseline

1. Inspect the existing project/folder before creating anything; preserve unrelated files and archives.
2. Prefer the bot’s official documentation, official source repository, and stable package/release channel.
3. Confirm current supported Python/runtime versions from official sources before choosing an interpreter.
4. Prefer an officially supported exchange whose public market-data endpoints work without authentication.
5. Treat official sample strategies as compatibility-safe educational starters—not performance claims.

For Freqtrade, use:

- Docs: `https://www.freqtrade.io/en/stable/`
- Source: `https://github.com/freqtrade/freqtrade`
- Stable package: PyPI `freqtrade`
- Config schema: `https://schema.freqtrade.io/schema.json`

## 2. Isolate the installation

Create a dedicated project directory and virtual environment with a supported 64-bit Python. Do not install into Hermes’ own environment or the system interpreter.

Typical Windows layout:

```text
<project>/
  .venv/
  user_data/
    config.json
    strategies/
  START-DRY-RUN.bat
  CHECK-SETUP.bat
  OPEN-WEB-UI.bat
  README.md
```

Install the stable bot and immediately run its version command. Never assume installation success means runtime completeness.

## 3. Build a safety-first Freqtrade config

Required intent:

```json
{
  "$schema": "https://schema.freqtrade.io/schema.json",
  "dry_run": true,
  "dry_run_wallet": 1000,
  "trading_mode": "spot",
  "margin_mode": "",
  "max_open_trades": 2,
  "stake_amount": 50,
  "initial_state": "stopped",
  "force_entry_enable": false,
  "exchange": {
    "key": "",
    "secret": ""
  },
  "api_server": {
    "enabled": true,
    "listen_ip_address": "127.0.0.1"
  }
}
```

Adapt stake currency and pairs to the selected exchange. Do not bind the API to `0.0.0.0` by default.

### Local UI credential handling

- A username is not secret and may be changed directly when requested.
- Tell the user **not to paste a real or reused password into chat**.
- Prefer a local prompt (`getpass`, PowerShell `Read-Host -AsSecureString`, or a small local setter script) so the password never appears in chat, tool arguments, logs, shell history, or source control.
- When Freqtrade receives the password through `FREQTRADE__API_SERVER__PASSWORD`, JSON-encode it as a string first; Freqtrade parses JSON-looking environment values and a numeric/boolean-looking password can otherwise resolve to the wrong type.
- If a generated bootstrap credential is unavoidable, make it unique to this localhost-only paper bot, require changing it locally, and do not place it in README or Git.
- Restart the worker after changing API credentials, then verify authentication and localhost binding. Never claim a login change took effect from a file edit alone.

See `templates/freqtrade-dryrun-config.json` for a copyable starter.

## 4. Verification ladder

Run every applicable rung; fix failures before handoff.

1. **Runtime:** `freqtrade --version` reports the intended interpreter and release.
2. **Dependencies:** `python -m pip check` reports no broken requirements.
3. **Config:** parse JSON with duplicate-key detection, then run `freqtrade show-config ...`; confirm `dry_run: true` and compare every config-overridable strategy value (strategy name, timeframe, ROI, stop-loss, trailing/order settings) with the exact tested candidate. Remember: CLI > environment > config > strategy.
4. **Strategy:** `freqtrade list-strategies ...` shows the configured class with status `OK`; verify ROI timer keys are expressed in elapsed minutes, not candles.
5. **Exchange:** `freqtrade test-pairlist ... --print-json` reaches public markets and returns expected pairs.
6. **Worker startup:** launch `freqtrade trade ...`; verify logs state `Runmode set to dry_run`, the exchange is public/dry-run, the strategy resolves, and the worker reaches a heartbeat.
7. **Safety state:** verify the heartbeat is `STOPPED` when `initial_state` is stopped.
8. **API:** `GET http://127.0.0.1:8080/api/v1/ping` returns `{"status":"pong"}`.
9. **UI:** `GET http://127.0.0.1:8080/` returns FreqUI HTML/assets.

A config-only success is insufficient. A real worker startup plus API/UI probe is the completion standard.

## 5. Evidence-based strategy research and validation

When the user asks for the “most successful” strategy or “deep market analysis,” separate three questions:

1. **Published evidence:** Prefer peer-reviewed/NBER research and official bot documentation over strategy marketplaces, influencer rankings, or headline backtest returns. A documented crypto momentum factor is a research hypothesis—not proof that one EMA/RSI implementation will remain profitable.
2. **Current regime:** Calculate current trend, momentum, realized volatility, liquidity/spread, and drawdown metrics from the actual configured exchange and pairs. Label the timestamp and sample window. Regime analysis selects which hypotheses are plausible; it does not establish expected profit.
3. **Implementation evidence:** Test the exact executable strategy with fees, realistic order assumptions, multiple assets, multiple market regimes, and a holdout/walk-forward period. Compare against buy-and-hold and a deliberately simple baseline.

Favor parsimonious designs over indicator piles. For a conservative spot-paper candidate, a long-only trend/momentum regime filter plus liquidity/volatility constraints and portfolio protections is defensible, but it must still earn deployment through testing.

Required anti-overfitting discipline:

- Write and commit the economic rationale, chronological splits, gates, and bounded search budget before looking at performance.
- Keep parameter searches small; record every tested variant, archived source hash, effective config, and fee—not only the winner.
- Compare a parameter plateau across neighboring settings and calendar regimes; never select the isolated maximum.
- Require sufficient trades and market-regime coverage; a short recent sample is readiness evidence only.
- If development gates fail, stop before validation/holdout. Never tune from holdout results or relabel an already-seen period as untouched.
- Run Freqtrade `lookahead-analysis` and `recursive-analysis` when supported, and verify their final semantic result table—process exit code alone is insufficient.
- Inspect drawdown, exposure, turnover, fees, slippage sensitivity, one-bar execution delay, protection ablation, per-pair concentration, bootstrap uncertainty, and stability—not merely total return or win rate.
- Use forward dry-run as the final gate. Never promote to live merely because a backtest is positive.

See `references/evidence-based-crypto-strategy.md` for the condensed source bank and validation checklist. See `references/freqtrade-research-provenance-and-gating.md` for archive manifests, holdout discipline, bootstrap checks, timeframe overrides, semantic bias-tool verification, and execution-stress sequencing.

### Mapping backtest results to strategy names

Freqtrade backtest result zips (`.zip`) and their companion `.meta.json` files do NOT consistently store the strategy name or backtest timerange. The zip's internal JSON has a `strategy_comparison` array but the `strategy` field is often empty, and `.meta.json` can be missing keys. To identify which strategy produced which result zip:

1. Use the **log file** that was passed to `--backtest-directory` or the saved run log (e.g. `research-dev.log`, `baseline-validation.log`).
2. Parse the log for `Using resolved strategy <Name> from` — the first occurrence before the STRATEGY SUMMARY section identifies the tested strategy.
3. Cross-reference with backtest timestamps: the log records the exact minute each run starts, so you can match it to the nearest `backtest-result-YYYY-MM-DD_HH-MM-SS.zip` by time.

```python
import re, glob, zipfile, json
# Find strategy name from a log file
with open('user_data/backtest_results/research-dev.log') as f:
    text = f.read()
strategies = re.findall(r'Using resolved strategy (\w+) from', text)

# Then read actual profit from each corresponding zip
for zpath in sorted(glob.glob('user_data/backtest_results/backtest-result-*.zip')):
    with zipfile.ZipFile(zpath) as z:
        with z.open(z.namelist()[0]) as f:
            d = json.load(f)
    sc = d.get('strategy_comparison',[{}])[0]
    print(f'{zpath}: {round(sc.get("profit_total",0)*100,2)}%')
```

Alternatively, when you can re-run the backtest, pass `--notes "MyStrategyName"` to annotate result files so they're self-identifying.

### Historical data constraints

- Check the selected exchange’s Freqtrade notes before promising candle downloads.
- Some exchanges require rebuilding OHLCV from raw trades; do not switch exchanges merely to force a quick backtest without considering jurisdiction and support.
- A limited public OHLCV window may support current-regime analysis, but it is not a robust long-horizon backtest.
- When historical candles are available, download a bounded dataset, backtest with a smaller detail timeframe when available, and run lookahead/recursive analysis before discussing strategy quality.
- Audit each pair/timeframe file before selecting the detail timeframe: verify first/last timestamps, duplicates, monotonicity, gaps, OHLCV validity, and hashes. Never infer lower-timeframe coverage from the strategy timeframe—5m data may begin years later than otherwise complete 15m/1h history. Use `scripts/audit_freqtrade_ohlcv.py` and fall back to the finest detail timeframe that covers the entire tested split.
- Audit derivatives features independently before implementation. Historical queryability today is not proof that funding, open interest, positioning, premium/basis, or liquidation observations were available at the simulated decision time. Preserve event/period/settlement/publication/ingestion timestamps; verify full archive coverage and revisions; apply a conservative availability lag; and reject or disable unverifiable families. Follow `references/derivatives-data-causal-audit.md`.
- If a public data endpoint returns a jurisdictional/legal block such as HTTP 451, never bypass it. Use an accessible officially supported research venue, preserve the requested paper venue, and disclose quote-currency, basis, fee, spread, and microstructure differences.
- If only forward dry-run is practical, say so clearly; do not substitute simulated profitability claims.

### Ecosystem comparison and architecture transfer

When comparing Freqtrade with other open-source trading systems, compare responsibilities rather than feature counts: research/live parity, execution realism, signal-sizing-risk-execution separation, portfolio controls, bias detection, reproducibility, and deployment scope.

- Prefer official documentation and primary repositories, and label each point as documented capability, source observation, or recommendation/inference.
- Use vn.py and NautilusTrader as references for strategy-independent pre-trade risk; LEAN for explicit portfolio, risk, execution, fill, fee, and slippage models; Hummingbot for controller/executor and bounded-position lifecycles; and Jesse for strategy ergonomics, optimization, regression testing, and ML feature parity.
- Adapt patterns to Freqtrade rather than recreating another framework inside it. If tick-level market making, an institutional OMS, or multi-asset target portfolios are core requirements, recommend changing platforms instead of forcing a large architectural transplant.
- Rank recommendations by safety and evidence: pre-trade risk and portfolio heat first; bias/reproducibility and execution-cost stress next; bounded position lifecycle next; DCA, order-flow, and ML only after those gates.

See `references/open-source-trading-ecosystem-patterns.md` for the comparison matrix, official sources, ranked transfers, and practices not worth porting.

### Official validation and security review

When the task is a research/review rather than an installation, return an ordered checklist with direct official URLs and representative, release-verified commands. Cover the full gate: effective config, pairlist/data coverage, realistic backtest, lookahead analysis, recursive analysis, protection-enabled comparison, sustained dry-run, localhost API/FreqUI hardening, and live UI verification after every change.

Key invariants:

- A profitable backtest is never sufficient; every signal must be exercised in lookahead analysis, recursive variance must be decision-irrelevant at the chosen startup count, and dry-run is the final pre-live gate.
- Lookahead analysis intentionally disables protections and changes execution assumptions; do not treat it as a protection or profitability test.
- For new Freqtrade `MaxDrawdown` configurations, prefer the officially recommended equity calculation mode and test protection behavior explicitly with `--enable-protections`.
- On Docker, distinguish container binding (`0.0.0.0` may be necessary) from host publishing (`127.0.0.1:8080:8080` for local-only access).
- Freqtrade supports environment overrides and split private configs but does not document native Windows Credential Locker integration. Clearly label Microsoft Learn material as general Windows security guidance, not Freqtrade documentation.

See `references/freqtrade-validation-and-security.md` for exact gates, Kraken history constraints, API/UI security, Windows secret-handling boundaries, and authoritative URLs.

## 6. Windows DNS fallback pattern

If normal `socket.getaddrinfo`/`curl` resolve the exchange but Freqtrade’s async client reports pycares/aiodns DNS failures:

1. Prove the split by testing system DNS and the same HTTPS endpoint outside Freqtrade.
2. Keep `aiodns` and `pycares` installed so `ccxt` dependencies remain satisfied.
3. Configure the venv’s aiohttp resolver to use `ThreadedResolver` (Windows system resolver) instead of deleting required packages.
4. Re-run `pip check` and the live pairlist test.
5. Preserve an idempotent repair script because an aiohttp upgrade may overwrite the local resolver choice.

Use `scripts/repair_freqtrade_windows_dns.py` rather than hand-editing when this exact diagnostic split is present. Do not apply it preemptively.

## 7. User handoff

Provide, bottom-line-first:

- Absolute installation path.
- One-click start/check/UI files.
- Local UI URL and login.
- Exact paper wallet, stake size, pair list, and max trades.
- Explicit confirmation that no payment method or exchange key exists.
- Current process state (running/stopped) based on a real heartbeat.
- A short warning that the starter strategy is not guaranteed profitable.

Do not overwhelm the handoff with installation logs. Put operational detail and authoritative links in the project README.

## Pitfalls

- Installing with an unsupported Python merely because it is first on `PATH`.
- Calling an official sample strategy “successful” or “optimized.”
- Enabling live trading or requesting keys when the user asked for no payment method.
- Leaving the UI exposed beyond localhost.
- Treating `show-config` as full verification without starting the worker.
- Removing `aiodns`/`pycares` to bypass DNS and leaving `pip check` broken.
- Claiming backtest readiness before checking exchange-specific historical-data support.
- Launching directly into a trading state without a deliberate user start action.
- Asking the user to paste a real/reused UI password into chat, or persisting a bootstrap password in README/Git.
- Treating published momentum-factor evidence as proof that a specific indicator rule is profitable.
- Tuning repeatedly on a short recent OHLCV window and reporting only the winning variant.
- Treating `minimal_roi` timer keys as candles; Freqtrade expresses them in elapsed minutes.
- Trusting a syntactically valid JSON file without checking duplicate keys and effective config precedence.
- Mutating live order/pricing settings to make `lookahead-analysis` pass; use an analysis-only override because the tool forces market orders.
- Bypassing an exchange HTTP 451/geographic restriction instead of using a disclosed, officially supported research-data venue.
- Passing arbitrary passwords as raw environment values when the application JSON-parses environment variables; encode them as strings and keep them out of logs.

## Supporting files

- `references/freqtrade-windows-paper-setup.md` — condensed implementation notes and verification evidence pattern.
- `references/evidence-based-crypto-strategy.md` — primary-source notes, regime-analysis fields, conservative architecture, and anti-overfitting validation gates.
- `references/freqtrade-strategy-capability-reference.md` — catalog of every advanced strategy callback (custom_exit, custom_stoploss, custom_roi, adjust_trade_position), informative pair decorators and manual patterns, FreqAI feature-engineering pipeline, DataProvider runtime access, persistent custom data storage, and documented limitations. Verified against official docs 2026-07-18.
- `references/freqtrade-validation-and-security.md` — official validation sequence, release-verified commands, Kraken history constraints, API/UI hardening, and Windows credential boundaries.
- `references/freqtrade-2026-validation-pitfalls.md` — config/ROI traps, safe multi-timeframe alignment, mechanism-level hypothesis discipline, execution-cost stress, semantic lookahead/recursive checks, protection ablation, jurisdiction-safe data substitution, and secure Windows environment encoding.
- `references/freqtrade-research-provenance-and-gating.md` — preregistered chronological gates, ZIP/source-hash provenance, bootstrap uncertainty, timeframe/config traps, semantic bias-tool verification, and execution-stress sequencing.
- `references/derivatives-data-causal-audit.md` — point-in-time audit for funding, open interest, positioning, premium/basis, and liquidation data; includes official Binance archive enumeration, schema-era handling, revision risk, full-file quality checks, conservative availability lags, and independent family-level go/no-go rules.
- `references/open-source-trading-ecosystem-patterns.md` — responsibility-based ecosystem comparison, ranked Freqtrade transfers, official sources, and architectural patterns not worth porting.
- `templates/freqtrade-dryrun-config.json` — safety-first starter config.
- `scripts/audit_freqtrade_ohlcv.py` — read-only per-file coverage, integrity, gap, OHLCV, and SHA-256 audit before selecting research/detail timeframes.
- `scripts/repair_freqtrade_windows_dns.py` — idempotent resolver fallback for the proven Windows pycares/system-DNS split.
