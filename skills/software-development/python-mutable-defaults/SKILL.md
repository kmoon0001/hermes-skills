---
name: python-mutable-defaults
description: "Detect and fix Python mutable-default-arg pattern that causes module-level constant overrides to silently fail. Covers the setattr trap, lazy-lookup pattern, and detection heuristics."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [python, debugging, gotchas, mutable-defaults, module-constants]
    related_skills: [systematic-debugging, test-driven-development]
---

# Python Mutable Default Arguments — Module Constant Trap

## Overview

Python evaluates default parameter values at **function definition time**, not call time. When a function signature uses a module-level constant as its default, that constant's value is baked into the function's `__defaults__` tuple. Changing the module attribute later via `setattr()` has **zero effect** on the function behavior, even though `module.CONSTANT` reads correctly after the setattr.

This causes silent failures in parameter sweeps, config overrides, and experiment runners that use `setattr` to modify constants.

## When to Suspect

- A parameter sweep produces **identical results** for every value of a parameter
- `setattr(module, "CONSTANT", new_value)` changes `module.CONSTANT` (verified by reading it back) but function behavior doesn't change
- The function body references the constant via a **default parameter**, not directly

## Detection

Check function signatures for this pattern:

```python
# SUSPECT — constant baked in at import time
def compute_scale(vol, target: float = VOLATILITY_TARGET):
    scale = target / vol  # target is always the import-time value
```

The function's `__defaults__` tuple holds the captured value:

```python
# Check what's actually baked in
print(compute_scale.__defaults__)  # (0.4,) — the import-time value
```

## Fix — Lazy Lookup Pattern

```python
# FIXED — None triggers module-level lookup at call time
def compute_scale(vol, target: float | None = None):
    if target is None:
        target = VOLATILITY_TARGET  # looked up fresh every call
    scale = target / vol
```

After fix, `setattr(module, "VOLATILITY_TARGET", 0.15)` correctly propagates to all calls.

## Other Functions Commonly Affected

Any function where a module constant appears as a default parameter:

```python
def compute_funding_fade(series, percentile: float = FUNDING_FADE_PERCENTILE, ...)
def compute_oi_divergence_factor(trend, oi, reduction: float = OI_DIVERGENCE_REDUCTION)
def compute_vol_scale(vol, target: float = VOLATILITY_TARGET)
```

## Multi-File Constant Propagation

When fixing the default-arg bug, the constant may be defined in **multiple files**. A single sweep or config may need to override the same constant in 2+ modules (e.g., `cycle5_backtest.VOLATILITY_TARGET` and `cycle6_backtest.VOLATILITY_TARGET` both exist independently). Search the entire codebase for the constant name before declaring it fixed:

```bash
grep -rn "^VOLATILITY_TARGET" research/
```

Every definition site needs the lazy-lookup pattern, and every `setattr` call must set ALL of them.

## Parameter Sweep Approach

When running parameter sweeps that modify module constants, use **clean subprocess per run** instead of in-process `setattr`. On **Windows**, subprocess sweeps may consistently hang (Python process startup + heavy imports can deadlock). Alternatives when subprocess fails:

```python
import subprocess, sys
# Write a runner script that applies overrides, runs experiment, prints result
# Each subprocess is a clean Python import → no stale state
proc = subprocess.run([sys.executable, "-B", str(runner_path)], ...)
```

Each subprocess is a clean Python import → no stale state. On Windows, subprocess import overhead makes each run ~3 min even for simple experiments; factor this into timeout estimates.

### Windows Subprocess Hang

On Windows, `subprocess.run([sys.executable, "-c", code])` may **hang indefinitely** when the child process imports large libraries (pandas, numpy, pyarrow). This appears to be related to Windows process initialization + DLL loading. Workarounds:

1. **Run directly in Hermes terminal** instead of subprocess — use `importlib.reload()` to reset module state between runs
2. **Set a hard timeout** with `subprocess.run(..., timeout=600)`
3. **Use importlib.reload** pattern:
   ```python
   import research.module as mod
   setattr(mod, "CONSTANT", new_value)
   importlib.reload(mod)  # force re-load with new constants
   from research.module import some_function
   result = some_function()
   ```
   Note: reload has its own edge cases — functions defined in the module get fresh `__defaults__`, but state from other imported modules may persist.

### Phantom Fast Sweep

Key sign that setattr overrides are NOT working: the sweep finishes "fast" (every run takes the same short time) and produces **nearly identical metrics** across different parameter values. This happens because the defaults mask the override — the function uses the import-time value regardless of what you set.

After fixing the bug (lazy lookup), the first real override run will be significantly **slower** (e.g., 3 min → 5 min) because the bootstrap and signal chains now run with the actual parameter values for the first time. This is correct behavior, not a regression — the old "fast" run was silently short-circuiting.

## Verification

```python
# Before fix — test that override actually propagates
mod = sys.modules["research.module"]
setattr(mod, "CONSTANT", 0.15)
result = mod.some_function(test_data)
# If result == result_at_0.40 → mutable default trap
# If result differs → override works
```
