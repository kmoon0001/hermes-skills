# Freqtrade research provenance, gating, and robustness workflow

Use this reference for multi-run strategy research where archived results, parameter variants, chronological splits, and execution stress must remain auditable.

## 1. Freeze evidence before selection

Before running development experiments, write and commit:

- Fixed universe, exchange mode, direction/leverage constraints, strategy and detail timeframes.
- Explicit fee per side and a separate adverse-cost fee.
- Chronological development, validation, and genuinely untouched holdout windows.
- Minimum development gates: trade count, profit factor, calendar/regime stability, drawdown, pair concentration, and uncertainty.
- Maximum search budget and exact parameters allowed to vary.
- A rule that failed development gates stop the candidate before validation or holdout.

If an alleged holdout has already influenced strategy-family or parameter selection, call it a quasi-holdout or confirmation period. Reserve another unexamined interval when possible. Never repair a failed strategy using holdout results.

## 2. Preserve archive provenance

Freqtrade result ZIPs can contain the exact strategy source and run configuration. Build a manifest with one row per archive/strategy containing:

- Archive name and timestamp.
- Strategy and source member path.
- SHA-256 of archived strategy source.
- Sanitized configuration hash with credentials removed.
- Timerange, timeframe, detail timeframe, protections, trades, return, PF, drawdown, Sharpe/Sortino, expectancy, and pair concentration.
- Effective per-side fee derived from trade fields such as `fee_open`/`fee_close` when the archived config reports `fee: null`.

Do not compare contradictory results by strategy class name alone. First group by source hash and effective configuration. Diff archived source against current source. Unit corrections—especially `minimal_roi` keys interpreted as elapsed minutes rather than candles—require rerunning every split.

## 3. Development selection without winner-picking

Screen all predeclared architectures under identical assumptions. Select only candidates that pass every gate. If none pass:

1. Record “no development candidate” rather than choosing the least negative result.
2. Do not open validation or holdout.
3. At most run the predeclared bounded neighborhood, if the protocol allowed one.
4. Prefer a broad stable plateau across adjacent settings and calendar years over the single highest return.
5. Close the cycle if the neighborhood is unstable.

A useful uncertainty check is both naive trade bootstrap and calendar-month block bootstrap. Report a 95% total-profit interval and `P(total > 0)`. Wide intervals spanning zero, PF near 1, low Sharpe, or high mean-profit p-values are evidence against promotion even when nominal return is positive.

## 4. Timeframe and configuration traps

Freqtrade configuration overrides strategy-class attributes. A base config containing `"timeframe": "1h"` will silently run a class intended for 4h at 1h unless the command supplies `--timeframe 4h` or a dedicated config. Confirm resolved timeframe in logs before accepting any result. The detail timeframe must be strictly smaller than the strategy timeframe.

Run every strategy list/backtest without duplicating the normal strategy directory as an extra `--strategy-path`; duplicate discovery can create misleading duplicate class listings.

## 5. Bias tools: verify semantic success, not only process exit

`lookahead-analysis` forces market orders, changes wallet/stake/max-open-trades, and disables protections. It is a bias test, not a profitability run. Supply an analysis-only override after the primary config:

```json
{
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market",
    "stoploss_on_exchange": false
  },
  "entry_pricing": {"price_side": "other"},
  "exit_pricing": {"price_side": "other"}
}
```

Require the final result table to state `has_bias: No` with nonzero analyzed signals. A wrapper or CLI process can report exit code 0 while the log contains `ERROR - Configuration error`; inspect the tail/result table before marking a check complete.

For `recursive-analysis`:

- Use one liquid pair and at least ~5,000 strategy candles for the benchmark.
- Test startup counts around the strategy requirement and realistic exchange retrieval limits.
- If a requested startup count exceeds the exchange limit, rerun with the highest accepted odd count; treat the first run as failed even if its process wrapper returned success.
- Interpret indicator variance at the startup count actually usable in dry/live operation; do not demand mathematical zero when EMA variance is decision-irrelevant.

## 6. Execution and robustness ladder

For a candidate that survives development, run separate, labeled tests:

1. Baseline explicit fee and strategy order assumptions.
2. Market-order/opposite-side pricing override at the baseline fee.
3. Adverse all-in per-side fee incorporating extra spread/slippage.
4. One additional signal-bar delay for both entry and exit, implemented as a stress-only subclass—not a selectable candidate.
5. Protections enabled versus disabled, with the protection-enabled run used for promotion.
6. Per-year/regime, per-pair, exit-reason, exposure, rejected-signal, and drawdown-duration analysis.
7. Lookahead and recursive analysis.
8. Locked validation, then a single holdout reveal only if all earlier gates pass.
9. Sustained dry-run before any live consideration.

A tiny edge erased by a modest fee increase or one-bar delay is not defensible. Do not promote it merely because it passes lookahead analysis.

## 7. Reporting

Lead with the decision:

- `PROMOTE TO DRY-RUN`, or
- `NO DEFENSIBLE EDGE — HOLDOUT UNTOUCHED`.

Then report the exact completed and incomplete gates. Distinguish “started” from “verified.” Never describe a created but unexecuted stress class, background process, or delegated expert report as completed evidence.
