# Kanban CLI Pitfalls

## boards switch does NOT persist

`hermes kanban boards switch <slug>` changes the active board for the current
shell process only. Each `hermes kanban` invocation via terminal() or execute_code
gets its own subshell — the switch does NOT carry over.

**Symptom:** After `hermes kanban boards switch projects`, running `hermes kanban list`
still shows the default board's tasks, and `hermes kanban boards current` says
"Current board: default."

**Fix:** Always use `--board <slug>` on every kanban command:
```bash
hermes kanban --board projects create "Task title" --body "..."
hermes kanban --board projects list
hermes kanban --board projects complete t_abc123 --summary "..."
hermes kanban --board projects block t_def456 "reason"
```

**Discovery:** Jul 22, 2026 — during Freqtrade project kanban population.
Tasks created after `boards switch projects` went to the default board instead.
Had to archive all 9 tasks and recreate with explicit `--board projects` flag.
