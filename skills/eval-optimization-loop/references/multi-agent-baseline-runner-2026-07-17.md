# Multi-agent baseline runner (2026-07-17)

## Purpose
After fixing multiple agents in one session, capture **2× MultiTurn (Conv) + 2× SingleTurn (SR)** per agent so Kevin can analyze scores the next day.

## Preconditions
- Structural spot-check PASS on live `data` (SASC package intact)
- Publish Succeeded verified via Dataverse (not pac CLI alone)
- Eval token via `node refresh_eval_token.cjs` → `~/.copilot-studio-cli/test-agent-token.txt` starts with `eyJ`
- Never put az Dataverse token in that file

## Implementation used
`Pacific-Coast-Therapy-Hub/scripts/run_baselines_tonight.py`

Behavior:
- Parallel start: one run per bot
- Per-bot queue: Conv, Conv, SR, SR
- Poll list endpoint every 30s; refresh token every ~5 min
- Write `eval_baselines_tonight/BASELINE_REPORT.md` as runs complete
- Log: `baseline_log.txt`; state: `baseline_state.json`

## Test set selection
From `GET .../makerevaluations/testsets` use field **`evaluationSetType`**:
- `SingleTurn` → SR
- `MultiTurn` → Conv

Prefer displayNames matching the agent. Discard foreign-named 100-case sets for scoring (still record if accidentally run).

## Pitfalls
- One active run **per agent** — starting a second while InProgress returns soft failure; wait and chain
- Token path: `os.path.expanduser('~/.copilot-studio-cli/test-agent-token.txt')` on Windows Python (not `/c/Users/...`)
- Quota 20/24h — plan run count before launching
- Score variance ±5%; averages need ≥2 completed runs of same kind
