# Pre-Launch Verification Checklist

Complete every item before moving to the next phase.

## Phase 1: Dry Run (1-2 weeks minimum)

- [ ] All 4 Task Scheduler jobs created and verified
- [ ] Daily pipeline completes 5+ consecutive days without errors
- [ ] Watchdog reports all-green for 7+ consecutive days
- [ ] Stock paper trader runs 2+ weekly cycles
- [ ] Portfolio manager shows consistent combined equity tracking
- [ ] Pre-flight checks pass: `trading_ops.py --preflight`
- [ ] All tests pass (zero failures, zero errors)
- [ ] No unhandled exceptions in any log file
- [ ] Heartbeat file updated within last hour
- [ ] Trade history backups exist and are rotated
- [ ] NSSM service starts on boot (if configured)
- [ ] Windows toasts appear on watchdog alerts

## Phase 2: Paper Live (1 week minimum)

- [ ] Exchange demo account created
- [ ] API keys generated (TRADE permission only, no withdraw)
- [ ] Credentials stored in env vars or encrypted file, NOT in git
- [ ] `trading_ops.py --preflight --mode paper_live` passes
- [ ] Orders execute on demo exchange and appear in exchange UI
- [ ] Fill prices within expected slippage range (+-20bps for crypto, +-5bps for stocks)
- [ ] Kill switch tested: engage, verify no new orders, disengage, verify resume
- [ ] P&L attribution matches exchange records

## Phase 3: Small Live (2 weeks minimum)

- [ ] Starting capital: minimum viable ($100-200)
- [ ] Position sizes: $10-20 per trade
- [ ] Exchange balance verified before first trade
- [ ] All orders settle within expected time
- [ ] No order rejections (insufficient balance, rate limits, etc.)
- [ ] Slippage within model estimates for all fills
- [ ] Daily P&L matches exchange
- [ ] Alerting system tested (email, desktop) on real events
- [ ] Kill switch tested with real open orders

## Phase 4: Full Live

- [ ] Gradual position size increase (25% → 50% → 75% → 100% over 4 weeks)
- [ ] Daily monitoring for first month
- [ ] Weekly P&L review against attribution report
- [ ] Monthly rebalancing per portfolio_manager target weights
- [ ] Quarterly strategy review (still beating benchmark? drawdown within tolerance?)
