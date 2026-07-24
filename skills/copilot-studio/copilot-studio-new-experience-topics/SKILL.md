---
name: copilot-studio-new-experience-topics
description: "Diagnose and fix new-experience Copilot Studio agent topic issues — ConversationStart gates, grounding, MultipleTopicsMatched, Fallback/Search priority, eval queue management."
version: 1.0.0
tags: [copilot-studio, new-experience, topics, grounding, evaluation]
---

# New-Experience Agent Topic Fixes

Proven patterns for fixing new-experience (Sonnet 4.6, GPT) Copilot Studio agents. Based on Therapy Doc Feedback agent fix (15% → 63% Conv).

## Quick Diagnostic Checklist

When conv eval is low:
1. Check ConversationStart for Question nodes (OnConversationStart fires EVERY conversation)
2. Check MultipleTopicsMatched for `triggerBehavior: Always`
3. Check Fallback vs Search topic priority — both have OnUnknownIntent
4. Check if Search topic is ACTIVE
5. Check GPT instructions for citation rules (groundedness failures)

## Pattern 1: Question-First Anti-Pattern

**Symptom:** Conv eval 0-15%, all test cases too many turns
**Cause:** ConversationStart topic has `kind: Question` that fires `OnConversationStart`
**Fix:** Replace Question with SendActivity + EndDialog. Let Fallback handle actual queries.

```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnConversationStart
  id: main
  actions:
    - kind: SendActivity
      id: greeting
      activity: Hello! Describe what you need help with, and I'll review your documentation or answer Medicare compliance questions.
    - kind: EndDialog
      id: end
      clearTopicQueue: true
```

## Pattern 2: MultipleTopicsMatched triggerBehavior: Always

**Symptom:** Agent asks "did you mean..." on every single turn
**Cause:** `triggerBehavior: Always` makes OnSelectIntent fire even for single-matched intents
**Fix:** Remove `triggerBehavior: Always` line entirely (default = only on ambiguity). Also fix "None of these" routing: use CancelAllDialogs + EndDialog instead of ReplaceDialog → Fallback (avoids trigger loop).

## Pattern 3: Fallback Overrides Search

**Symptom:** Agent apologizes instead of searching knowledge
**Cause:** Both Fallback and Search have `kind: OnUnknownIntent`. Fallback has default priority (higher), Search has `priority: -1` (lower). Fallback fires first and returns "I'm sorry."
**Fix:** Give Fallback the same SearchAndSummarizeContent logic as Search topic.

## Pattern 4: Groundedness Failures

**Symptom:** rel=Yes, comp=Yes, but ground=No on 6/7 failures
**Causes (check all):**
1. GPT instructions missing citation mandate
2. Fallback topic not using SearchAndSummarizeContent
3. Search topic INACTIVE
4. `useModelKnowledge: true` not in bot configuration

**Fix order:** instructions first, then Fallback, then Search activation.

### Groundedness Diagnostic Flow (validated Jul 5 2026)

When multiple groundedness=No failures persist after basic fixes:

1. **Check bot config** — `GET /bots/{id}?$select=configuration` — `useModelKnowledge: true` and `isSemanticSearchEnabled: true`
2. **Check knowledge sources** — `componenttype eq 14` — all statecode=0 (Active), count matches expected
3. **Check GPT instructions** — citation mandate at TOP, not buried. Examples: "Per CMS BP Manual..."
4. **Check Fallback topic** — must use `SearchAndSummarizeContent`, not static apology
5. **Check Search topic** — must be ACTIVE (statecode=0)
6. **If all correct and groundedness still fails** — model generates good answers without citing. Move citation rule to absolute first line of instructions.

### Related Skills
- `copilot-studio-instructions-v9` — citation rules, RESPONSE FORMAT, no-refusal, merging two instruction versions
- `copilot-studio-run-eval` — gateway API, eval cancel, token capture, polling

## Eval Queue Management (Gateway API)

Cancel stale evals:
```
PATCH /makerevaluations/{runId}/cancel
Body: {"evaluationRunId": "<runId>"}
```

Start fresh eval:
```
POST /makerevaluations
Body: {"testSetId": "<testSetId>"}
```

List runs:
```
GET /makerevaluations?count=10
```

Gateway: `https://powervamg.us-il107.gateway.prod.island.powerapps.com/api/botmanagement/v2`
Required headers: X-CCI-ApplicationSource, X-CCI-BapEnvironmentId, X-CCI-BotId, X-CCI-CdsBotId, X-CCI-TenantId, X-CCI-OrganizationId, x-ms-user-agent

## Token Capture

CDP token capture requires eval tab open in browser:
```bash
node "D:/my agents copilot studio/pipeline/scripts/cdp_capture_token.cjs" --port 9223
```
Token expires ~15min. Saved to `%USERPROFILE%\.copilot-studio-cli\test-agent-token.txt`

## pac publish caching

If `pac copilot publish` keeps returning same cached failure timestamp, the bot's synchronizationstatus is stuck. Publish from Copilot Studio UI instead.
