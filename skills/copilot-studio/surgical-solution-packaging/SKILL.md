---
name: surgical-solution-packaging
description: Import a single bot (not the full swarm) between Copilot Studio environments. Use when a full-solution import fails due to privilege errors (prvCreateEntity) or MAX_PATH issues. Mirrors Kiro's surgical-solution-packaging skill.
category: copilot-studio
---

# Surgical Solution Packaging — Single-Bot Environment Transport

## When to Use
- Moving one bot from staging to dev
- Full-solution import fails: `prvCreateEntity`, `MAX_PATH`, or conflicting components
- Need to deploy a bot without overwriting other active swarm bots

## Core Approach

Extract only the target bot's components from a solution zip, scrub unrelated entities/flows/workflows, and repackage into a clean surgical solution.

## Prerequisites

```powershell
# Auth to target environment
pac org select --environment https://orgbd048f00.crm.dynamics.com/
```

## The Surgical Extraction

1. Open source solution zip using `System.IO.Compression`
2. Extract `solution.xml`, `customizations.xml`, `[Content_Types].xml`
3. **Scrub** `<Entities>`, `<EntityRelationships>`, `<Workflows>` nodes from `customizations.xml` (removes blocked custom tables)
4. **Rewrite** `<RootComponents>` in `solution.xml` to contain only the target bot's `schemaName`
5. Extract only `botcomponents/<schema>*` and `bots/<schema>*` entries
6. Repackage into a clean zip

## Import

```powershell
pac solution import --path ./TargetBot_Surgical.zip --publish-changes --force-overwrite
```

## Validation Gate

```powershell
# Verify bot exists in target env
$uri = "https://orgbd048f00.crm.dynamics.com/api/data/v9.2/bots?`$filter=contains(name,'BotName')"
# Expect: statecode = 0 (active), synchronizationstatus = Synchronized
```

After import, publish the bot and verify `lastFinishedPublishOperation.status` = `Succeeded`.

## Verified Example (2026-07-23)

Competency Check Gamer Agent (bot `7667e9b4`) created fresh in Therapy AI Agents Dev. No migration needed since it was built from scratch via API. For existing bots needing transport, use this surgical approach to avoid full-solution import pitfalls.

## Hard Rules
- Never import the full swarm solution — it overwrites all active bots
- Always use `--force-overwrite` for idempotent re-imports
- Always run `--publish-changes` in the SAME command — do not publish separately
- Confirm `statecode = 0` AND `synchronizationstatus` via OData before declaring success
- Use `copilot-studio-agent-solution-migration` for the full supported ALM path; use this skill only when that fails
