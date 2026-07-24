---
name: copilot-studio-add-other-agents
description: Add multi-agent capabilities to a Copilot Studio agent — child agents (AgentDialog) and connected agents (InvokeConnectedAgentTaskAction).
---

# Add Other Agents

Add multi-agent capabilities to a Copilot Studio agent.

## Pattern 1: Child Agent
Create AgentDialog that parent orchestrator can delegate to.

### Two-Phase Workflow (CRITICAL)
Phase 1: Create plain agent ONLY (agent.mcs.yml with config, instructions, inputs, outputs). NO knowledge directory. Tell user to push first.
Phase 2: Add knowledge sources ONLY after user confirms push. Knowledge sources reference the agent — child must exist in environment first.

### Structure
```yaml
kind: AgentDialog
beginDialog:
  kind: OnToolSelected
  id: main
  description: This agent handles billing inquiries, payment issues, refund requests. Route here when users ask about charges or invoices.
settings:
  instructions: |
    You are a billing support specialist. Help customers with charges, invoices, refunds.
inputs:
  - kind: AutomaticTaskInput
    propertyName: CustomerQuery
    description: The customer's billing-related question
inputType:
  properties:
    CustomerQuery:
      displayName: Customer Query
      description: The customer's billing-related question
      type: String
outputType: {}
```

CRITICAL: AgentDialog must NOT have beginDialog.actions. Child agents use generative orchestration — behavior driven by settings.instructions only. Do NOT add action nodes.

## Pattern 2: Connected Agent
Call external independently-managed agent. Creates TaskDialog with InvokeConnectedAgentTaskAction.

### Calling Side (your agent)
```yaml
kind: TaskDialog
modelDisplayName: Expense Report Processor
modelDescription: Process expense reports by sending to expense agent
inputs:
  - kind: AutomaticTaskInput
    propertyName: expenseReportFileFullPath
    description: Full file path of expense report
action:
  kind: InvokeConnectedAgentTaskAction
  inputType:
    properties:
      expenseReportFileFullPath:
        displayName: expenseReportFileFullPath
        isRequired: true
        type: String
  botSchemaName: cr123_expenseAgent
  historyType:
    kind: ConversationHistory
```

### Called Side (user must configure)
Needs: OnRedirect topic, global variables with external source permissions, inputType/outputType.

Templates: templates/agents/agent.mcs.yml, templates/agents/child-agent.mcs.yml
