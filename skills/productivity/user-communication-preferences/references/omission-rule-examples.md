# Omission Rule — Concrete Examples

## Jul 22, 2026: Portfolio Integration Gap

Kevin asked me to build a production-grade trading system. I built crypto and stock systems
separately but did NOT proactively point out they should be unified into a single portfolio.
When Kevin asked why I didn't bring it up, he explicitly stated:

  "why wouldnt you bbring up tying them togeher? my rule was no not telling me.
  omission is breking the rule. you must present alll options even when i dont ask,
  if theres a better way to do things, bring it up. understand?"

This is a hard rule. After completing a task, ALWAYS ask: "What else could be improved?
What connections am I not seeing? What industry best practices haven't I applied?"

The portfolio integration (risk parity, cross-asset correlation, unified volatility targeting,
drawdown circuit breaker across both asset classes) was the missing piece that should have
been flagged during the watchdog build, not discovered by the user later.

## Pattern

When finishing any system build, before considering it done:
1. Scan for integration opportunities with other systems the user has
2. Check if industry standard practices are missing (risk management, monitoring, alerting)
3. Ask if the system is production-grade or just functional
4. Present gaps as a list even if the user didn't ask for them
