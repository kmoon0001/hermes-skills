# Subagent CDP SPA Timeout Pattern

**Discovered:** Jun 10, 2026 during OT/SLP/PT 3-agent debug cycle.

**Pattern:** `delegate_task` subagents attempting to navigate the Copilot Studio SPA via CDP
`Page.navigate` will time out (600s) and fail silently. The SPA only renders 50-200 chars
(navigation header) when loaded via automated CDP navigation — the full application never boots.

**What works (OT subagent — SUCCESS):**
- Diagnostic analysis via `pac org fetch` to inspect topic YAML
- Reading local YAML files from the agent's home directory
- Querying Evaluation REST API for scores and failure patterns
- Root cause identification (CancelAllDialogs in 2 topics)
- Returning findings as structured subagent summary

**What fails (SLP/PT subagents — TIMEOUT):**
- Navigating to Copilot Studio pages via CDP Page.navigate
- Reading topic code editor content via CDP Runtime.evaluate
- Any live UI operation that requires page navigation

**Recommendation:** Use subagents for analytical/diagnostic work only (pac, API, file analysis).
For fix application, use the parent agent's CDP insertText workflow or ask the user
to apply fixes manually. Do NOT delegate live-UI fix application to subagents.
