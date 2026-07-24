# Production Gap-Coverage Testing Pattern

## When to Use

After an audit identifies untested high-risk code paths in production pipeline code
(trade execution, logging, alerts, strategy indicators). Apply systematic TDD gap
coverage: write failing test, watch it fail, fix or verify, run full suite QA.

## Testing Production File-I/O Code

Production modules often read/write JSON files at hardcoded paths. To test in isolation:

### Monkeypatch paths to tmp_path
```python
monkeypatch.setattr(tl, "SIGNALS_PATH", tmp_path / "signals.json")
monkeypatch.setattr(tl, "POSITIONS_PATH", tmp_path / "positions.json")
monkeypatch.setattr(tl, "HISTORY_PATH", tmp_path / "trade_history.json")
monkeypatch.setattr(tl, "CONFIG_PATH", tmp_path / "config.json")
monkeypatch.setattr(tl, "DATA_DIR", tmp_path)
```

For module-level attributes accessed inside functions, use string-based monkeypatch:
```python
monkeypatch.setattr("production.execute_trades.TRADE_HISTORY_PATH", hist_path)
```

### Freeze time for idempotency tests
When testing idempotency or time-dependent behavior:
```python
monkeypatch.setattr(tl, "_today_str", lambda: "2026-07-21T12:00:00Z")
```

### Create temp feather data
```python
dates = pd.date_range("2026-07-01", "2026-07-21", freq="D", tz="UTC")
df = pd.DataFrame({
    "date": dates, "open": [...], "high": [...], "low": [...],
    "close": [...], "volume": [...],
})
df.reset_index(drop=True).to_feather(str(tmp_path / "BTC_USDT-1d.feather"))
```

### Seed initial state
Write the initial JSON state files before calling the function under test:
```python
(tmp_path / "trade_history.json").write_text(json.dumps(initial_history))
(tmp_path / "signals.json").write_text(json.dumps(signals_data))
(tmp_path / "positions.json").write_text(json.dumps(positions_data))
```

## Gap-Coverage Workflow

1. **Identify the gap** — read the source, find the untested code path
2. **Write failing test** (RED) — construct minimal fixture showing expected behavior
3. **Run to confirm it fails** — verify the failure is because of the gap, not a syntax error
4. **Fix the code or verify it's correct** (GREEN)
5. **Run the specific test** — confirm it passes
6. **Run full suite** — verify no regressions: `pytest tests/ -x --tb=short -q`
7. **Log the result** — code fix needed, or code was correct (test added as regression guard)

## Common Pitfalls

### numpy bool vs Python bool
`result["trend"].iloc[-1]` returns `numpy.bool_`, not Python `bool`.
Use `assert bool(result["trend"].iloc[-1]) is True` instead of `is True`.

### Floating-point threshold edge cases
At exact threshold boundaries (e.g., `94.0/100.0` for exactly -6% stoploss),
IEEE 754 floating point may produce values slightly above or below the
mathematical boundary. Accept either behavior or test one notch away.

### Path.__truediv__ is read-only on Windows
Cannot monkeypatch `Path.__truediv__`. Instead, monkeypatch the module-level
path constants or use string-based setattr.

### Time-sensitive tests
Tests that depend on `datetime.now()` will drift. Use explicit frozen times
via monkeypatching `_today_str` or similar. At exact threshold boundaries
(e.g., "36h ago"), processing overhead adds milliseconds that can push the
result over the threshold.

## Test Categories by Gap Type

| Gap Type | What to Test | Example |
|----------|-------------|---------|
| Idempotency | Same-day rerun → no duplicates | Gap 1 |
| Threshold comparison | Below/above/exactly at boundary, edge cases | Gaps 2, 3, 4, 6 |
| Error resilience | Missing file, corrupt JSON, zero values | Gaps 3, 4 |
| Output contract | Expected columns, bounded values, formula correctness | Gap 5 |
| Determinism | Same input → same output (no state leak) | Gap 8 |
| Logic verification | Correct formula, correct pair matching | Gaps 2, 3, 6 |

## QA Loop

After every gap fix, run the full test suite:
```bash
pytest tests/ -x --ignore=tests/test_cycle2_mtf_strategies.py --tb=short -q
```

Only one code change needed in this session — the `_today_str()` idempotency
bug in trade_logger.py. All other gaps were already correct; tests added as
regression guards confirming existing behavior.
