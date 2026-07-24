---
name: copilot-studio-int-patterns
description: "Pattern library for Copilot Studio agent design. 15 proven implementation patterns with YAML examples. For design guidance, pattern suggestions, and troubleshooting known pitfalls."
category: copilot-studio
---

# Copilot Studio Pattern Library

## Pattern Index

| Pattern | Use When |
|---------|----------|
| **JIT Glossary** | Adding acronym lists, terminology tables for knowledge search |
| **JIT User Context** | Country/department/role-aware personalized answers via M365 connector |
| **Dynamic Topic Redirect** | Routing to topics based on variables using Switch expressions |
| **Prevent Child Agent Responses** | Child agent returns data without messaging user directly |
| **Date Context** | Date-relative questions, schedules, calendars |
| **Orchestrator Variables** | Classify/extract structured data at orchestration time, zero latency |
| **Prevent Tool Call Leaks** | Stop raw JSON/tool metadata leaking to end users |
| **Channel-Aware Behavior** | Detect Teams vs M365 Copilot vs web vs voice via ChannelId |
| **RAI Error Handling** | Category-specific messages for Azure OpenAI content-filter errors |
| **Line Breaks in Messages** | `<br /><br />` for reliable paragraph spacing across channels |
| **Knowledge Hold Message** | Randomized hold messages during knowledge search latency |
| **Deterministic MCP Calls** | Force MCP tool invocation for business-critical workflows |
| **Chain of Thought Logging** | "Thinking" messages during multi-step orchestration |
| **Conversation History Variable** | Capture transcript for escalation, logging, automation |
| **Teams Production Hardening** | 8 patterns for Teams/M365 Copilot: reinstalls, stale context, resets |
| **OCR Async Polling with Retry** | Async document OCR processing: submit job, poll status with 10-attempt limit, sentinel exit via `IsBlank`, `GotoAction` loop back to check |

## Common Combinations

- JIT Glossary + JIT User Context → single conversation-init topic
- Orchestrator Variables + JIT User Context → classify AND personalize
- RAI Error Handling + Teams Production Hardening → RAI subcodes first, then generic diagnostic
- Knowledge Hold + Chain of Thought → reduce perceived latency

Full pattern YAML examples at: https://github.com/microsoft/skills-for-copilot-studio/tree/main/patterns