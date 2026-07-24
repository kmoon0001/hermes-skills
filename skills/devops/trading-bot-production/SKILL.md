---
name: trading-bot-production
description: Freqtrade multi-asset trading bot — production state, architecture, and key facts
version: 2.0.0
---

# Freqtrade Production Trading System

## Architecture

```
Watchdog (8 checks, hourly)
├── bot health (API ping)
├── data freshness (signals, feather files)
├── disk space (free GB, data dir)
├── pipeline status (last log pass/fail)
├── crypto equity/drawdown
├── position concentration
├── stock portfolio (SMA252)
└── unified portfolio (risk parity, correlation, DD scale)

Daily Pipeline (10am, hardened + retry)
├── generate_signals (3x retry) → validate_data (25 files) → execute_trades → trade_logger → check_alerts
├── performance_report (crypto vs stocks vs benchmark)
├── monitor_status → portfolio_manager → watchdog summary

Data Integrity
├── validate_data.py: 25 feather files — existence, staleness, price sanity, file size. Exit codes for pipeline integration. Adjust staleness thresholds per timeframe (daily is critical, lower timeframes are supplementary).
├── performance_report.py: side-by-side crypto vs stocks vs SPY benchmark. --brief one-liner for cron. --json for machine reading. Handles single-snapshot edge case (shows equity even without enough history for metrics).

Data Integrity
├── validate_data.py: 25 feather files — existence, staleness, price sanity, file size. Exit codes for pipeline integration. Adjust staleness thresholds per timeframe (daily is critical, lower timeframes are supplementary). Suppresses pyarrow FutureWarning noise.
├── performance_report.py: side-by-side crypto vs stocks vs SPY benchmark. --brief one-liner for cron. --json for machine reading. Handles single-snapshot edge case (shows equity even without enough history for metrics). Also handles snapshots-vs-equity_history field name discrepancy in stock data.

Operations Layer
├── trading_ops.py: order lifecycle, slippage (Almgren), kill switch, pre-flight (6 checks), P&L attribution
├── portfolio_manager.py: risk parity weights, vol targeting, correlation scaling, DD circuit breaker
├── alerting.py: email (SMTP) + desktop (Windows toast) + log, severity filter, dedup

Stock System
├── paper_trade.py: SMA252 crossover (optimal, 26yr proven), dividends, T-bill cash return, SPY benchmark, retry, costs, alerts
├── multi_asset_sma.py: Parameterized SMA backtest (--sma N) for full-period sweeps
├── backtest_engine.py: parameter sweep, bootstrap CI, OOS validation, strategy comparison
```

## Exchange-Agnostic Data Layer

The crypto exchange is NOT hardcoded. All production files import from a single source.

Full architecture pattern (problem, solution, implementation steps, pitfalls) is
documented in `references/exchange-config-pattern.md`. Quick reference:

```
production/exchange_config.py:
  get_exchange()       → "okx" / "binance" / etc.
  get_data_dir()       → Path to user_data/data/<exchange>/
  get_pairs()          → list of trading pairs
  get_exchange_name()  → display name ("OKX", "Binance")
  set_exchange(name)   → writes exchange_settings.json
  list_supported()     → 6 dry-run exchanges with metadata
```

**Supported exchanges** (dry-run, no API key needed):
Binance, Bybit, Kraken, Coinbase, OKX, KuCoin. Freqtrade supports 77 via CCXT.

### Non-Coder Exchange Switching

Double-click `SWITCH-EXCHANGE.bat` → pick a number → confirm → optional data download.
Old data is preserved (not deleted) so you can switch back anytime.

### What Changes vs What Stays

When switching exchanges:
- **Changes:** data directory (`user_data/data/binance/` etc.), download source, config.json `name` field
- **Stays:** pairs (BTC/USDT etc. are universal), strategies (OHLCV-agnostic), stocks (separate), tests (pass regardless of data source)

### Files That Import From exchange_config

`trade_logger.py`, `watchdog.py`, `validate_data.py`, `execute_trades.py`,
`generate_signals.py`, `monitor_status.py` — all use `get_data_dir()` + `get_pairs()`.
Zero hardcoded `"okx"` strings remain in production code.

### Pitfall: sys.path for production imports

When adding `from production.exchange_config import ...` to files that didn't
previously import from `production.*`, you MUST add `sys.path.insert(0, str(ROOT))`
BEFORE the import. Files like `watchdog.py` and `validate_data.py` run standalone
and don't have the project root on their path by default. Forgetting this causes
`ModuleNotFoundError: No module named 'production'`.

## Launchers / Entry Points

Everything is reachable from a single double-click. The one-shot launcher covers
crypto, stocks, pipeline, watchdog, portfolio status, and performance reporting
in a menu-driven interface.
See also: `skill: standalone-project-delivery` for the launcher drift detection pattern.

| File | What it launches |
|------|-----------------|
| `START-FREQTRADE-DRY-RUN.bat` | **One-shot launcher** — menu: crypto dry-run, stock paper trade, full system, daily pipeline, watchdog, portfolio status, performance report, all checks |
| `START-FREQTRADE-DRY-RUN.ps1` | PowerShell version of the same 8-option menu |
| `SWITCH-EXCHANGE.bat` | **Non-coder exchange switcher** — pick from 6 exchanges by number, auto-updates config, offers data download |
| `install.bat` | One-click setup: Python, venv, deps, Task Scheduler, optional NSSM service |
| `setup.bat` | Lighter setup — just Task Scheduler config (venv must exist) |
| `uninstall.bat` | Removes all scheduled tasks and service |
| `production/pipeline.bat` | Daily pipeline (called by Task Scheduler) — no bash dependency, calls Python directly with retry |
| `production/watchdog.bat` | Hourly health check (called by Task Scheduler) |
| `production/stocks.bat` | Weekly stock paper trade + portfolio sync |
| `production/log_cleanup.bat` | Weekly log rotation |
| `production/run_cycle6_full.sh` | Bash fallback pipeline — see pipeline.bat for native Windows |
| `production/validate_data.py` | Data integrity: 25 files, freshness, price bounds, exit codes |
| `production/performance_report.py` | Combined performance: crypto vs stocks vs SPY, --brief/--json modes |
| `production/exchange_config.py` | Single source of truth for exchange name, data dir, pairs. `--set`, `--get`, `--list` CLI |

## Code Quality & Bulletproofing

All code quality gates pass as of 2026-07-23:

| Metric | Status |
|--------|:------:|
| Ruff linting | 0 violations |
| Docstrings | 100% (480/480 public functions) |
| Type annotations | 100% (return + params) |
| Duplicated utilities | 0 (all centralized to production/util.py) |
| Bare excepts | 0 |
| F-string syntax errors | 0 |
| Tests | 221 pass, 0 fail |

After any major feature push or before handoff, run the code quality audit workflow.
Full checklist and methodology in `references/code-quality-audit.md`. Quick summary:

- **Phase 1:** Find and remove dead files (backups, old docs, unused scripts)
- **Phase 2:** Fix bare excepts, strategy name drift, exchange hardcoding
- **Phase 3:** Add unit tests for untested production modules (priority: data integrity > health > pipeline > reporting)
- **Phase 4:** Run full test suite + production health check

Production modules with unit tests (as of Jul 23):
- `test_exchange_config.py` — 9 tests
- `test_validate_data.py` — 9 tests
- `test_watchdog.py` — 9 tests
- Pipeline modules covered by integration tests (test_production_pipeline.py, test_production_gaps.py)

## CI/CD Pipeline

GitHub Actions workflow at `.github/workflows/ci.yml`. Runs on every push/PR to master
plus daily at 09:00 PT.

```
lint (ubuntu) — HARD GATE
├─ ruff: E,F,N,UP rules, full codebase
├─ no bare excepts (E722)
├─ no undefined names (F821)
├─ bandit security scan (informational)
└─ deduplication check

test (ubuntu + windows) — HARD GATE
├─ pytest 221 tests on both OSes
└─ shell: bash required on Windows (PowerShell backtick vs bash backslash)

coverage (windows) — informational
├─ coverage run + report (numpy conflict on Linux prevents hard gate)
└─ Codecov upload

typecheck (ubuntu) — informational
└─ mypy on production/research/stocks

build (ubuntu + windows) — master only
└─ structure verification
```

### Pre-commit Hooks

`.pre-commit-config.yaml` catches issues before they reach CI:
- ruff lint + format
- trailing-whitespace, end-of-file-fixer, check-yaml/json/toml
- check-added-large-files, detect-private-key, mixed-line-ending
- bandit security lint

Setup: `pip install pre-commit && pre-commit install`

### CI Pitfalls Discovered

- **pytest-cov/coverage + numpy conflict:** On Python 3.11, coverage tools' import hooks
  conflict with numpy C extensions (`ImportError: cannot load module more than once per
  process`). Solution: run coverage as a separate Windows-only informational job.
- **PowerShell vs bash multiline:** Windows CI runner defaults to `pwsh` which uses
  backtick for line continuation. Always add `shell: bash` to cross-platform steps.
- **Coverage scoping:** `--cov=.` measures the entire repo (venv, tests, user_data)
  → 36%. Use `--source=production,research,stocks` to scope correctly.
- **F-string quote conflicts:** Converting `%` formatting to f-strings can introduce
  syntax errors when dict access `["key"]` uses the same quote as the f-string delimiter.
  Always `py_compile` files touched by UP031 fixes.
- **Conditional imports for CI:** `Cycle6Strategy.py` imports `talib` and `freqtrade` at
  module level — not available in CI. Wrap in try/except with fallback stubs.
- **Branch protection:** Set in GitHub Settings → Branches. Require lint + test (both
  OSes) before merge. Documented in `docs/BRANCH_PROTECTION.md`.

### Files to update when changing config

After adding any new production script, verify the one-shot launcher menu has an
entry for it AND that the .bat and .ps1 versions stay in sync. If the user can't
reach a subsystem from the menu, it effectively doesn't exist. If a .bat adds an
option, the .ps1 mirror needs the same option.

Detailed Windows batch file patterns (menus, retry loops, timestamps, confirmation
prompts) are documented in `references/windows-bat-patterns.md`. Consult that
reference when building or modifying launchers.

### Drift-Audit Checklist (run after any batch of changes)

1. **Strategy name:** grep both launchers for `--strategy` — must match the value
   in `user_data/config.json` (`"strategy": "Cycle6Strategy"`). Mismatch = silent
   startup failure (Freqtrade refuses to load unknown strategies).
2. **Exchange references:** grep `production/*.py` for hardcoded `"okx"` /
   `"binance"` — all production files must import from `exchange_config.py`.
   Research files and test files are exempt (historical backtests, test fixtures).
3. **Menu alignment:** count menu items in `.bat` vs `.ps1` — they must match.
4. **Config drift:** `CHECK-SETUP.bat` validates against a hardcoded strategy name —
   update it when the active strategy changes.
5. **Batch file audit:** list all `.bat` files and verify none reference deleted
   scripts or stale exchange names. The full list is:
   `START-FREQTRADE-DRY-RUN.bat`, `START-FREQTRADE-DRY-RUN.ps1`, `SWITCH-EXCHANGE.bat`,
   `install.bat`, `setup.bat`, `uninstall.bat`, `CHECK-SETUP.bat`, `OPEN-WEB-UI.bat`,
   plus 4 in `production/`.

### Pitfall: Strategy Name Drift

The Freqtrade config at `user_data/config.json` specifies the active strategy:
`"strategy": "Cycle6Strategy"`. Three files hardcode this name and MUST stay
in sync:
- `START-FREQTRADE-DRY-RUN.bat` (2 `--strategy` occurrences)
- `START-FREQTRADE-DRY-RUN.ps1` (2 `--strategy` occurrences)
- `CHECK-SETUP.bat` (1 `--strategy` occurrence)

If the config switches to a different strategy and these files are NOT updated,
Freqtrade silently fails to start. Verify with:
```bash
grep -rn "strategy" START-FREQTRADE-DRY-RUN.bat START-FREQTRADE-DRY-RUN.ps1 CHECK-SETUP.bat user_data/config.json
```

### Pitfall: sys.path for production imports

When adding `from production.exchange_config import ...` to files that didn't
previously import from `production.*`, you MUST add `sys.path.insert(0, str(ROOT))`
BEFORE the import. Files like `watchdog.py` and `validate_data.py` run standalone
and don't have the project root on their path by default. Forgetting this causes
`ModuleNotFoundError: No module named 'production'`.

## Research Codebase

All research TODOs resolved. The full cleanup workflow (audit, extract shared utils,
vectorize loops, fix stubs) is documented in `references/research-todo-cleanup.md`.
Key patterns:

### Shared Utility Extraction

When the same function exists in two or more research files, extract it ONCE into
`research/utils.py`. Do not leave a TODO — future sessions will forget.

**Done:** `aggregate_hourly_to_daily()` was duplicated in `cycle5_backtest.py` and
`weekly_momentum_backtest.py` (identical 50-line bodies). Extracted to
`research/utils.py`. Both files now import from the shared module. Verify with
`grep -rn "TODO\|FIXME" research/ --include="*.py"` — should return empty.

### Vectorization Over Loops

When a research function has a `for day in ...` loop iterating a pandas index,
replace with `groupby(...).transform('nunique')` or equivalent vectorized
operation. ~20x speedup on large datasets.

### Bootstrap Analysis
### Bootstrap Analysis
`research/bootstrap_analysis.py` requires NAV series saved to disk. The experiment
runners accept `--save-nav` to write `research/cycle5_nav.feather`. The bootstrap
script detects missing data and prints clear instructions.

### Expanded Data Sourcing (Beyond Exchange Limits)

Exchange APIs limit historical data. OKX goes back to 2022-06, Binance is geo-blocked.
For pre-2021 crypto data, use yfinance:

```python
import yfinance as yf
df = yf.Ticker("BTC-USD").history(start="2017-01-01", interval="1d")
# Save as user_data/data/<exchange>/BTC_USDT-1d.feather
```

**Always back up existing exchange data before overwriting** (use `.okx_backup` suffix).
USD and USDT prices are effectively identical for backtest purposes.

See `references/expanded-data-sweep.md` for full methodology and results.

### Vol Target Sweep (Critical Methodology)
`research/run_vt_sweep.py` — automated sweep: 8 vt values, each in a fresh
subprocess to avoid state caching. Overrides BOTH `cycle5_backtest.VOLATILITY_TARGET`
AND `cycle6_backtest.VOLATILITY_TARGET`. Output to
`research/vol_target_sweep_full.json`. Full protocol in
`references/vol-target-sweep.md`.

`research/run_vt_regime.py` — sub-period regime analysis (bull 2021, bear 2022,
recovery 2023, sideways 2024). Tests vt robustness across market conditions.

## Verified Configuration (active as of 2026-07-23)

**CRITICAL: The world-class analysis (Holm-Bonferroni correction + walk-forward OOS)
proved that vt=0.40's apparent improvement is NOT statistically significant.**
The full-period backtests looked promising (+2.5% CAGR) but the improvement
disappears when tested on unseen data. See `references/world-class-analysis.md`.

| Parameter | Value | 2021-2024 (5 pairs) | 2017-2024 (BTC+ETH) | Rationale |
|-----------|:-----:|:-------------------:|:--------------------:|-----------|
| Crypto vol target | **0.30** | 28.2% CAGR, Sharpe 0.835, DD -26.2% | 61.1% CAGR, Sharpe 1.145, DD -26.2% | Robust baseline. Higher vt improvements NOT significant (Holm p>0.6). Walk-forward OOS confirms vt=0.30. |
| Stock SMA | **252** | +8.8% CAGR over 26.5yrs, Sharpe 0.70, DD -27.5% | N/A (stock data already 26yr) | Independently verified, 26-year sweep. Beats SPY on CAGR with half the drawdown. |
| Portfolio split | **70/30** | ~20.7% CAGR, ~0.93 Sharpe | ~44.6% CAGR (est.) | Computed from verified inputs ✓ |

### Vol Target Sweep — Full Results

Full-period sweep results (fresh subprocess per vt, both c5 and c6 modules overridden):

| vt | 2021-2024 CAGR | 2021-2024 Sharpe | 2021-2024 MaxDD |
|:--:|:--------------:|:----------------:|:---------------:|
| 0.15 | 25.7% | 0.823 | -24.6% |
| 0.20 | 26.5% | 0.828 | -25.1% |
| 0.25 | 27.3% | 0.832 | -25.7% |
| **0.30 ★** | **28.2%** | **0.835** | **-26.2%** |
| 0.35 | 28.9% | 0.836 | -26.8% |
| 0.40 | 29.6% | 0.837 | -27.4% |
| 0.45 | 30.3% | 0.839 | -27.8% |
| 0.50 | 30.8% | 0.839 | -28.3% |

**Expanded 2017-2024 (BTC+ETH, yfinance data):**

| vt | CAGR | Sharpe | MaxDD |
|:--:|:----:|:------:|:-----:|
| 0.30 | 61.1% | 1.145 | -26.2% |
| 0.40 | 63.7% | 1.147 | -27.4% |

**Why vt=0.30 is selected despite vt=0.40 having higher numbers:**

1. **Multiple testing correction (Holm-Bonferroni):** All 6 comparisons of higher
   vt vs vt=0.30 have p-values > 0.6. After correcting for testing 8 values,
   zero are significant. The apparent improvement is indistinguishable from noise.
2. **Walk-forward OOS:** Both valid windows showed the "optimal" vt from training
   UNDERPERFORMED vt=0.30 on unseen data. The optimization doesn't generalize.
3. **Cost sensitivity:** vt=0.40 maintains +2.5% advantage at all cost levels up
   to 100bps — this is the strongest evidence FOR vt=0.40. But the statistical
   tests say the improvement isn't reliable enough to ship.
4. **Decision:** Stick with the robust, walk-forward-validated baseline.
   Full methodology and results in `references/world-class-analysis.md`.

| vt | CAGR | Sharpe | MaxDD | vs vt=0.30 |
|:--:|:----:|:------:|:-----:|:----------:|
| 0.15 | 25.7% | 0.823 | -24.6% | -2.5% |
| 0.20 | 26.5% | 0.828 | -25.1% | -1.6% |
| 0.25 | 27.3% | 0.832 | -25.7% | -0.8% |
| 0.30 | 28.2% | 0.835 | -26.2% | baseline |
| 0.35 | 28.9% | 0.836 | -26.8% | +0.7% |
| **0.40 ★** | **29.6%** | **0.837** | **-27.4%** | **+1.4%** |
| 0.45 | 30.3% | 0.839 | -27.8% | +2.1% |
| 0.50 | 30.8% | 0.839 | -28.3% | +2.6% |

Regime analysis (bear 2022, sideways 2024): higher vt amplifies losses by ~0.2%
but full-period net effect is strongly positive (+1.4% CAGR). This is standard
leverage math — bull market gains outweigh bear market losses.

### Critical Lessons

1. **NEVER optimize on a short bull-market window.** SMA20 sweep (2018-2023,
   6yrs) showed +12.8% CAGR / 1.19 Sharpe — but over 26 years (2000-2026) it's
   +1.6% / 0.20. The 2018-2023 period had no major crashes. Always backtest
   over at least one full cycle including 2000-2002 and 2008.

2. **Engine versions are NOT comparable.** The engine was fixed July 21, 2026
   (off-by-one NAV lag, P-sleeve contamination). Numbers from before and after
   the fix CANNOT be compared. When re-running sweeps, note the engine commit.
   The experiment runner had a state-caching bug (fixed now) and a module-level
   vol-target override bug (overriding cycle6_backtest when cycle5_backtest
   actually controls the simulation). Both bugs documented and fixed — but if
   you see identical results across different vt values, the override didn't
   take. See `references/vol-target-sweep.md` for the correct methodology.

3. **Always independently verify claims before accepting them.** The AGENTS.md
   claimed SMA20 was optimal (Sharpe 1.19). Independent re-run proved SMA252 is
   optimal. Trust data, not documentation. Run the sweep, check the numbers,
   then update the docs.

4. **Parameter sweeps need multiple-testing correction.** Testing 8 vt values
   guarantees some will look good by chance. Apply Holm-Bonferroni (Harvey, Liu
   & Zhu 2016) to correct for data mining bias. In our case, all 6 comparisons
   of higher vt vs baseline had p>0.6 — none survived correction. The apparent
   +2.5% CAGR improvement was noise.

5. **Full-period backtest results do NOT guarantee out-of-sample performance.**
   Walk-forward validation (optimize on training, test on unseen data) is the
   gold standard. Our walk-forward showed the "optimal" vt from training
   UNDERPERFORMED the baseline on test data in both valid windows. Always run
   walk-forward before claiming a parameter is "optimal."

6. **Cost sensitivity is necessary but not sufficient.** vt=0.40 maintained a
   +2.5% advantage at all cost levels up to 100bps. Cost robustness alone
   doesn't make a parameter optimal — you still need statistical significance
   and OOS validation.

See `references/world-class-analysis.md` for the full academic methodology
(bootstrap, Holm correction, cost sensitivity, walk-forward) and results.

### Files to update when changing config

| Parameter | Location |
|-----------|----------|
| Crypto vol target | `user_data/strategies/Cycle6Strategy.py:45` (`VOL_TARGET`) and `research/cycle6_backtest.py:20` (`VOLATILITY_TARGET`) |
| Stock SMA | `stocks/paper_trade.py:38` (`SMA_PERIOD`) |
| Portfolio split | `run_portfolio.py:35` (`DEFAULT_CRYPTO_PCT`) |
| Test assertion | `tests/test_strategy_tsmom.py:131` (assert default vol_target) |

## Key Numbers

- Crypto: Cycle6Strategy, TS MOM + Parkinson vol, **vt=0.30 (robust, walk-forward validated)**, 5 pairs, $1,000 wallet
  - 2021-2024 (5 pairs): 28.2% CAGR, Sharpe 0.835, MaxDD -26.2%
  - 2017-2024 (BTC+ETH, 8yr): 61.1% CAGR, Sharpe 1.145, MaxDD -26.2%
  - Survives 2018 crypto winter (BTC -84%, strategy MaxDD -27%)
  - vt=0.40 tested: +2.5% CAGR improvement but NOT statistically significant (Holm-Bonferroni p=0.88, walk-forward OOS negative)
- Stocks: **SMA252** tactical (verified, 26yr proven), 8 ETFs, $10,000 paper, +8.8% CAGR, Sharpe 0.70, MaxDD -27.5%. BEATS SPY B&H (+8.3%) with half the drawdown (-55.2%).
- Combined: **70/30** crypto/stocks split, ~20.7% CAGR (2021-2024), ~44.6% CAGR (2017-2024 est.), ~0.93 Sharpe, ~-27% MaxDD
- Benchmarks: SPY B&H +8.3% CAGR, Sharpe 0.51, MaxDD **-55.2%** (our stocks cut that in half)
- 221 tests (155 crypto + 39 stocks + 27 production unit tests), all passing
- Repo: kmoon0001/freqtrade-cycle5-research
- No Hermes dependency — standalone Windows, one-click install.bat
- Research: zero TODOs remaining, shared utils module (research/utils.py), vectorized loops, bootstrap functional, vol target sweep + regime analysis + expanded data tooling
- Exchange: configurable via SWITCH-EXCHANGE.bat (6 exchanges), single source of truth in production/exchange_config.py

## Risk Controls

| Control | Threshold | Action |
|---------|-----------|--------|
| Portfolio vol target | 15% annualized | Scale positions to target |
| DD exposure scaling | 15%→1.0x, 25%→0.5x, 30%+→0.1x | Dynamic position reduction |
| Cross-asset correlation | Warn >0.70, reduce crypto >0.60 | Diversification breakdown |
| Crypto allocation | Floor 20%, ceiling 60% | Prevent extreme concentrations |
| Single position | Max 25% | Per-asset limit |
| Kill switch | Emergency stop | Cancels all orders, closes all positions |
| Stoploss (crypto) | -6% per trade | Hard limit |
| Stock exit | Close < SMA252 | Moves to cash (T-bill rate) |

**Expected drawdowns (verified July 2026):**
- Crypto: ~27% max (vt=0.40, confirmed on both 4yr and 8yr datasets). Strategy survived 2018 crypto winter — BTC drawdown -84%, strategy MaxDD only -27%.
- Stocks: ~28% max (SMA252, across 2000-2026 including 2000-2002 dot-com and 2008 GFC)
- Combined 70/30: ~27% (diversification benefit — lower than either alone)

## Launch Phases

Full 4-phase plan with concrete exit criteria per phase. See LAUNCH_GUIDE.md in the repo
for the operational playbook (pre-flight checklists, emergency procedures, monitoring cadence).

## Reference Files

- `references/exchange-config-pattern.md` — Full architecture for exchange-agnostic data layer
- `references/launch-checklist.md` — Pre-launch validation checklist
- `references/research-todo-cleanup.md` — Workflow for cleaning up research TODOs
- `references/risk-framework.md` — Risk control methodology and thresholds
- `references/windows-bat-patterns.md` — Windows batch file patterns (menus, retry, timestamps)
- `references/sma-full-sweep.md` — **CRITICAL**: SMA 20-252 full-period sweep results (2000-2026). SMA20 is worst over full history.
- `references/performance-report-parser.md` — Section-aware parsing fix for backtest output
- `references/engine-version-pitfall.md` — Engine version compatibility + module-override bugs + index-alignment fix
- `references/vol-target-sweep.md` — Correct methodology for vol target comparison (fresh subprocess, override BOTH modules)
- `references/world-class-analysis.md` — **CRITICAL**: Full academic methodology. Holm-Bonferroni, walk-forward, cost sensitivity. Definitive reference for vt=0.30 choice.
- `references/bootstrap-quarterly-methodology.md` — **NEW**: Quarterly aggregation for stable bootstrap CIs. Code pattern + results for vt comparison.
- `references/data-sourcing-yfinance.md` — **NEW**: How to get pre-2021 crypto data when exchange APIs are limited. Backup strategy.
- `references/code-quality-audit.md` — **NEW**: Systematic workflow for dead code removal, lint fixes, test coverage audit. Run before handoff.

## New Research Tools (2026-07-23)

- `research/run_vt_sweep_expanded.py` — Extended sweep: 8 vt values, 2017-2024 (yfinance BTC+ETH), regime analysis
- `research/run_world_class_analysis.py` — Academic-grade analysis: bootstrap + Holm + cost sensitivity + walk-forward
- `research/run_vt_regime.py` — Sub-period regime breakdown (bull/bear/sideways)
- `research/run_walkforward.py` — Walk-forward validation with clean cache
- `stocks/multi_asset_sma.py` — Parameterized SMA backtest (--sma N) replacing fixed SMA252 file
