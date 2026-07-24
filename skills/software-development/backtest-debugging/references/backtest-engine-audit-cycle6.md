# Backtest Engine Audit — Cycle 6 / Cycle 5

Full report: `audit/backtest_audit.md` in the freqtrade repo.

## Key Findings Referenced by the Skill

| Bug | Sleeve Impact | Category | Doc Link |
|-----|--------------|----------|----------|
| C1: Full-notional daily cost | All sleeves, all cycles | Cost | SKILL.md Pitfall 7 |
| C2: P-sleeve ignores target_p=0 | Cycle 5 nav inflated | Aggregation | SKILL.md Pitfall 1 (extended) |
| C3: run_cycle5 uses r["nav"] with P | Cycle 5 metrics wrong | Aggregation | SKILL.md Pitfall 1 |
| M1: Anti-volatility cost bias | All, regime-dependent | Cost interaction | SKILL.md Pitfall 7 (extended) |
| m1: _cap fillna(1.0) | Cycle 6 only | NaN edge case | SKILL.md Pitfall 4 |
| m2: setattr global mutation | walkforward/expanding | Methodology | SKILL.md new Pitfall 10 |

## Cost Impact Magnitudes

For relevant conversations, quote these numbers:

**C1 magnitude (Cycle 6 B-only, vt=0.30, cost=20bps):**
- Wrong cost: 0.30 × 0.002 = 0.06% of sleeve NAV daily
- Correct cost (turnover-based): ~0.002% on typical vol-change days
- Annualized drag gap: 12–20pp of sleeve NAV

**M1 interaction (anti-volatility bias):**
When realized vol is low (calm trending), vol_scale is HIGH (≈1.0), so target allocation is HIGH. Cost = high notional × cost_rate = HIGH.
When realized vol is high (crash spikes), vol_scale is LOW (≈0), so target allocation is LOW. Cost = low notional × cost_rate = LOW.
Result: strategy pays MORE cost during the best trending periods and LESS during protective periods — overstates the cost of trend-following.

## Fix Patterns

### Fix 1: Cost on turnover (replaces Pitfall 7 snippet)
```python
def simulate_with_turnover_cost(nav, target, price, cost=0.001):
    """Costs only when target allocation changes."""
    prev_notional = 0.0
    prev_target = 0.0
    for t in range(1, len(nav)):
        new_target = float(target[t-1])
        new_notional = float(nav[t-1] * new_target)
        delta = abs(new_notional - prev_notional)
        cost_charge = delta * cost
        nav[t] = nav[t] - cost_charge  # approximate; real impl on notional
        prev_notional = new_notional
    return nav
```

### Fix 2: P-sleeve respects target_p (replaces Pitfall 1 workaround)
```python
if target_p_series.iloc[t-1] > 0:
    passive[t] = passive[t-1] * (closes[pair].iloc[t] / closes[pair].iloc[t-1])
else:
    passive[t] = SLEEVE_WEIGHT * target_p_series.iloc[t-1]
```

### Fix 3: Replace setattr with call-time parameters
Use `__init__` or factory functions instead of monkey-patching module globals.
