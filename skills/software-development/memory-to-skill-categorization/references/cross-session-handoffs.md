# Cross-Session Handoffs

Use this when a user wants to run `/new` while work is incomplete.

## Handoff pattern

1. Keep detailed progress in the session transcript and task list, not durable memory.
2. Save one compact memory pointer containing:
   - stable project/repository path;
   - safety boundaries that must survive the reset;
   - exact `session_search` recall phrase;
   - only the minimum volatile state needed to avoid damage, such as known uncommitted files.
3. Prefer replacing an existing project pointer instead of adding another entry.
4. If memory is near capacity, shorten the replacement before deleting unrelated durable preferences.
5. Tell the user the exact recall phrase after the memory write succeeds.

## Background delegation before `/new`

- Do not launch additional speculative subagents once the user signals an imminent reset.
- Acknowledge already-running delegation results without repeatedly rewriting memory unless the handoff state materially changes.
- If a worker leaves uncommitted files, record that narrow fact in the pointer so the next session verifies rather than blindly overwrites them.
- Treat a subagent summary as unverified. The next session must read the files and rerun checks before committing or claiming completion.

## Avoid

- Commit hashes, test counts, temporary worker IDs, and long progress narratives in memory.
- One memory update per asynchronous notification.
- Claiming a timed-out worker produced no useful files without checking the reported handoff state.
