---
name: copilot-studio-add-global-variable
description: Add a global variable to a Copilot Studio agent that persists across all topics within a conversation.
tags: [copilot-studio, variables, global-variable, yaml]
---

# Add Global Variable

Create a global variable that persists across all topics within a conversation.

## Instructions
1. Auto-discover agent directory: Glob **/agent.mcs.yml
2. Read settings.mcs.yml to get schemaName prefix
3. Determine from user: variable name (PascalCase), description, aIVisibility, default value

## Variable File
Create at `<agent-dir>/variables/<VariableName>.mcs.yml`:
```yaml
# Name: <Human-readable Name>
# <Description>
name: <VariableName>
aIVisibility: <UseInAIContext or HideFromAIContext>
scope: Conversation
description: <Description>
schemaName: <prefix>.globalvariable.<VariableName>
kind: GlobalVariableComponent
defaultValue: <DEFAULT or specific value>
```

## Key Fields
- **name**: PascalCase identifier. Referenced as `Global.<name>`
- **aIVisibility**:
  - `UseInAIContext`: orchestrator can read and reason about it
  - `HideFromAIContext`: internal bookkeeping, AI doesn't see it
- **scope**: `Conversation` (always for global variables)
- **schemaName**: `<agent-schemaName>.globalvariable.<VariableName>`
- **defaultValue**: initial value, use `DEFAULT` if none needed

## How Topics Use Global Variables
- Reading: `=!IsBlank(Global.LastDiscussedCity)`
- Setting: `variable: Global.LastDiscussedCity, value: =Topic.CityName`
- Activity text: `"Last time we discussed {Global.LastDiscussedCity}."`

## When to Use
- Cross-topic state (user preferences, last search query)
- AI-aware context (`UseInAIContext` for routing decisions)
- Conversation-wide defaults
- Dynamic knowledge source URLs via `=$"{Global.VarName}"`
