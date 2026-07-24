# UI Architecture Pitfall: Agent-Wide Changes vs. Topic-Level Failures

## Problem Pattern
After a broad agent instruction patch, multiple topic-triggered queries fail with the same artifact (e.g., citation footnotes). The agent-level fix actually *increased* failures rather than fixing them.

## Root Cause
Agent instructions and triggered topics BOTH contribute to answers. Some topics have their own structured output formats that may amplify instruction prompts in unexpected ways (e.g., combining two "source anchor" formats causes duplication, bracket citations, or double-answer patterns).

## Indicator
- Broad patch causes regression in topics that worked fine before
- Failures show identical artifact across unrelated queries within the same topic category
- Topic-level preview still works (safety bypassed), but evaluation grade drops

## Fix Options
1. **Roll back the agent patch** and return to known-good baseline (safer, immediate)
2. **Disable or delete the specific topics** causing the regression and rely on agent base instructions
3. **Edit the topic via code editor** (More > Open code editor) with a narrower prompt update