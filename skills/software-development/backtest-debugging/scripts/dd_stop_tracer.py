"""
DD Stop state machine tracer.
Given a portfolio NAV series and DD thresholds, traces the stop's behavior:
when it triggers, what multiplier it applies, and whether it capped drawdown.
"""
import numpy as np
import pandas as pd


def trace_dd_stop(
    portfolio_nav: pd.Series,
    soft_stop: float = 0.25,
    hard_stop: float = 0.40,
    scale_down: float = 0.50,
    scale_crash: float = 0.0,
    recover_threshold: float = 0.10,
) -> pd.DataFrame:
    """Trace DD stop state machine.
    
    Returns DataFrame with columns: nav, peak, dd, dd_mult, reduced_state
    """
    peak = portfolio_nav.expanding().max()
    dd = (peak - portfolio_nav) / peak.where(peak > 0, 1.0)
    
    mult_vals = []
    reduced = False
    trig_25 = trig_40 = rec_10 = None
    reduce_count = exit_count = recover_count = 0
    
    for i, d_val in enumerate(dd):
        if not np.isfinite(d_val):
            mult_vals.append(1.0)
            continue
        if d_val > hard_stop:
            if not reduced:
                exit_count += 1
                trig_40 = trig_40 or i
            reduced = True
            mult_vals.append(scale_crash)
        elif d_val > soft_stop:
            if not reduced:
                reduce_count += 1
                trig_25 = trig_25 or i
            reduced = True
            mult_vals.append(scale_down)
        elif reduced and d_val < recover_threshold:
            if reduced:
                recover_count += 1
                rec_10 = rec_10 or i
            reduced = False
            mult_vals.append(1.0)
        elif reduced:
            mult_vals.append(scale_down)
        else:
            mult_vals.append(1.0)
    
    result = pd.DataFrame({
        "nav": portfolio_nav,
        "peak": peak,
        "dd": dd,
        "dd_mult": mult_vals,
        "reduced_state": reduced,
    }, index=dd.index)
    
    trigger_info = {
        "soft_stop_first": dd.index[trig_25].date() if trig_25 else None,
        "hard_stop_first": dd.index[trig_40].date() if trig_40 else None,
        "recover_last": dd.index[rec_10].date() if rec_10 else None,
        "soft_stop_triggers": reduce_count,
        "hard_stop_triggers": exit_count,
        "recover_triggers": recover_count,
        "days_active": int((result["dd_mult"] < 1.0).sum()),
        "days_fully_exited": int((result["dd_mult"] == 0.0).sum()),
        "max_dd_achieved": float(dd.max()),
    }
    
    return result, trigger_info


def print_trace(trace: pd.DataFrame, info: dict, around_date=None, window=15):
    """Pretty-print the DD trace around a trigger date or worst-DD point."""
    if around_date is None:
        around_date = trace["dd"].idxmax()
    
    loc = trace.index.get_loc(around_date)
    start = max(0, loc - window)
    end = min(len(trace), loc + window // 2)
    
    print(f"{'Date':<14} {'NAV':>8} {'Peak':>8} {'DD%':>7} {'Mult':>5} {'Red':>5}")
    print("-" * 47)
    for idx in trace.index[start:end]:
        r = trace.loc[idx]
        print(f"{str(idx.date()):<14} {r['nav']:>8.2f} {r['peak']:>8.2f} "
              f"{r['dd']*100:>6.1f}% {r['dd_mult']:>5.1f} "
              f"{'YES' if r['reduced_state'] else 'no':>5}")
    
    print(f"\nSoft stop @{info['soft_stop_first']}" if info['soft_stop_first'] else "\nSoft stop: NEVER triggered")
    print(f"Hard stop @{info['hard_stop_first']}" if info['hard_stop_first'] else "Hard stop: NEVER triggered")
    print(f"Recover @{info['recover_last']}" if info['recover_last'] else "Recover: NEVER")
    print(f"Days active: {info['days_active']}, Full exit: {info['days_fully_exited']}")
    print(f"Max DD achieved: {info['max_dd_achieved']*100:.1f}%")


if __name__ == "__main__":
    print("Usage: from dd_stop_tracer import trace_dd_stop, print_trace")
    print("trace, info = trace_dd_stop(portfolio_nav)")
    print("print_trace(trace, info)")
