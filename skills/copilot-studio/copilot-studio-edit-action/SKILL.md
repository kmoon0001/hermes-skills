---
name: copilot-studio-edit-action
description: "Edit existing actions (kind: TaskDialog) in a Copilot Studio agent — connector actions and MCP server actions."
tags: [copilot-studio, actions, connectors, mcp]
---

# Edit Action

Edit existing actions (kind: TaskDialog) in a Copilot Studio agent. Supports connector actions and MCP server actions.

## Connector Lookup
```bash
node "D:/my agents copilot studio/pipeline/scripts/connector-lookup.bundle.js" list
node "D:/my agents copilot studio/pipeline/scripts/connector-lookup.bundle.js" operations <connector>
node "D:/my agents copilot studio/pipeline/scripts/connector-lookup.bundle.js" operation <connector> <operationId>
node "D:/my agents copilot studio/pipeline/scripts/connector-lookup.bundle.js" search <keyword>
```

Schema lookup:
```bash
node "D:/my agents copilot studio/pipeline/scripts/schema-lookup.bundle.js" summary TaskDialog
node "D:/my agents copilot studio/pipeline/scripts/schema-lookup.bundle.js" summary InvokeConnectorTaskAction
node "D:/my agents copilot studio/pipeline/scripts/schema-lookup.bundle.js" summary InvokeExternalAgentTaskAction
```

## Instructions
1. Auto-discover agent: Glob **/agent.mcs.yml
2. Find action: Glob <agent-dir>/actions/*.mcs.yml
3. Identify connector and operation from YAML
4. Determine action type: InvokeConnectorTaskAction (regular) or InvokeExternalAgentTaskAction (MCP)
5. Read template for structural reference: templates/actions/connector-action.mcs.yml or templates/actions/mcp-action.mcs.yml
6. Make edits

## Common Modifications
- Modify Input Descriptions on AutomaticTaskInput
- Add/Remove Inputs (cross-reference connector definition)
- Switch AutomaticTaskInput <-> ManualTaskInput
- Modify Outputs
- Change modelDisplayName / modelDescription
- Change Connection Mode (Maker vs Invoker)

## MCP Actions — Editable Fields
Safe: modelDisplayName, modelDescription, connectionProperties.mode, ManualTaskInput entries
Do NOT edit: operationDetails.operationId, connectionReference, do NOT add AutomaticTaskInput
modelDescription should be SINGLE-LINE (multi-line breaks MCP tool registration)

## Important Rules
- NEVER change action.operationId or action.operationDetails.operationId
- NEVER change action.connectionReference
- Property names must match connector definition
- ManualTaskInput values are strings only
- Output propertyName values must match connector definition

Templates: D:/my agents copilot studio/pipeline/templates/actions/
