# Platform-Wide Evaluation Service Failure — June 18, 2026

## Timeline

| Time | Agent | Type | Score | Notes |
|------|-------|------|-------|-------|
| 2:57 PM | SLP | Conv | 100% | Last successful eval |
| 3:00 PM | PT | Conv | 90% | Working |
| 3:12 PM | PT | Conv | 90% | Working |
| 3:16 PM | SLP | Conv | 90% | Working |
| 3:33 PM | SLP | Conv | 100% | Last successful eval |
| 3:37 PM | PT | Conv | 90% | Last successful eval |
| 3:50 PM | PT | Conv | 30% | CRASH — simultaneous |
| 3:50 PM | SLP | Conv | 60% | CRASH — simultaneous |
| 3:50 PM | TDA | Conv | 78% | CRASH — simultaneous |
| 4:12 PM | SLP | Conv | 0% | Total failure |
| 4:21 PM | PT | Conv | 0% | Total failure |
| 4:?? PM | TDA | Conv | 0% | Total failure |
| ...all subsequent runs for all agents... | | | 0% | Persistent failure |
| 10:00 PM | OT | Conv | 0% | UNTOUCHED agent also fails |

## Key Facts

- All 4 agents (OT, PT, SLP, TDA) return "Error" on ALL eval test cases
- OT was NOT modified — last eval was 2:27 AM yesterday (95% Conv)
- All agents work perfectly in the Test pane
- Knowledge sources: "Status: Ready", "Connectivity Status: Connected"
- No topic errors visible
- No model retirement notice
- Re-publishing doesn't fix it
- Model: GPT-5 Chat

## Root Cause

The Microsoft Copilot Studio evaluation service failed for this environment at ~3:50 PM. The agents themselves are functioning correctly (Test pane works). The evaluation service's ability to communicate with the agents or their knowledge sources broke at the platform level.

## Diagnostic Steps Taken

1. Checked agent configurations — all correct
2. Checked knowledge sources — all "Ready" and "Connected"
3. Checked topics — no errors
4. Re-published all agents — didn't fix
5. Triggered fresh evals — still 0%
6. **Triggered eval on UNTOUCHED agent (OT) — also 0%** ← definitive proof

## Resolution

- Wait for platform recovery (transient Microsoft service issue)
- Check Microsoft service health: https://admin.powerplatform.microsoft.com/health
- Try the Evaluation REST API as alternative endpoint
- Contact Microsoft support with environment ID: Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f

## Lesson Learned

**Always test an untouched agent early when diagnosing simultaneous eval failures.** Don't spend hours debugging agent instructions/topics when the eval service itself is broken. The diagnostic: trigger eval on OT (or any agent you know you didn't modify). If it also fails, stop debugging agents and wait for platform recovery.
