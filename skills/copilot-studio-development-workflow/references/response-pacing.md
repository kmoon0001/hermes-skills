# Response Pacing Rules (Kevin's Preference)

Kevin gets frustrated with empty responses between tool calls and with writing scripts without running them. He wants to see RESULTS, not file writes.

## Hard Rules
1. ALWAYS run a script in the SAME turn you write it. Never write → wait → write → wait.
2. If a script runs and produces output, REPORT the output immediately. Never just return silent.
3. If a script fails, report the error and the fix in the same turn.
4. If you're monitoring/waiting for something, report a status update every time. Never go silent.
5. Prefer a single terminal() call with the full command over writing a .cjs file, unless the logic is complex enough (5+ steps, error handling, loops) to justify a file.
6. When the user asks "update me" or "status" — give the concise answer immediately, don't start a new investigation.

## Why
Kevin operates multiple AI agents (Hermes, Claude, Gemini, Codex) simultaneously. He can't afford to wait through silent turns or write-then-write-again loops. Every empty response wastes his attention.
