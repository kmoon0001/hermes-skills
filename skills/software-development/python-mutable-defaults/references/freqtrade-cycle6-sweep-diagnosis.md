# Mutable Default Arg Diagnosis — Freqtrade Cycle 6 Parameter Sweep

## Session 2026-07-19

### Symptom
The parameter sweep script (`param_sweep.py`) used `setattr(module, "VOLATILITY_TARGET", 0.15)` to override constants. A simple test showed `module.VOLATILITY_TARGET == 0.15` after setattr, but `compute_vol_scale_from_parkinson()` returned the same result regardless of override value.

### Root Cause
The function signature was:
```python
def compute_vol_scale_from_parkinson(parkinson_vol, target: float = VOLATILITY_TARGET):
```

Python evaluated `VOLATILITY_TARGET` (0.40) once when the `def` statement executed during module import. The default value `0.40` was captured in the function's `__defaults__` tuple. Changing `module.VOLATILITY_TARGET` to 0.15 later had no effect because the function never re-reads the module attribute — it uses the captured default.

### Evidence
```python
# After setattr, module reads correctly
mod = sys.modules["research.cycle6_backtest"]
setattr(mod, "VOLATILITY_TARGET", 0.15)
print(mod.VOLATILITY_TARGET)  # 0.15  ← correct!

# But the function uses the captured default
print(compute_vol_scale_from_parkinson.__defaults__)  # (0.4,)  ← baked in!

# So the function ignores the setattr
result = compute_vol_scale_from_parkinson(test_data)
# result == same as if VOLATILITY_TARGET were 0.40
```

### Fix Applied
Changed the function signature to the lazy-lookup pattern:
```python
def compute_vol_scale_from_parkinson(parkinson_vol, target: float | None = None):
    if target is None:
        target = VOLATILITY_TARGET  # read fresh every call
    scale = target / parkinson_vol
```

Same fix applied to:
- `compute_funding_fade(percentile=None)` — looks up `FUNDING_FADE_PERCENTILE`
- `compute_oi_divergence_factor(reduction=None)` — looks up `OI_DIVERGENCE_REDUCTION`

### Remaining Issue
Even after the lazy-lookup fix, the in-process setattr approach still failed because other module-level state (cached DataFrames, random state, experiment runner state) leaked between consecutive runs in the same process.

### Final Sweep Approach
Switched to **clean subprocess per run** — each parameter combination runs in its own Python process via `subprocess.run`. This avoids both the mutable-default trap AND all module-level state leakage.

### Files Changed
- `research/cycle6_backtest.py` — 3 function signatures refactored to lazy-lookup pattern
- `research/param_sweep.py` — rewritten from in-process setattr to subprocess-per-run

### Bootstrap Performance Insight (Codex Investigation)

The experiment runner appeared to "hang" (5-8 min vs ~3 min) when constants changed from defaults. Codex traced this to the **block bootstrap** (20,000 replicates). The default config produced invalid NAV values (C-B = -5.6%), causing the bootstrap to skip/fail early — making it appear fast. The optimized config (C-B = +0.17%) passed all gates, ran the full bootstrap, and took the full time.

**Lesson:** "Hangs" after parameter changes may be the expensive computation running **correctly** for the first time, not a bug. Check if the "fast" baseline was skipping validation gates or bootstrap due to invalid intermediate values.
