# Freqtrade 2026 validation pitfalls and proven patterns

Use this reference when validating a Freqtrade strategy/config pair on current releases. Reconfirm behavior against the installed version; these observations were exercised on Freqtrade 2026.6.

## Configuration and strategy precedence

Freqtrade precedence is CLI > environment > configuration files > strategy class. Therefore:

- A valid strategy can still run with unintended ROI, stop-loss, trailing-stop, timeframe, or order settings when the same key exists in config.
- Run `show-config` and compare the effective values with the tested strategy before startup.
- Detect duplicate JSON keys with a parser using an `object_pairs_hook`; ordinary JSON loaders silently keep the last duplicate. A duplicate `strategy` key can make the wrong class run even when both names look present in the file.
- Some pairlist filters inspect config directly. In 2026.6, `PrecisionFilter` required `stoploss` in config even when the strategy defined the same value. Mirror the tested value rather than inventing a second one.

## ROI timer unit trap

`minimal_roi` dictionary keys are elapsed **minutes**, not candles. For a 1-hour strategy, values such as `48`, `120`, and `240` mean minutes, not 48/120/240 candles. This can collapse exits into the first few candles and invalidate comparisons.

Before backtesting, annotate ROI keys with their intended wall-clock durations and verify the resolved config. Treat a unit correction as a correctness fix; rerun every candidate and chronological split afterward.

## Protections on current releases

Config-level protection placement may be deprecated depending on release. On 2026.6, strategy-level `protections` was the supported path used successfully. Verify with the installed docs and worker startup logs. Backtests must pass `--enable-protections`; lookahead analysis intentionally disables protections and is not a profitability test.

## Lookahead-analysis market-order override

Lookahead analysis forces market orders unless explicitly overridden. Current validation can reject a normal limit-order config when `entry_pricing.price_side` / `exit_pricing.price_side` are incompatible with forced market orders.

Do not mutate the live config just to satisfy analysis. Supply a second analysis-only config containing:

```json
{
  "entry_pricing": {"price_side": "other", "use_order_book": false},
  "exit_pricing": {"price_side": "other", "use_order_book": false}
}
```

Run the primary config first and the override second so only the analysis process receives the change. Do not enable limit orders merely to silence the validator; official docs warn that this can create false positives.

## Chronological and intrabar validation

- Compare a small, predeclared set of strategy families under identical data, fees, stakes, and protections.
- Use a detail timeframe smaller than the strategy timeframe when data exists (for example, 5m detail for 1h signals).
- After selecting a candidate, rerun an earlier segment and a strictly later out-of-sample segment without changing parameters.
- Preserve weak statistics honestly. A small positive result with a high p-value is a paper-forward candidate, not a proven edge.
- Reject losing candidates instead of describing capital preservation as profitability.

## Multi-timeframe alignment and hypothesis discipline

For a lower-timeframe strategy with higher-timeframe context:

- Use only completed candles. Freqtrade normally removes the unfinished exchange candle; do not reconstruct or merge repainting data back into the strategy.
- Use `@informative()` or `merge_informative_pair()` rather than a plain pandas merge. Informative candle timestamps refer to candle opens, so an ordinary merge can expose the higher-timeframe close before it was knowable.
- Avoid `shift(-n)`, absolute `iloc` access in `populate_*`, whole-column aggregates without `rolling()`, and left-labeled resampling.
- Keep indicator calculations in `populate_indicators()` or informative methods so `recursive-analysis` includes them.
- Treat the higher timeframe as a regime selector and the lower timeframe as an event-like trigger. Assign each component exactly one job and ablate it independently.

When a small parameter grid around one mechanism fails, do not rescue it by adding filters or widening the grid. Test a small number of economically distinct families instead, such as trend-gated pullback continuation, regime-bounded mean reversion, and volatility-compression expansion. Start from fixed conventional periods; only test narrow one-dimensional neighborhoods after the mechanism works across chronological folds.

## Candle execution optimism and cost stress

Current Freqtrade backtests make several optimistic or deterministic assumptions:

- Requested orders fill without slippage when the price lies within candle high/low.
- Stop losses fill exactly at the stop price.
- The engine imposes an intrabar event order for stoploss, ROI, and trailing behavior.
- Current exchange amount/price limits and precision are applied because historical limits are unavailable.

Therefore, changing a backtest order type to `market` does not create a market-impact model. Required validation pattern:

1. Use the actual account/jurisdiction fee tier and assume taker fees on both legs unless post-only maker behavior has been demonstrated.
2. Run adverse execution surcharges, for example an extra 5/10/20 basis points per leg. Inflating `--fee` is a useful first proxy because Freqtrade applies it on entry and exit, but it cannot model missed orders, partial fills, queue position, latency, or state-dependent impact.
3. Rerun serious candidates with a smaller `--timeframe-detail` (for example 5m detail for 1h signals).
4. Add a conservative fill variant that delays or rejects marginal candle-touch limits; a result that requires every touched limit to fill should be rejected.
5. Use sustained dry-run to observe spread, order age, timeout/cancellation behavior, and signal-to-order latency. Dry-run market fills use current order-book volume, but remain simulated and are not proof of live queue position.

Fee schedules can vary by exchange region, account tier, assets, and rolling volume. Cite the applicable exchange fee page, but do not hard-code a globally assumed rate when the account jurisdiction is unknown.

## Semantic use of bias and recursive tools

`lookahead-analysis` starts with a baseline and reruns each entry and exit signal separately. It also neutralizes several portfolio constraints and forces protections off and market orders by default. Consequences:

- Ensure every signal type triggers enough times; an untriggered signal can create a false negative.
- Diagnose biased entries before exits because a biased entry frequently makes its paired exit appear biased.
- Do not interpret the run as a profitability, protection, wallet, or portfolio-concurrency test.
- Limit orders and custom pricing can create delayed-entry false positives; prefer the default forced-market analysis plus an analysis-only pricing override when required.

For `recursive-analysis`:

- Use a long benchmark timerange (official guidance recommends at least 5,000 candles) and several startup histories around the intended value.
- The tool compares last-row indicator values, not resulting trades. Confirm separately that observed variance cannot cross any regime, entry, or exit threshold.
- Absolute zero is not always necessary for recursive indicators such as EMA, but the selected variance must be decision-irrelevant.
- Run representative high-volatility and low-priced instruments when rounding or pair-specific behavior may matter.

## Protection ablation

Assess raw signal quality without protections first, then add a small policy-driven layer. Protections must not manufacture apparent alpha.

- Backtests and hyperopt require explicit `--enable-protections`.
- Prefer `MaxDrawdown` with `calculation_mode: "equity"` for new setups; ratio mode is a legacy approximation and can differ when position sizing changes.
- A minimal starting family is pair-level `CooldownPeriod`, a global `StoplossGuard`, and a global equity `MaxDrawdown` lock.
- Set thresholds from an ex-ante risk policy rather than hyperoptimizing them for return. Compare raw and protected trade sets to reveal whether a protection merely avoids one historically convenient episode.

## Jurisdictional historical-data restriction

If a venue returns a legal/geographic restriction such as HTTP 451, do not bypass it. Select another officially supported venue whose unauthenticated public market data is accessible. Keep the paper/live exchange unchanged unless the user requested a venue change, and disclose that:

- Historical research venue and paper-execution venue differ.
- Quote currencies (for example USDT versus USD), basis, fee schedules, spread, and microstructure can differ.
- The result is suitability evidence for dry-run, not exchange-specific proof.

## Secure Windows launcher details

Microsoft Learn supports `Read-Host -AsSecureString` for masked local input. Freqtrade supports environment overrides using `FREQTRADE__SECTION__KEY`.

When passing an arbitrary password through `FREQTRADE__API_SERVER__PASSWORD`, JSON-encode the plaintext string first (`ConvertTo-Json -InputObject $plain -Compress`). Otherwise a password that looks like JSON (`true`, a number, an array/object prefix) may be parsed as the wrong type. Keep the conversion lifetime short, clear local variables, and remove environment variables when the child exits.

A generated bootstrap secret can be rotated and verified programmatically without printing it: read config locally inside a verification process, authenticate to `/api/v1/token/login`, then assert runtime fields from `/api/v1/show_config`. Print booleans/status only, never the password or bearer token.

## Final security verification

Before handoff, verify all of the following from live state:

- Port listens on `127.0.0.1` only.
- No duplicate config keys.
- No exchange key/secret in dry-run.
- Username changed as requested.
- Password/JWT/WebSocket tokens have appropriate entropy, measured for their encoding (for example, a 32-byte URL-safe token is typically 43 characters).
- Authenticated runtime readback shows dry-run, spot, intended strategy/timeframe, conservative stake/max trades, stopped state, and zero unexpected open trades.
- FreqUI renders its real login dialog. Automation may fill the non-secret username, but the user must enter the password locally.
