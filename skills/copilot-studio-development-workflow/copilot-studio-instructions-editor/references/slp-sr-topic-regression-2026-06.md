# SLP Single Response Topic Regression (June 2026)

## Timeline

| Date/Time | Run | Config | Score | State |
|-----------|-----|--------|-------|-------|
| Jun 12 2:29 AM | 260612_0229 | SR 100-item | **96%** | Peak: all caregiver topics OFF, clean KB |
| Jun 12 4:05 AM | 260612_0405 | SR 100-item | 92% | After KB/instruction changes |
| Jun 13 10:26 AM | 260613_1026 | SR 100-item | 90% | Continued decline |
| Jun 13 1:53 PM | 260613_1353 | SR 100-item | 89% | New caregiver topic ON (static template) |
| Jun 13 8:11 PM | 260613_2011 | SR 100-item | 86% | static SendActivity topic |
| Jun 13 10:11 PM | 260613_2211 | SR 100-item | **85%** | AnswerQuestionWithAI topic |
| Jun 13 11:07 PM | 260613_2307 | SR 100-item | **92%** | Caregiver topics deleted |
| Jun 14 12:23 AM | 260614_0023 | SR 100-item | **35%** | CB topic citation fix (anti-citation, no char limit) |\n| Jun 14 12:53 AM | 260614_0053 | SR 100-item | Running | CB topic rolled back to original config |\n| Jun 14 12:53 AM | 260614_0053 | SR 100-item | **95%** | CB topic restored (600 chars + Always cite) |

## Root Cause

Any authored caregiver topic that intercepts queries before the agent's instruction-level AI degrades Single Response scores:

1. **Static SendActivity with bracket placeholders** (`[Assessment...]`, `[HIGH/MODERATE/LOW]`): 8+ SR caregiver questions match triggerQueries and get template text. Grader sees incomplete placeholders. Result: 86-89%.

2. **AnswerQuestionWithAI with additionalInstructions**: The topic's additionalInstructions conflict with agent-level instructions. The agent generates less coherent answers than without the topic. Result: 85%.

3. **No caregiver topic at all**: Agent's instruction-level generative AI + Conversational Boosting handles caregiver queries. Result: 96% (peak).

## Key Insight

No authored topic can improve upon what the agent's instruction-level AI + Conversational Boosting already provides for caregiver documentation compliance queries. The topic's mere existence as a routing interceptor degrades performance, regardless of action type (SendActivity, AnswerQuestionWithAI, CreateGenerativeAnswers).

## Fix

Delete ALL caregiver-related topics:
- SLP Caregiver Documentation Compliance Audit (new)
- Caregiver Competency Audit (old)
- SLP Conv Guard - Caregiver Competency (old)
- SLP Conv Guard - Caregiver Cognitive Capacity (old)
- SLP Conv Guard - Caregiver Safety (old)

The agent should not have any caregiver-specific topic. Let the CB topic route caregiver queries through the agent's instructions and knowledge sources.

## CB Citation Artifact Issue

After deleting caregiver topics, SR went from 85% to 92% (not back to 96%). Remaining failures were caused by CB topic's citation-enforcing `additionalInstructions` (see `cb-topic-citation-fix.md`).

## CB Topic Experiment (June 14)

An experiment removed the CB topic's 600-char limit and "Always cite" instructions,
replacing them with anti-citation instructions. Results:

| Change | SR Score |
|--------|----------|
| Original CB (600 chars + "Always cite") | **92%** (baseline) |
| Modified CB (no limit, anti-citation) | **35%** (catastrophic regression) |
| **Rolled back to original** | **95%** (restored) |

**Conclusion**: The original CB config is correct and Microsoft Learn-aligned.
The 600-char limit keeps answers concise (Learn best practice), and the "Always
cite" instruction works WITH the platform's native citation rendering. Modifying
either causes regression.