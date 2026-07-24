# Therapy Report Prep V2 — Safe post-baseline fix (2026-07-17)

Bot: `fd1bce12-cf47-f111-bec5-70a8a5b1c3a3` (`auto_agent_aaamq`)  
Env: Therapy AI Dev  
Baseline (pre-safe): SR avg **69.5%**, Conv avg **37.5%** (2× each)  
Structural pass earlier same night: Pattern L leaves + boosting emit Answer + GPT5Chat + EVAL CTX  
Safe publish: **Succeeded** ~09:57 AM PT

## Failure concentration (SR#2 details)
- 26/31 fails = **abstention**
- Common prompts: facility utilization, patient lists, therapy minutes by discipline, productivity rankings, "review our documentation" without paste
- Grader reason pattern: agent did not deliver facility-specific numbers → marked abstention even when CMS framework was present
- Secondary: Suggested Actions returned **menu only** for analysis asks
- Runtime: `ConnectedAgentBotNotPublished`, `ConnectedAgentChainingNotSupported` on IDT/routing-style turns

## Surgical patches applied (script)
`Pacific-Coast-Therapy-Hub/scripts/fix_reportprep_safe.py`  
Backups: `backups/reportprep_safe_20260717_095615/`

| Change | Intent |
|--------|--------|
| Instructions ANTI-ABSTENTION block | Never menu-only; facility-metric → template + "To complete from your facility data" |
| Boosting additionalInstructions | Same; keep FullResponse + SendActivity |
| Suggested Actions triggers narrowed | Explicit menu phrases only |
| Fallback softer | Never-refuse SASC copy |
| Disable Case Historian / Dashboard / Command Center TaskDialogs | Stop connected-agent crash answers |

## What NOT to do next
- Do not rewrite Progress/Recert/Discharge/Eval leaves again without new structural evidence
- Do not invent facility metrics to chase abstention scores
- Remaining fails may be **eval-setup** (ask for operational data the agent cannot have) — reword tests or accept template answers as ship-quality for a note-prep agent

## Related
- Structural audit: `references/report-prep-v2-audit-2026-07-17.md`
- Pattern R in agent-audit-protocol SKILL.md
- Baselines: `eval_baselines_tonight/BASELINE_REPORT.md`