---
name: copilot-studio-agent-solution-migration
description: Migrate Microsoft Copilot Studio agents between Power Platform/Dataverse environments using custom unmanaged solutions. Use when exporting/importing agents, cloning agents to another environment, creating agent transport solutions, publishing imported agents, or verifying bot synchronizationstatus after solution import.
---

# Copilot Studio Agent Solution Migration

## Overview

Use this workflow to move Copilot Studio agents between environments through supported Power Platform solution ALM. Treat Microsoft Learn as the source of truth and the live Dataverse tenant as the validation source.

Primary Learn pages:
- Export and import agents using solutions: https://learn.microsoft.com/microsoft-copilot-studio/authoring-solutions-import-export
- Create and manage solutions in Copilot Studio: https://learn.microsoft.com/microsoft-copilot-studio/authoring-solutions-overview
- Power Platform CLI `pac solution`: https://learn.microsoft.com/power-platform/developer/cli/reference/solution

## Rules

- Use a custom unmanaged solution for export/import. Do not rely on hand-edited solution zips as the primary path.
- Add agents as solution components with component type name `bot`; avoid numeric component IDs for `pac solution add-solution-component`.
- Do not trust `pac copilot list` for final state. Verify the `bot` table and `synchronizationstatus`.
- Publish imported agents before calling the migration complete.
- Preserve PHI rules: never export, paste, or log patient data. Agent migration should move configuration, not clinical records.

## Environment Setup

Identify source and target environments before changing anything:

```powershell
pac auth list
pac org list
```

For browser work, default environments may need the route form:

```text
https://make.powerapps.com/environments/Default-<tenant-id>/solutions
```

Example for Ensign default:

```text
https://make.powerapps.com/environments/Default-03cc92c3-986c-4cf4-ae27-1478cf99d17f/solutions
```

## Verify Source Agents

Query source bots directly:

```powershell
pac org fetch --environment <source-env-url> --xml "<fetch count='50'><entity name='bot'><attribute name='botid'/><attribute name='name'/><attribute name='schemaname'/><attribute name='synchronizationstatus'/><filter type='or'><condition attribute='name' operator='eq' value='PT_Specialist'/><condition attribute='name' operator='eq' value='OT_Specialist'/><condition attribute='name' operator='eq' value='SLP_Specialist'/></filter></entity></fetch>"
```

Adjust names for the requested agents. Record the source `botid`, `name`, and `schemaname`.

## Create Or Reuse A Source Solution

Preferred path:

1. Create a custom unmanaged solution in the source environment.
2. Add each agent to that source solution.
3. Export that solution from Dataverse.

If using CLI, create the solution through the browser or Dataverse Web API if needed, then add agents:

```powershell
pac solution add-solution-component --environment <source-env-url> --solutionUniqueName <solution-unique-name> --component <bot-guid> --componentType bot
```

If the CLI says the numeric component type is unknown, retry with `--componentType bot`.

## Export

Export the source solution as unmanaged:

```powershell
pac solution export --environment <source-env-url> --name <solution-unique-name> --path "<output-zip>" --overwrite --max-async-wait-time 60
```

Inspect the exported zip before import when risk is high:

- `Solution.xml` unique name and version match expectations.
- `Managed=0`.
- No unintended workflow/flow root components if the target lacks connection references.

Avoid deleting agent components from the zip to work around dependencies. Microsoft Learn warns direct component removal can break export/import.

## Import

Import through CLI when reliable:

```powershell
pac solution import --environment <target-env-url> --path "<solution-zip>" --publish-changes --force-overwrite --max-async-wait-time 60
```

Use the browser when CLI/network/auth/UI constraints require it:

1. Open the target environment Solutions page.
2. Select **Import solution**.
3. Upload the exported unmanaged zip.
4. Confirm the parsed solution details.
5. Select **Import**.

If the in-app browser cannot set file inputs, ask the user to select the zip in the native file picker, then continue the wizard.

## Publish And Verify

After import, fetch imported bot rows from the target:

```powershell
pac org fetch --environment <target-env-url> --xml "<fetch count='50'><entity name='bot'><attribute name='botid'/><attribute name='name'/><attribute name='schemaname'/><attribute name='synchronizationstatus'/><filter type='or'><condition attribute='name' operator='eq' value='<agent-name-1>'/><condition attribute='name' operator='eq' value='<agent-name-2>'/></filter></entity></fetch>"
```

Publish any imported agent that is not fully synchronized:

```powershell
pac copilot publish --bot <target-bot-guid> --environment <target-env-url>
```

The completion gate is:

- The solution exists in the target environment.
- Each expected `bot` row exists in the target.
- Each agent has `lastFinishedPublishOperation.status` of `Succeeded`.
- Each agent has `currentSynchronizationState.provisioningStatus` of `Provisioned`.
- Each agent has `currentSynchronizationState.state` of `Synchronized`.

If an agent remains `Synchronizing`, wait briefly and fetch again. If it remains stuck, explicitly publish that target bot GUID and recheck `synchronizationstatus`.

## Known Pitfalls

- `pac copilot list` can be stale; do not use it as final proof.
- Direct Power Apps routes using environment GUIDs can fail for default environments; use `Default-<tenant-id>`.
- Hand-built solution packages can fail with manifest parser errors or wrong component type IDs.
- Full source solutions may include flows or connection references missing in the target. Build a focused source solution instead of importing unrelated dependencies.
- Imported agents might have new target bot IDs. Always fetch target `botid` before publishing or reporting results.
