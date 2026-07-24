---
name: copilot-studio-add-action
description: "Guide users through adding a new connector action to their Copilot Studio agent via the portal UI, then offer to edit the pulled YAML."
version: "1.0"
---

# Add Connector Action (Guide)

Guide users through adding a new connector action to their Copilot Studio agent. Does NOT write action YAML directly because connector actions require a connection reference that can only be created through the Copilot Studio UI.

## Why This Is a Guide
Connector actions need:
1. A connection reference — authenticated link to external service
2. Connection reference can only be created by user authenticating in Copilot Studio portal
3. Once action is added via UI and pulled locally, YAML can be edited with edit-action skill

## Connector Lookup
Help user find right connector and operation before going to UI:
```bash
node "D:/my agents copilot studio/pipeline/scripts/connector-lookup.bundle.js" list
node "D:/my agents copilot studio/pipeline/scripts/connector-lookup.bundle.js" operations <connector>
node "D:/my agents copilot studio/pipeline/scripts/connector-lookup.bundle.js" operation <connector> <operationId>
node "D:/my agents copilot studio/pipeline/scripts/connector-lookup.bundle.js" search <keyword>
```

## MCP Server Actions
MCP actions use different YAML: InvokeExternalAgentTaskAction + ModelContextProtocolMetadata.
Like regular connector actions, MCP actions require connection reference created through Copilot Studio portal.
MCP actions do NOT use AutomaticTaskInput — MCP protocol handles tool parameter discovery dynamically.
ManualTaskInput entries OK for passing context (e.g., user identity via Power Fx: value: =System.User.Email).

## Walkthrough
1. Understand what user wants (ask clarifying questions if vague)
2. Search for operation using connector-lookup
3. Show operation details
4. Walk user through UI steps (open copilotstudio.microsoft.com -> Actions -> + Add action -> search -> configure -> save)
5. After user confirms pull, check for new action file: Glob **/actions/*.mcs.yml
6. Offer to edit action YAML

## Templates
Connector: templates/actions/connector-action.mcs.yml
MCP: templates/actions/mcp-action.mcs.yml
