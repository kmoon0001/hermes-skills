# Research-First Methodology & Safe-Change Pattern

## Trigger
When a Copilot Studio evaluation score drops and root cause is unclear.

## Research-First Process
Before making ANY change to fix a regression:

1. **Check authoritative sources first** — Microsoft Learn docs (via MCP or web_extract), stored session history, and KB. Do NOT guess the fix.
2. **Identify the known-good baseline** — What config achieved the peak score? Why did it work? What changed between the peak and the regression?
3. **Form a hypothesis of root cause** — Do not apply workarounds without understanding. If the cause involves a system topic (CB, Fallback), be extremely careful.
4. **Snapshot before any change** — Save the current YAML/instructions to a rollback file. Every system topic change needs a revert path.
5. **One change per publish cycle** — Make one modification at a time. Run evaluation before making the next change. Never batch fixes.
6. **If regression >5 points, REVERT immediately** — Restore the known-good state before investigating elsewhere. Do not continue modifying the same component.

## Proven Pattern from SLP Fleet (June 2026)

| Symptom | Tried | Result | Root Cause |
|---------|-------|--------|------------|
| SR dropped 96% to 89% | Modified CB topic | 35% regression | CB config was already correct |
| SR 89% | Deleted caregiver topics | 92% recovery | Caregiver topics intercepted SR queries |
| SR 92% | Rolled back CB to original | 95% recovery | Original CB config was correct |

**Lesson:** Always rule out topic intercepts before touching system-level config.
