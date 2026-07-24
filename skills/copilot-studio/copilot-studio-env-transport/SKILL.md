---
name: copilot-studio-env-transport
description: Move Copilot Studio agents between Power Platform environments with focused unmanaged solutions (export/import), then re-fetch target botid and audit. Use when transporting agents PCCA Package ↔ Therapy AI Dev or similar. Complements pinned copilot-studio-agent-solution-migration with a validated 2026-07-16 CLI/API path.
---

# Copilot Studio environment transport

## When to use
- Move an agent between envs via solutions (not clone-in-UI only)
- User says export/import/solutions/transport
- After transport, run readiness audit

## Rules
- Focused unmanaged solution only (not Default/CDS full dump)
- `componentType bot` + `--AddRequiredComponents`
- Target **botid usually changes** — re-fetch by name
- Transport success ≠ eval-ready — run agent-audit-protocol first-pass
- PHI: config only, never clinical records
- Report times in **Pacific local**

## Validated path (Doc Defense, 2026-07-16 Pacific)

Source: PCCA `pccapackage.crm.dynamics.com` bot `9e7b871d-1d80-f111-ab0f-000d3a5b0d6c`  
Target: Therapy AI Dev `orgbd048f00.crm.dynamics.com` bot **`2e08ac68-bdef-481e-9c04-6a349c79d6c0`**

1. Confirm source bot exists; confirm target has **no** row for that name.
2. Create solution via Dataverse if needed:
   `POST /api/data/v9.2/solutions` with uniquename, friendlyname, version, `publisherid@odata.bind`
3. Add agent:
```bash
pac solution add-solution-component \
  --environment "<source>" \
  --solutionUniqueName DocDefenseTransport \
  --component "<source-bot-guid>" \
  --componentType bot \
  --AddRequiredComponents
```
4. Export unmanaged (Windows path for `--path`):
```bash
pac solution export --environment "<source>" --name DocDefenseTransport \
  --path "C:/Users/kevin/Desktop/docdef_migrate/DocDefenseTransport.zip" \
  --overwrite --managed false --max-async-wait-time 60
```
5. Import:
```bash
pac solution import --environment "<target>" \
  --path "C:/Users/kevin/Desktop/docdef_migrate/DocDefenseTransport.zip" \
  --publish-changes --force-overwrite --max-async-wait-time 90
```
6. Fetch target bot by name → new botid. Publish until Synchronized.
7. First-pass audit: GPT55Chat, empty responseInstructions, SASC missing FullResponse, Fallback without SASC.

## Pitfalls
- `pac org fetch --xmlFile` needs Windows paths (not `/tmp`)
- Registry tables can list wrong env/botid — Dataverse fetch is truth
- Pinned skill `copilot-studio-agent-solution-migration` may refuse curator patches; keep durable deltas here or in agent-audit-protocol references
- **Eval runs do NOT survive transport.** The new env has zero eval history, zero test sets, and no eval definitions for the transported bot. All prior eval baselines (even completed runs) are lost. You must create new test sets (auto-generate or CSV upload) and run fresh evals from scratch after migration. The old env's 0/10 runs from before migration are noise — ignore them.
- **Auto-generated test sets require Copilot Studio UI.** There is no API shortcut exposed by the gateway for creating auto-generated test sets. The `POST /makerevaluations` endpoint requires a `testSetId` that doesn't exist until the test set is created in the UI. Plan for a UI session to set up evals, or create a CSV locally and upload it.
- **After transport, verify eval availability first** by listing runs before setting up new ones: `GET /environments/{env}/bots/{bot}/makerevaluations?$top=5`. If zero runs, move straight to test-set creation.
- **Bot ID changes.** Always re-fetch by name with `pac copilot list` after import. The old bot ID from the source env is dead.

## Related
- `agent-audit-protocol` + `references/post-migration-doc-defense-therapy-ai-dev.md`
- `copilot-studio-agent-instructions` + `references/solution-transport-then-audit.md`
- `copilot-studio-agent-solution-migration` (pinned Learn-oriented overview)
- `copilot-studio-create-eval-set` — creating a CSV test set for import when UI auto-generate isn't viable
- `agent-audit-protocol/references/post-migration-eval-gap.md` — doc of eval-data loss after transport
