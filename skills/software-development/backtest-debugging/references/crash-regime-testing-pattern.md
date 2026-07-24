# Crash-Regime Testing Pattern

When verifying a backtest engine handles extreme markets correctly, use fixed targets
(target_b=1.0, cost=0.0) to isolate engine resilience from signal timing.

## Why signal-aware tests fail for crash scenarios

The TS MOM trend signal requires 100+ days of data and a clear uptrend to produce
target_b > 0. Synthetic crash data (sharp V-dip, extended bear) often lacks enough
pre-crash trend history for the signal to trigger, so the strategy stays flat and the
crash never enters the NAV. The test sees -5% DD instead of -40%.

## Pattern

```python
def test_crash_regime():
    """Test engine handles a -35% crash correctly."""
    n = 330
    dates = pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC")

    # Build synthetic price with crash
    pre_close = 100.0 * np.cumprod(1.0 + rng.normal(0.001, 0.015, 200))
    crash_ret = (1.0 - 0.35) ** (1.0 / 30) - 1.0
    crash_close = pre_close[-1] * np.cumprod(np.full(30, 1.0 + crash_ret))
    recovery_close = crash_close[-1] * np.cumprod(1.0 + rng.normal(0.0005, 0.01, 100))
    close = np.concatenate([pre_close, crash_close, recovery_close])
    close_s = pd.Series(close, index=dates)

    # FIXED targets — always long, no signal dependency
    targets = pd.DataFrame(
        {"target_a": 0.0, "target_b": 1.0, "target_c": 0.0,
         "target_p": 0.0, "target_pv": 0.0},
        index=dates,
    )
    pair_opens = pd.DataFrame({"PAIR/USDT": close_s})
    pair_closes = pd.DataFrame({"PAIR/USDT": close_s})

    # cost=0 — daily full-notional cost obscures DD measurement
    result = simulate_sleeves(targets, pair_opens, pair_closes,
                              pair="PAIR/USDT", cost=0.0)
    m = compute_metrics(pd.DataFrame({"nav": result["nav"]}), annual_days=365)

    # Verify crash shows up in metrics
    assert m["max_drawdown"] < -0.10
```

## Why cost=0 is necessary

`simulate_sleeves` charges cost on full notional EVERY day (Pitfall 7). Over 200+
trading days at 0.20% daily cost, total costs exceed 40% of starting NAV. This
obscures the actual drawdown from the crash. Use cost=0 for engine verification
tests and cost=0.0020 for realistic backtests.

## Multi-sleeve NAV dilution

The combined NAV (`result["nav"]`) is the sum of 5 sleeves (a, b, c, p, pv) each
starting at SLEEVE_WEIGHT=0.20. Even when all sleeves except one are flat (target=0),
the flat sleeves contribute 0.80 of NAV, diluting the active sleeve's DD. A -47%
asset drawdown might only show as -11% in combined NAV. This is correct engine
behavior — the crash test should verify the engine handles extremes, not that
combined NAV DD matches asset DD.

For tests that need to verify asset-level DD, use `result["sleeve_b"]` directly:

```python
m = compute_metrics(pd.DataFrame({"nav": result["sleeve_b"]}), annual_days=365)
assert m["max_drawdown"] < -0.30  # closer to asset DD
```

## Crash scenario catalog

| Scenario | Crash % | Days | Recovery | Tests |
|----------|:-------:|:----:|----------|-------|
| V-shape ("flash crash") | -20% | 5 | 5-day bounce | Engine handles sharp reversals |
| Extended bear | -45% | 180 | 125-day drift | 2022-crypto-style grind down |
| Single sharp decline | -35% | 30 | 100-day recovery | Most common crash pattern |
| No crash (bull) | 0% | 0 | N/A | Ensure engine doesn't flag false DD |
