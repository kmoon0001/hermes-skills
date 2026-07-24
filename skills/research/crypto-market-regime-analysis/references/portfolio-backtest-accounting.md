# Causal Multi-Asset Portfolio Backtest Accounting

Use this reference when a crypto hypothesis changes portfolio sleeves on a daily or weekly schedule. It supplements `strategy-robustness-protocol.md` with implementation details that prevent timing and accounting errors.

## Separate four clocks

Represent these events explicitly rather than collapsing them into one row:

1. **Observation:** the final completed bar allowed into the signal.
2. **Decision:** the timestamp at which the target allocation is calculated.
3. **Execution:** the first executable open after the decision.
4. **Return accrual:** the interval over which the executed holdings earn P&L.

Example for weekly crypto rules: form the signal from the completed Sunday UTC daily close, change holdings at Monday 00:00 UTC open, then accrue Monday-open to Tuesday-open return. Never apply Sunday's signal to a return that began before Monday execution.

## Preserve target updates, not forward-filled target weights

Store allocation changes only on rebalance rows; leave non-rebalance rows null. The simulator should distinguish:

- **null row:** hold existing units and allow weights to drift;
- **numeric row:** rebalance to the new target;
- **numeric zero:** sell the sleeve and hold cash.

Forward-filling target weights and multiplying them by daily returns silently assumes cost-free daily rebalancing. That can materially alter return, volatility, and turnover.

## Event-driven NAV accounting

At each execution timestamp:

1. Compute pre-trade NAV from cash plus marked asset values.
2. Compute current weights from those marked values.
3. Turnover is `sum(abs(target_weight - current_weight))`.
4. Trading cost is `pretrade_NAV * turnover * one_way_cost`.
5. Deduct cost, then set asset values to target weights of post-cost NAV; residual stays cash.
6. Between rebalances, hold units/asset values and let weights drift with price.

For each return interval, record asset-level net contributions so that:

`sum(asset_net_contributions) == portfolio_return`

This equality should be a unit-test invariant.

## Common eligibility and matched controls

Warmups can create misleading comparisons. Apply every attribution cell over the same first eligible execution date and same ending date.

For a directional signal combined with volatility scaling, report all four fixed cells:

- A: always-long, unscaled;
- B: always-long, volatility-scaled;
- C: signal, unscaled;
- D: signal, volatility-scaled.

Primary directional attribution is D minus B; C minus A checks whether the signal adds value without the scaling overlay. Compare Sharpe and tail risk as well as return because a timing rule often lowers exposure.

Do not promote a control merely because it wins. If the control was not a preregistered candidate with promotion gates, its result is exploratory. Before consuming validation, subject it to its own causal delay, temporal breadth, block-bootstrap, best-period deletion, and leave-one-asset-out checks.

## Missing and stale data

- Aggregate only complete source-bar groups (for example, exactly 24 unique hourly bars per UTC day).
- Do not fabricate returns across gaps.
- Missing or stale data forces the affected sleeve to cash; do not redistribute it unless redistribution was preregistered.
- Start at the latest common eligible date when matched cells or assets require different warmups.

## Required deterministic tests

1. **Aggregation completeness:** incomplete days are excluded.
2. **Signal boundary:** first non-null signal occurs only after the full longest lookback.
3. **Execution timing:** a Sunday decision first appears as a Monday update.
4. **No redistribution:** an inactive sleeve remains cash.
5. **Volatility cap:** scaling never exceeds one and is null before its full lookback.
6. **Exact cost example:** verify NAV, turnover, and cost with hand-computable prices.
7. **No hidden rebalance:** a non-update day has zero turnover and drifting weights.
8. **Contribution identity:** asset contributions sum to portfolio return on every row.
9. **Future truncation:** removing future rows leaves every earlier signal, target, and completed return bit-identical.
10. **Cell alignment:** all attribution cells have identical evaluation indices.

## Interpreting a negative result

A positive absolute return is not evidence of signal alpha when the matched always-long control performs better. A lower drawdown is also insufficient if it comes primarily from lower exposure and the signal has a lower Sharpe ratio.

If the primary estimate is negative and fails temporal, breadth, delay, cost, and bootstrap gates, stop. Do not run search-adjusted tests as a rescue attempt and do not tune adjacent lookbacks against the same development sample.
