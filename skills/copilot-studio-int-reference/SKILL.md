---
name: copilot-studio-int-reference
description: "Reference tables for Copilot Studio YAML authoring: triggers, actions, variables, entities, Power Fx functions, templates."
category: copilot-studio
---

# Integration Reference

Reference tables for Copilot Studio YAML authoring.

## Trigger Kinds
| Kind | Description |
|------|-------------|
| OnRecognizedIntent | Triggered by NLU matching trigger phrases |
| OnUnknownIntent | Fallback for unmatched utterances |
| OnActivity | Triggered on any activity (custom events) |
| OnConversationStart | Fires once at conversation start |
| OnError | Fires on runtime errors |
| OnInactivity | Fires after user inactivity timeout |
| OnInstallationUpdate | Teams install/uninstall events |
| OnSystemRedirect | System-initiated topic redirects |

## Action Kinds
| Kind | Description |
|------|-------------|
| SendActivity | Send a text message |
| Question | Ask user a question and wait for response |
| AdaptiveCardPrompt | Display an Adaptive Card |
| SearchAndSummarizeContent | Generative answers with knowledge sources |
| AnswerQuestionWithAI | AI-generated answer with knowledge |
| ConditionGroup | Branching logic (if/else) |
| Switch | Multi-branch routing based on variable |
| SetVariable | Set a variable value |
| InvokeFlowAction | Call Power Automate flow |
| InvokeConnectedAgentTaskAction | Call connected/child agent |
| EndDialog | End current topic immediately |
| GoToDialog | Redirect to another topic |
| ClearConversation | Reset conversation state |
| BeginDialog | Entry point for topic |

## Power Fx Functions (common)
| Function | Use |
|----------|-----|
| `System.Activity.Text` | Current user message |
| `System.Activity.ChannelId` | Channel identifier |
| `Topic.Name` | Current topic name |
| `Global.<VariableName>` | Global variable access |
| `Var.<VariableName>` | Topic variable access |
| `Blank()` | Empty value |
| `If(condition, trueVal, falseVal)` | Conditional |
| `Lower(text)` | Lowercase conversion |
| `Trim(text)` | Remove whitespace |
| `Concatenate(s1, s2)` | Join strings |

Full reference: https://learn.microsoft.com/microsoft-copilot-studio/guidance