# MaxDD Sign Convention — Cross-File Audit Template

Use this template when running a sign convention audit across all result JSONs.

## Audit Procedure

### 1. List ALL result JSONs in the repo
```bash
find research/ production/ stocks/ -name "*results*.json" -o -name "*comparison*.json" 2>/dev/null | sort
```

### 2. For each file, extract max_drawdown values and check sign
```python
import json
from pathlib import Path

def audit_signs(root="research"):
    """Print sign audit table for all JSONs."""
    print(f"{'File':<50} {'Key':<20} {'Value':>12} {'Sign':>8}")
    print("-" * 92)
    for path in sorted(Path(root).rglob("*.json")):
        try:
            data = json.loads(path.read_text())
            for k, v in _walk_maxdd(data):
                sign = "NEGATIVE ✓" if v <= 0 else "POSITIVE ✗"
                rel = str(path).replace("\\", "/")
                print(f"{rel:<50} {k:<20} {v:>12.4f} {sign:>8}")
        except Exception:
            pass

def _walk_maxdd(obj, prefix=""):
    """Recursively find all max_drawdown / max_dd values."""
    results = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("max_drawdown", "max_dd") and isinstance(v, (int, float)):
                results.append((f"{prefix}.{k}" if prefix else k, v))
            elif isinstance(v, (dict, list)):
                results.extend(_walk_maxdd(v, f"{prefix}.{k}" if prefix else k))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            results.extend(_walk_maxdd(item, f"{prefix}[{i}]"))
    return results
```

### 3. Run the fixer on files with positive values
```python
def negate_maxdd(obj):
    """Negate any positive max_drawdown/max_dd values in-place."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("max_drawdown", "max_dd") and isinstance(v, (int, float)) and v > 0:
                obj[k] = -v
            elif isinstance(v, (dict, list)):
                negate_maxdd(v)
    elif isinstance(obj, list):
        for item in obj:
            negate_maxdd(item)
    return obj

def fix_signs(root="research"):
    """Fix all JSONs with positive max_drawdown."""
    for path in Path(root).rglob("*.json"):
        try:
            data = json.loads(path.read_text())
            fixed = negate_maxdd(data)
            path.write_text(json.dumps(fixed, indent=2, default=str) + "\n")
            print(f"Fixed: {path}")
        except Exception as e:
            print(f"Error: {path} - {e}")
```

## Common Failure Patterns

### Pattern 1: compute_metrics returns positive, some runners flips it
`compute_metrics → float(-np.min(drawdown))` = positive.
Some experiment runners negate this after calling compute_metrics; others don't.
The fix must be applied at the compute_metrics level or consistently at every writer.

### Pattern 2: New runner inherits the bug
When a new experiment runner copies the code pattern from an older runner but misses the sign flip, its JSONs will have positive values. Cycle 9 copied from Cycle 6 but the sign flip was in the main() output dict construction, which was different between the two runners.

### Pattern 3: Summary JSONs inherit signs from source
If a comparison JSON quotes max_dd from source result JSONs, and the source had a positive sign, the summary inherits the wrong convention. Always audit source + summary together.

## Example Audit (Cycle 5/6/9, July 2026)

| File | MaxDD Value | Sign | Status |
|------|------------|------|--------|
| cycle6_results.json | -0.3459 | NEGATIVE | Correct |
| cycle6_expanding_window_results.json | -0.3459 (all windows) | NEGATIVE | Correct |
| cycle5_results.json | -0.6651 | NEGATIVE | Correct |
| cycle9_results_ew.json (B) | +0.2503 | POSITIVE | **Wrong** |
| cycle9_risk_parity_comparison.json (EW) | +0.2503 | POSITIVE | **Wrong** |
| cycle9_risk_parity_comparison.json (RP) | +0.2808 | POSITIVE | **Wrong** |
| cycle9_results_ew.json (C/D/E) | +0.199-0.235 | POSITIVE | **Wrong** |
| feature_backtest_results.json (all) | +0.058-0.089 | POSITIVE | **Wrong** |
