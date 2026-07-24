# Modified-Agent Batch Evaluation Recipe

Use this when asked to test every agent changed in one work period.

## Discovery before launch

1. Inspect recent version-control history to identify agents with live changes; do not infer the inventory from memory alone.
2. Verify each bot still exists/published in the target environment.
3. Enumerate each bot's evaluation sets and record `id`, `evaluationSetType`, case count, and display name.
4. Check for active/queued runs for every bot. Do not start another run for the same bot.
5. Choose named/current sets where possible. Do not invent a MultiTurn run if the bot has only SingleTurn sets; document the coverage gap and run the available evaluation type.

## Batch mechanics

- Commit/push the runner/configuration before consuming evaluation quota.
- Keep one active run per bot; different bots may run concurrently.
- Standard post-change baseline: 2x MultiTurn + 2x SingleTurn per bot when both types exist.
- For a bot with only one type, run two independent repetitions of that type and clearly label the missing dimension.
- Refresh the Gateway evaluation token about every five minutes. Treat a nonzero refresh-helper exit as nonfatal only if the token file was freshly written and validates as a JWT; otherwise stop before launching.
- Persist a machine-readable state file, append-only log, and markdown report with test-set IDs, run IDs, Pacific start/end times, passed, failed, errors, and score.

## Transport-resilient polling and recovery

- Treat `TimeoutError`, `URLError`, and socket/SSL read failures as **transient poll failures**, not terminal evaluation states. Catch them at the request boundary, log the event, refresh the token when due, and continue polling on the next interval. Never let an unhandled Gateway read timeout terminate a batch process.
- State must be durable before and after each launch and each terminal-result write. Store the full `runId`, not only a shortened display prefix.
- If the local poller exits after runs were launched, **do not restart the launch runner**: that can consume quota and duplicate evaluations. First query the live Gateway list endpoint for each bot, match the expected full `runId`s, and inspect the details endpoint for every expected run.
- Build a final reconciliation artifact from the live run records: state, passed, failed, errors, score, and start/end time. Explicitly say whether reconciliation started any new runs (normally: no).
- Resume only genuinely unstarted queue entries, after confirming there is no active run for that bot. Do not infer incomplete status merely because the local state file is behind.

## Cross-session task recovery ("what's left with agent X?")

When the user returns mid-batch or asks "what's left on agent X?" in a new session:

1. **Check persistent memory** for stored context about the agent (bot ID, last known score, outstanding work).
2. **Run session_search** with the agent name and relevant keywords (eval, fix, remaining, grounding, publish).
3. **Reconcile with live Gateway state** — query the list endpoint for every known run ID the prior session launched. A run that shows `state=Completed` on the live Gateway is done even if the local poller never reported it. Do NOT re-launch completed runs.
4. **Re-pull live agent state** — checkpoint the live `data` for key topics (SASC nodes, instructions, knowledge sources). Prior session's audit was a snapshot; the live agent may have diverged.
5. **Classify remaining work into buckets:**
   - **Unlaunched evals** — planned runs that were never started (no run ID in prior session). Launch these.
   - **In-progress evals** — runs with a live `InProgress` state. Wait for them.
   - **Completed evals below target** — the fix-loop was incomplete. Read the details endpoint for the latest run and resume triage.
   - **Structural fixes** — changes planned but never implemented (resource governance, KB additions, test-set rewording).
6. **Do not re-audit from scratch** — trust the prior session's structural snapshot unless more than ~48h have passed or the user reports unexpected behavior.
7. **Report the gap clearly** in terms of agent name, what was done, what remains, and what blocks it (eval quota, credential, user input needed).

## Completion

Do not claim a batch is complete until every queued run is terminal **in the live Gateway** and the final report has been read back. A completed live reconciliation is valid even if the original background poller exited. Report any quota, gateway, or per-bot coverage limitation separately from an agent quality score.
