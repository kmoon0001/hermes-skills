# Pipeline Resilience Testing Pattern

Test every failure node in the production pipeline — missing data, corrupt files,
empty inputs, edge-case data. These tests verify the pipeline completes without
crashing, even when all upstream dependencies fail.

## Failure nodes to cover

| Node | Test pattern |
|------|-------------|
| Missing feather file | Mock all downloads to return non-zero exit codes |
| Corrupt feather file | Monkeypatch `pd.read_feather` to raise OSError |
| Empty DataFrame | Return `pd.DataFrame()` from read_feather |
| All downloads fail | Verify 5 pairs attempted, pipeline completes |
| NaN in price data | Feed NaN-infested NAV to compute_metrics |
| Single data point | NAV with 1 row → should return NaN metrics, not crash |
| Flat NAV (no returns) | NAV of all 1.0 → Sharpe should be 0 |
| Negative prices | NAV going below 0 → produce sensible metrics |
| Zero volume | Volume=0 everywhere → volume filter should not trigger |

## Example: corrupt file resilience

```python
def test_corrupt_feather_file_graceful(tmp_path):
    """A corrupted feather file should be skipped with a warning."""
    from production import generate_signals as gs

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(gs, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gs, "_get_current_equity", lambda: 1000.0)

    # Make read_feather throw OSError
    monkeypatch.setattr(
        pd, "read_feather",
        lambda p, **kw: (_ for _ in ()).throw(OSError("corrupt file")),
    )
    monkeypatch.setattr(
        gs.subprocess, "run",
        lambda *a, **kw: type("R", (), {"returncode": 0})(),
    )

    # Should not crash
    gs.main()
```

## Example: NaN in price data

```python
def test_nan_in_price_data_not_crash():
    nav = pd.Series(
        [1.0, 1.05, float("nan"), 1.08, 1.15],
        index=pd.date_range("2021-01-01", periods=5, freq="D"),
    )
    result = pd.DataFrame({"nav": nav})
    m = compute_metrics(result, annual_days=365)
    # Should produce dict even if metrics are NaN
    assert isinstance(m, dict)
```

## integration test: full pipeline output validation

```python
def test_full_run_outputs_valid_json(tmp_path):
    monkeypatch.setattr(gs, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(gs, "_get_current_equity", lambda: 1000.0)
    monkeypatch.setattr(gs.subprocess, "run",
                        lambda *a, **kw: type("R", (), {"returncode": 1})())
    gs.main()

    out = tmp_path / "signals.json"
    assert out.exists()
    data = json.loads(out.read_text())
    for key in ("generated_at", "equity", "signals", "positions"):
        assert key in data
    assert isinstance(data["equity"], (int, float))
    assert data["equity"] > 0
    assert isinstance(data["positions"], list)
```

## Running

```bash
.venv/Scripts/python -m pytest tests/test_stress_crash_resilience.py -v
```
