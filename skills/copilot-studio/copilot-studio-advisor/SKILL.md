---
name: copilot-studio-advisor
description: Design review, troubleshooting decision tree, and architecture guidance for Copilot Studio agents. Mirrors Kiro's copilot-studio-advisor skill. Load before major architectural changes, when diagnosing agent failures, or when reviewing agent design.
category: copilot-studio
---

# Copilot Studio Advisor

Use when reviewing agent design, troubleshooting failures, or making architecture decisions.

## When to Activate
- User asks "why is my agent doing X"
- User wants design review or improvement suggestions
- User asks about best practices for a specific pattern
- Before major architectural changes

## Design Review Checklist
1. Is orchestration mode appropriate? (Generative for most, Classic only for strict determinism)
2. Are knowledge sources properly described? (Description drives AI routing)
3. Are topics non-overlapping? (Merge topics with 50%+ intent overlap)
4. Are tools clearly bounded? (One purpose per tool, clear description)
5. Is the response format constrained? (Prevents truncation in eval)
6. Are trust and safety behaviors defined? (Out-of-scope, refusal, escalation)

## Troubleshooting Decision Tree

### Agent Not Responding or Auth Errors
1. Check Work IQ (mode Invoker blocks unauthenticated users)
2. Check external tool topics (InvokeExternalAgentTaskAction)
3. Check publish status (synchronizationstatus)

### Wrong Answers or Hallucination
1. Check knowledge sources are active and accessible
2. Check if webBrowsing is enabled (causes variable retrieval)
3. Check GPT instructions for conflicting directives
4. Check if applyModelKnowledgeSetting is false (blocks grounding)

### Routing Failures (Wrong Topic Triggered)
1. Count custom topics (more than 10 causes orchestrator confusion)
2. Check for overlapping trigger phrases across topics
3. Check topic descriptions (AI uses these for routing in generative mode)
4. Check connected agent botSchemaName values

### Truncation or Incomplete Responses
1. Check Response Formatting setting in UI
2. Check GPT instruction length (over 5500 causes overflow)
3. Check additionalInstructions verbosity (over 4 bullets causes expansion)
4. Check if webBrowsing is true (web content varies in length)

### Score Regression After Change
1. Did you rewrite working GPT? (Rewrite regression pattern)
2. Did you add topics? (Topic proliferation anti-pattern)
3. Did you change clearTopicQueue? (Topic stacking regression)
4. Did you enable OnGeneratedResponse? (Platform bug on most agents)

## Architecture Patterns (When to Use What)
- Knowledge-only (no custom topics): Simple QA from documents
- Knowledge + few topics: QA with some structured workflows
- Orchestrator + connected agents: Multi-domain routing
- Agent Flows + tools: Task execution with API calls

## Anti-Patterns (Never Do)
- Never have more than 10 custom topics on a knowledge-grounded agent
- Never use SearchSpecificFiles (restricts retrieval)
- Never mix JSON and prose requirements in same additionalInstructions
- Never copy-paste connected agent topics without updating botSchemaName
- Never trust pac copilot list status (verify in UI or Dataverse)
- Never rewrite GPT on agent scoring over 50% unless corruption confirmed

## Healthcare AI Standards
All clinical agents MUST have:
- contentModeration: High
- useModelKnowledge: false
- optInUseLatestModels: false
- isAgentConnectable: true (hub-and-spoke)
- authenticationTrigger: Always
- accessControlPolicy: GroupMembership
- webBrowsing: false
- codeInterpreter: false
