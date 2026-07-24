# Copilot Studio Citation Behavior

## Platform Behavior (Microsoft Learn)

Per Microsoft Learn knowledge management documentation:
- **"Currently, citations returned from a knowledge source can't be used as inputs to other tools or actions."**
- Citations (`[1]: cite:1 "Source-1"`, `[1] [2] [3]` footnotes, raw URLs) are **platform-level rendering** appended by `SearchAndSummarizeContent` and `CreateGenerativeAnswers` actions.
- The platform controls citation formatting; agent instructions can influence but not fully suppress them.

## Proven Pattern

The original Conversational Boosting topic configuration (600-char limit + "Always cite using [Source Name] format") works WITH the platform's citation behavior, not against it. This configuration achieved:
- Conversation: 95%
- Single Response: 96% (peak) / 95% (stable)

## Anti-Patterns (Do NOT Use)

### Attempting to suppress citations in instructions
Adding "NEVER include citations" or "Do not output cite:1" to `additionalInstructions` conflicts with platform behavior and causes:
- Unpredictable response formatting
- Grader penalizes inconsistent output
- Does NOT actually stop the platform from appending citations

### Removing the 600-character limit
The CB topic's 600-char limit keeps responses concise and focused. Removing it causes:
- Excessively long answers (slowing 100-item SR evals to 40+ minutes)
- Massive SR regression (95% → 35%)
- Mismatch with grader expectations for concise single-response answers

## Topic Interception Damage

Any authored topic that intercepts knowledge queries (caregiver-specific, discipline-specific) before the Conversational Boosting topic degrades Single Response scores because:
1. Authored topics route through topic actions (SendActivity, AnswerQuestionWithAI) which may not leverage full knowledge base
2. Static SendActivity with template placeholders produces incomplete answers
3. Even AnswerQuestionWithAI with additionalInstructions can conflict with the agent's main instructions

**Best practice**: Let the Conversational Boosting topic + agent instructions handle all knowledge queries. Only create authored topics for very specific, frequent intent patterns where the CB fallback consistently fails.
