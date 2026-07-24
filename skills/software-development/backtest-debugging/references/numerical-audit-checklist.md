# Numerical & Methodology Audit Checklist

A runnable 9-category checklist for backtest engine audits. Based on the July 2026 freqtrade engine audit. Run every category — a pass that only reports bugs but doesn't confirm clean areas is incomplete.

## Category A: Cost Handling

```bash
# Check: cost on full notional or turnover only?
grep -A5 "nav\[t\].*=.*cost\|nav\[t\].*\*=.*cost" research/*.py stocks/*.py

# Check: cost=0 sanity check — NAV must match B&H exactly
python -c "
import numpy as np; import pandas as pd
# Simulate with target=1.0 always long, cost=0
# NAV must equal buy_and_hold_nav
# If not: allocation lag or full-notional cost bug
"
```

## Category B: NaN / Missing Data

```bash
# Find all fillna / fill calls with their values
grep -rn "fillna\|\.fill(" --include="*.py" research/ stocks/ | grep -v ".venv"

# Check _cap functions specifically
grep -A10 "def _cap" research/*.py stocks/*.py
```

## Category C: Methodology / Sleeve Contamination

```bash
# Check NAV aggregation in every runner
grep -rn "r\[\"nav\"\]\|result\[\"nav\"\]" --include="*.py" research/ stocks/

# Check SLEEVE_WEIGHT normalization (div by SLEEVE_WEIGHT)
grep -rn "SLEEVE_WEIGHT" --include="*.py" research/ stocks/ | grep -v "^.*:#"

# Check per-sleeve usage (sleeve_b vs nav)
grep -rn "sleeve_b\|sleeve_c\|sleeve_pv" --include="*.py" research/ stocks/ | grep -v "\.venv"
```

## Category D: State Management

```bash
# Find setattr / module constant mutation
grep -rn "setattr\|\.START\s*=\|\.END\s*=\|\.VOLATILITY_TARGET\s*=" --include="*.py" research/ stocks/ | grep -v ".venv" | grep -v "test_"

# Check for sys.modules manipulation
grep -rn "sys.modules" --include="*.py" research/ stocks/
```

## Category E: Sign Convention (Data Integrity)

```bash
# Double-negative maxDD pattern (should return NOTHING)
grep -rn "float(-np.min(drawdown))" --include="*.py" research/ stocks/

# Recursive sign walker over all JSONs
python -c "
import json; from pathlib import Path
for p in Path('research').glob('*results*.json'):
    d = json.loads(p.read_text())
    def walk(obj, path=''):
        if isinstance(obj, dict):
            for k,v in obj.items():
                if k in ('max_drawdown','max_dd','dd') and isinstance(v,(int,float)) and v>0:
                    print(f'{p.name}: POSITIVE at {path}.{k}={v:.4f}')
                walk(v, f'{path}.{k}')
        elif isinstance(obj, list):
            for i,it in enumerate(obj):
                walk(it, f'{path}[{i}]')
    walk(d)
"
```

## Pass F: Numerical Formula Verification

```bash
# Verify CAGR formula
grep -A3 "cagr.*=.*float.*exp\|cagr.*=.*np\.exp" research/*.py stocks/*.py

# Verify Sharpe formula (simple returns vs log returns)
grep -B1 -A1 "sharpe.*=.*float.*mean.*rets.*std\|sharpe.*=.*np\.mean" research/*.py stocks/*.py

# Verify max_drawdown formula
grep -B1 -A1 "max_drawdown.*=.*float.*np\.min\|max_drawdown.*=.*min\|dd.*=.*float.*cummax\|dd.*=.*nav.*cummax" research/*.py stocks/*.py

# Verify Parkinson vol formula
grep -A3 "parkinson.*=.*np\.log.*high.*low\|4 \* np\.log(2)" research/*.py

# Annualization consistency
grep -rn "ANNUALIZATION_DAYS\|= 252\|= 365" --include="*.py" research/ stocks/ | grep -v ".venv"
```

## Pass G: Security

```bash
# Hardcoded secrets
grep -rn "api_key\|secret\|token\|password\|jwt_secret" --include="*.py" . | grep -v ".venv" | grep -v "test_"

# subprocess injection
grep -rn "subprocess.run.*f\"\|subprocess.run.*f'\|os\.system\|exec(\|eval(" --include="*.py" . | grep -v ".venv" | grep -v "test_"
```

## Pass H: Error Propagation

```bash
# Non-atomic writes (direct write vs .tmp + rename)
grep -rn "write_text\|\.write(" --include="*.py" research/ production/ | grep -v ".venv" | grep -v "test_"

# Missing try/except around JSON reads
grep -rn "json.load\|json.loads" --include="*.py" research/ production/ | grep -v ".venv" | grep -v "test_"
```

## Pass I: Type Safety

```bash
# Mutable defaults
grep -rn "def .*=\[\]\|def .*={}" --include="*.py" research/ stocks/ production/

# Implicit or-trap
grep -rn "\.get(.*) or " --include="*.py" research/ stocks/ production/ | grep -v ".venv"
```

## Pitfall-Specific Checks

### Pitfall 0 (SLEEVE_WEIGHT double-compound)
```bash
grep -rn "SLEEVE_WEIGHT" --include="*.py" research/ stocks/ | grep -v "^.*:#"
# All experiment runners should have / SLEEVE_WEIGHT in NAV aggregation
```

### Pitfall 1 (P-sleeve ignores target_p)
```bash
grep -A5 "P sleeve\|passive\[0\]\|sleeve_p" research/cycle5_backtest.py
# Must have: if target_p_series.iloc[t-1] > 0 else cash
```

### Pitfall 13 (off-by-one allocation lag)
```bash
# Verify: target_alloc (not prev_target_alloc) drives NAV
grep -A2 "target_alloc\|prev_target_alloc" research/cycle5_backtest.py
# Cost=0 sanity check must produce exact B&H
```

### Pitfall 14 (P/PV asymmetry)
```bash
# Check both else branches
grep -A2 "else:" research/cycle5_backtest.py
# P-sleeve else: passive[t] = passive[t-1] (cash flat)
# PV-sleeve else: passive_vol[t] = SLEEVE_WEIGHT * target_pv (ZEROES — BUG)
```

### Pitfall 16 (feature backtest NAV field)
```bash
grep -rn "result\[\"nav\"\]" --include="*.py" research/ | grep -v ".venv"
# Should be result["sleeve_b"] or equivalent
```

### Pitfall 17 (duplicated compute_metrics)
```bash
grep -rn "def compute_metrics\|def _compute_metrics\|def metrics\|def compute_metrics_from_nav" --include="*.py" research/ stocks/ | grep -v ".venv"
# Any duplicate of the canonical version is a risk
```

## After-Fix Verification

1. **Cost=0 sanity check** — always-long NAV = B&H
2. **Re-run dev period** — compare before/after
3. **Re-run OOS period** — verify out-of-sample
4. **Vol target sweep** — must be monotonic (higher vt = higher CAGR AND Sharpe)
5. **Commit corrected results** — versioned JSONs, don't overwrite
