# Post-migration eval gap — critical finding

**Discovered 2026-07-18 Pacific** when investigating Doc Defense 0/10 scores.

## The finding

After migrating an agent between Power Platform environments (PCCA Package → Therapy AI Dev via unmanaged solution export/import), **eval data does NOT survive**.

Specifically:
- **Zero eval runs** in the target env — even completed runs from the source env are gone
- **Zero eval definitions / test sets** — the transport solution does not carry evaluation configuration
- The `GET /environments/{env}/bots/{bot}/makerevaluations?$top=5` endpoint returns empty `[]`
- `POST /makerevaluations` with a `testSetId` fails because no test sets exist yet

## Why this matters

- **Old 0/10 scores from source env are noise** — they belonged to a different environment with different configuration. Do not attempt to fix them.
- **Must create fresh test sets** before any eval can run
- **No API shortcut exists** for creating auto-generated test sets — the Copilot Studio Evaluate tab UI is required (or a manually crafted CSV)

## Required steps after migration

1. Do NOT attempt to re-run evals from the old environment — the new bot ID has no eval history
2. Go to Copilot Studio → Evaluate tab → New evaluation → Single response → Auto-generate test cases
3. Or create a CSV test set locally and upload it via the Evaluate tab
4. Only then run evals and establish a new baseline

## Relevant bot IDs

| Agent | Source env botid | Target env botid |
|-------|-----------------|-----------------|
| Pacific Coast Doc Defense Agent | `9e7b871d-1d80-f111-ab0f-000d3a5b0d6c` (PCCA) | `2e08ac68-bdef-481e-9c04-6a349c79d6c0` (Therapy AI Dev) |
