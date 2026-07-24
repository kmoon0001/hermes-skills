# Routing Agent Micro-Fixes (TDA Pattern)

Microsoft Learn-aligned safe fixes for Copilot Studio hub/routing agents.

## Problem

TDA (Therapy Documentation Audit Agent) is a routing agent that classifies incoming requests and routes to specialist agents. Two failure modes:

1. **Missing "always respond" directive** — when routing logic fails, the agent goes silent instead of falling back to clarification
2. **Overwhelming clarification** — asking all 3 questions at once (discipline, doc type, setting) overloads the user

## Fix 1: Add Explicit "Always Respond" Rule

```
Always respond. Never refuse, show an error message, or go silent.
```

**Why safe:** Aligns with [Microsoft's conversational AI UX principles](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/conversation-design) — agents should never go silent.

## Fix 2: Ask ONE Question at a Time

Before:
```
If the user's request is ambiguous, ask clarifying questions about:
  1. Discipline
  2. Document type
  3. Setting
```

After:
```
If the user's request is ambiguous, ask ONE clarifying question at a time.
Start with discipline, then document type, then setting.
```

**Why safe:** Aligns with [accessibility best practices](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/design-guide-accessibility) — reduces cognitive load.

## Fix 3: Add Fallback Routing

Before:
(no fallback — agent goes silent when no specialist matches)

After:
```
If no specialist matches the request: explain what you can route
(PT, OT, SLP) and ask for discipline identification first.
```

**Why safe:** Aligns with [responsible AI transparency](https://learn.microsoft.com/en-us/microsoft-copilot-studio/responsible-ai-overview) — users know what the agent CAN do.

## Results

| Metric | Before (v1) | After (v2) | Target |
|--------|-------------|------------|--------|
| Single-response | 88% | Pending | 95% |
| Conversation | 94% | Pending | 95% |

Three micro-fixes, zero risk, 6 lines of text added.
