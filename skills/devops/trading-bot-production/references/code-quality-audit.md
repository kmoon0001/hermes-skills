# Code Quality Audit — Bulletproofing Workflow

Date: 2026-07-23
Purpose: Systematic process for cleaning up and hardening a research-to-production codebase.

## When to Run This

After any major feature push or before handing off to another person. Run it as a
checklist — every step produces actionable output.

## Phase 1: Dead Code Removal

### Step 1: Find orphaned files
```python
from pathlib import Path
root = Path("project_root")
for f in root.rglob("*"):
    if f.is_dir(): continue
    # Check for: .bak, .backup, .okx_backup, files starting with _
    # Also: old docs (CYCLE*.md from superseded cycles), improvement_*.md
    # Also: unused scripts (OPEN-WEB-UI.bat, repair_windows_dns.py, etc.)
```

### Step 2: Find broken references
After deleting files, grep for references to them:
```bash
grep -r "deleted_file_name" . --include="*.py" --include="*.bat" --include="*.md"
```
CHECK-SETUP.bat referenced a deleted repair_windows_dns.py — removed the step entirely.

### Step 3: What to NEVER delete
- `__init__.py` files (Python package markers, even if empty)
- `logs/` directory (runtime artifacts, should be gitignored)
- `.gitkeep` files
- Data files in `user_data/` (production state)

## Phase 2: Code Quality Fixes

### Bare excepts
Every `except:` without a specific exception type is a bug waiting to happen.
Replace with `except (json.JSONDecodeError, KeyError):` or `except Exception:`
at minimum.

```bash
grep -rn "except:" --include="*.py" | grep -v "Exception\|__pycache__"
```

Found 6 in research scripts. Fixed all.

### Strategy name consistency
Three files hardcode the strategy name. They MUST match `user_data/config.json`:
- START-FREQTRADE-DRY-RUN.bat
- START-FREQTRADE-DRY-RUN.ps1
- CHECK-SETUP.bat
```bash
grep -rn "strategy" *.bat *.ps1 user_data/config.json
```

### Exchange references
No production file should hardcode an exchange name. All must import from
`production/exchange_config.py`. Research and test files are exempt.
```bash
grep -rn '"okx"\|/okx' production/ --include="*.py"
```

## Phase 3: Test Coverage

### Audit: which production modules lack unit tests?
```bash
ls production/*.py | while read f; do
  base=$(basename $f .py)
  [ -f "tests/test_${base}.py" ] && echo "TESTED: $base" || echo "GAP: $base"
done
```

Priority order for adding tests:
1. **Data integrity** — exchange_config, validate_data (protect against silent data corruption)
2. **Health monitoring** — watchdog (protect against silent bot failures)
3. **Pipeline** — already covered by integration tests (test_production_pipeline.py)
4. **Reporting** — performance_report, monitor_status (lower priority)

### Test patterns for production modules
- Use `tmp_path` fixture for file-based tests
- Use `patch.object()` for module-level path constants
- Test both happy path AND error cases (missing files, corrupt JSON, stale data)
- Test threshold values (are warning/critical levels reasonable?)
- Test all public API functions return expected types

### Example: exchange_config tests
```python
class TestExchangeConfig:
    def test_get_exchange_defaults_to_okx(self, tmp_path):
        with patch.object(ec, 'CONFIG_FILE', tmp_path / 'nonexistent.json'):
            assert ec.get_exchange() == 'okx'

    def test_set_and_get_exchange(self, tmp_path):
        with patch.object(ec, 'CONFIG_FILE', config_file):
            ec.set_exchange('binance')
            assert ec.get_exchange() == 'binance'

    def test_set_invalid_exchange_fails(self, tmp_path):
        assert ec.set_exchange('nonexistent_exchange') is False
```

## Phase 4: Run & Verify

```bash
# Full test suite
.venv/Scripts/python -m pytest tests/ -q --ignore=tests/test_cycle2_mtf_strategies.py

# Production health
.venv/Scripts/python production/watchdog.py
.venv/Scripts/python production/validate_data.py
.venv/Scripts/python production/performance_report.py --brief
```

## Results from Jul 23 run

| Metric | Before | After |
|--------|:------:|:-----:|
| Dead files | 26 | 0 |
| Bare excepts | 6 | 0 |
| Prod modules with tests | 0 | 3 |
| Total tests | 194 | 221 |
| Broken references | 1 | 0 |
