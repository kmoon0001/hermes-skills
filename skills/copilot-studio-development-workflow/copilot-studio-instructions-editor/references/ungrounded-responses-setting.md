# "Allow ungrounded responses" — critical setting for Conversation evals

## What it does (MS Learn source)

Location: **Settings > Generative AI > Knowledge > "Allow ungrounded responses"**

When **ON**: The agent can respond using the model's general knowledge, even when it doesn't use any knowledge sources or tools. Conversational inputs (greetings, introductions, follow-ups from context) get normal responses.

When **OFF** (default in some environments): The agent BLOCKS any response generated in a turn where it didn't use a knowledge source or tool. The Fallback topic triggers instead.

> "When you turn off this setting, the agent blocks any response generated in a turn where it didn't use a knowledge source or tool. This condition means that if the agent decides to answer a question directly from the conversation history or its general knowledge, without calling a knowledge source or tool, the response is blocked and the fallback topic triggers."
> — https://learn.microsoft.com/microsoft-copilot-studio/knowledge-copilot-studio#allow-ungrounded-responses

## MS Learn example

```
User: "What is the return policy for online orders?"
Agent: "Our return policy allows returns within 30 days..." (from KB)

User: "Does that apply to sale items too?"
Agent: (BLOCKED) ← can answer from context but platform blocks it
```

## Observed failure pattern (SLP, June 2026)

- SLP Conv eval: 80% (4/5 retries fail)
- Failure message: "I'm sorry, I cannot help with that request"
- Root cause: Conversational persona "Sarah Chen" introduces herself, asks follow-up questions. Agent can answer from context/general knowledge but platform blocks ungrounded responses. Fallback topic fires.
- Agent instructions said "Always answer the user's request directly. Never refuse" — but platform override supersedes instructions
- Fix: Toggle ON + Publish → Conv improved to 90%+ immediately

## Why instructions alone can't fix this

The "Allow ungrounded responses" check happens at the platform level, AFTER the agent generates a response but BEFORE it's sent to the user. If the agent didn't call a knowledge source or tool in that turn, the response is blocked regardless of what the instructions say. This is a safety/compliance feature, not a prompt engineering issue.

## Fix steps

1. Settings > Generative AI > Knowledge
2. Toggle "Allow ungrounded responses" ON
3. Save
4. Publish the agent
5. Trigger new eval

## Risk consideration

With this setting ON, the agent can respond from general model knowledge without KB grounding. For clinical/medical agents, this means responses may not always be backed by specific knowledge sources. The agent's instructions should include guardrails like "cite knowledge sources" and "include advisory" to manage this risk.

## Related MS Learn pages

- Main setting docs: https://learn.microsoft.com/microsoft-copilot-studio/knowledge-copilot-studio#allow-ungrounded-responses
- Follow-up questions behavior: https://learn.microsoft.com/microsoft-copilot-studio/guidance/generative-mode-guidance#use-follow-up-questions
- Fallback topic: https://learn.microsoft.com/microsoft-copilot-studio/guidance/fallback-topic
- Generative orchestration: https://learn.microsoft.com/microsoft-copilot-studio/guidance/generative-orchestration
