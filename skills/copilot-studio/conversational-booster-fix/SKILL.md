---
name: conversational-booster-fix
description: Fleet-wide prompt + YAML to fix Conversational Booster / Fallback / Catch-All topic on any therapy agent (SLP, OT, PT, TDA) in Copilot Studio.
category: copilot-studio
---

# Conversational Booster Topic Fix — Fleet-Wide

Fix the Conversational Booster / Fallback / Catch-All topic on any therapy agent (SLP, OT, PT, TDA).

## Applying the Fix

### Option A: Dataverse API (fastest, fleet-wide)
Use the `copilot-studio-manage-agent` skill's Direct Dataverse repair fallback. Workflow:
1. `pac copilot list` to confirm bot IDs
2. Query `botcomponents` with `componenttype eq 9` to find the Fallback topic for each agent
3. PATCH each Fallback topic's `data` field with the new YAML
4. Deactivate overlapping Clinical Inquiry topics (`componentstate=2`, `statecode=1`)
5. Publish via `pac copilot publish` or Dataverse PvaPublish action
6. If publish fails with persistent cached error (same timestamp), try PvaPublish API or Copilot Studio UI

**PITFALLS (Dataverse API approach):**
- **URL encoding:** Use `urllib.parse.urlencode(..., doseq=True)` for OData `$filter` params — raw strings with spaces cause `URL can't contain control characters` error
- **Data vs Content:** PATCH only the `data` field (authoring YAML). The `content` field (runtime/compiled YAML) is populated during publish. Never patch `content` directly — the platform rejects it with `Unexpected character encountered while parsing value`
- **Verification:** Always GET the component back after PATCH to verify YAML persisted. Dataverse returns HTTP 204 for successful PATCH even if the content didn't actually take effect
- **CRITICAL: Data vs Content staleness — the #1 cause of "fix didn't work":** After patching `data`, if you never publish, the `content` field stays STALE (old broken YAML). Evaluations run against `content`, not `data`. The agent will appear "fixed" in the authoring canvas but still fail every eval with 0-5% scores — because the runtime is executing the old compiled YAML. Always verify BOTH fields after publish: `$select=data,content`. If `content` still has the old pattern (e.g., `FallbackCount`, static `SendActivity`, no `SearchAndSummarizeContent`), the publish didn't regenerate it — re-publish from UI. This was the actual root cause of PT/OT/TDA scoring 0-5% conversational (Jul 4 2026, Ensign Default) — not a GUID registration issue, not incorrect YAML, just a stale `content` field from an unpublished Dataverse PATCH.

### Option B: Copilot Studio UI (single agent)
1. Navigate to agent → Topics → Conversational Boosting / Fallback
2. Code Editor → Select All → Delete → Paste the new YAML
3. Deactivate overlapping topics (Topics list → ⋮ → Deactivate)
4. Click Publish

**PITFALL:** `pac copilot publish` can return the same failed timestamp on every retry even after successful YAML patch — this is a cached Dataverse state, not a validation error. Try the PvaPublish API action or UI publish as fallback.

**PITFALL — The GUID-caching myth:** When a Conversational Boosting topic is deleted and recreated (new component GUID) instead of patched in-place (preserved GUID), some sessions have theorized that the platform "caches the old GUID" internally and a new GUID fails to register with the orchestrator, causing 0-5% conversational scores. **This theory is disproven** — proven Jul 4 2026: PT/OT/TDA all had IDENTICAL component IDs to previously patched records (no deletion/recreation happened), yet still scored 0-5% conversational. The real cause was stale `content` field (unpublished Dataverse PATCH). The platform handles topic deletion/recreation routinely. When an agent scores 0-5% conversational, audit the `data` vs `content` fields first — don't assume a platform registration issue. 0-5% is too catastrophic for a GUID-only problem; it signals stale compiled YAML.

## Support Files
- `references/botcomponent-ids.csv` — Component IDs for Fallback and Clinical Inquiry topics across OT, PT, SLP, TDA agents
- `references/fleet-patching-script.py` — Runnable Python script to apply the fix across all 4 agents via Dataverse API (dry-run mode, add `--apply` flag)
- `references/stale-content-case-study.md` — Jul 4 2026 case study: PT/OT/TDA scored 0-5% conversational because `content` field was stale after Dataverse PATCH without publish. Includes verification code and failed-fix-attempt log.

## New-exp alias: boosting often IS `topic.Search`
On new-experience agents, display name may be "Conversational boosting" while `schemaname` ends in `.topic.Search`. Custom leaves that `BeginDialog` into `*.topic.Search` hand off into this catch-all — not a separate generative topic. If boosting is silent (SASC → EndDialog without SendActivity), every leaf that routes there is eval-hollow (Therapy Report Prep V2 2026-07-17). Resolve schemaname before declaring architecture healthy. See agent-audit-protocol Pattern P.

**Silent success path (P0):** SASC sets `Topic.Answer` then ConditionGroup ends with EndDialog only — **must** `SendActivity: =Topic.Answer` before EndDialog on the has-answer branch, plus elseActions rephrase path.

**Also require:** `responseCaptureType: FullResponse` on every SASC (plus allowLatencyMessage:false / latencyMessageSettings).

## The Problem (validated across 4 agents)

1. **Static SendActivity** — hardcoded paragraph, conversational grader sees irrelevant responses
2. **`CreateSearchQuery` indirection** — routes through `Topic.SearchQuery.SearchQuery` instead of `=System.Activity.Text`
3. **`SearchSpecificFiles` block** — restricts retrieval, causes groundedness failures
4. **`SearchSpecificKnowledgeSources` block** — same restriction, may point to deactivated sources
5. **No `variable: Topic.Answer`** — AI result not captured
6. **Priority conflict with Fallback** — two `OnUnknownIntent` topics compete (boosting priority -1 usually wins; still fix Fallback)
7. **Verbose `additionalInstructions`** (9+ lines) → truncation → incomplete grading
8. **Silent EndDialog** — Answer captured but never sent (notextresponse)
9. **Hard char caps** ("under 800 characters") in additionalInstructions — completeness killer; use concise-but-complete / conditional format

## The Fix Pattern (validated: OT 90%→95%, SLP conversational 100%)

- Direct `userInput: =System.Activity.Text` — no CreateSearchQuery
- `variable: Topic.Answer` — captures AI response
- No `SearchSpecificFiles` or `SearchSpecificKnowledgeSources` — search ALL knowledge
- `ConditionGroup` with `!IsBlank(Topic.Answer)` — handles success/no-answer
- Dynamic `SendActivity: =Topic.Answer` — contextual per turn
- Graceful fallback message — polite rephrase prompt
- `EndDialog + clearTopicQueue: true` on both paths
- **4-bullet `additionalInstructions`** — concise, focused

## Also Do
- Delete or deactivate the Fallback topic (elseActions replaces it)
- Delete or deactivate "General [Discipline] Clinical Inquiry" if it has SearchSpecificFiles pointing to dead sources
- Enable End of Conversation and Reset Conversation system topics
- Verify Work IQ = Disabled
- Verify Response Formatting in Settings → Generative AI → Responses
- Publish from UI (not CLI)
- **Verify publish regenerated `content`:** Query `botcomponents({id})?$select=data,content` and confirm `content` matches the fix-pattern YAML (has `SearchAndSummarizeContent`, has `Topic.Answer`, no `FallbackCount`, no static `SendActivity`). If `data` is correct but `content` is stale, re-publish from UI.
- Verify Work IQ still disabled after publish
- Wait 90 seconds
- Run evaluation 3x (single response + conversational)

## Verifying the Fix Took Effect (data/content staleness check)

After every Dataverse PATCH + publish cycle, run this verification query against the patched topic:

```
GET /api/data/v9.2/botcomponents({id})?$select=data,content
```

Check that BOTH fields contain the fix pattern:
- `SearchAndSummarizeContent` present in both `data` AND `content`
- `Topic.Answer` present in both
- No `FallbackCount`, no `CreateSearchQuery`, no static `SendActivity` in either field

If `data` is correct but `content` is empty or has the old pattern → publish didn't regenerate `content`. Re-publish from UI (not CLI — Copilot Studio UI publish is more reliable for regenerating compiled YAML). Do NOT skip this check — a correct `data` + stale `content` = 0-5% conversational scores that look like a different root cause (proven: PT/OT/TDA, Jul 4 2026, Ensign Default).

## YAML Templates

### For SLP_Specialist
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: SearchAndSummarizeContent
      id: search-cb
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Answer the user's SLP clinical or compliance question using CMS Ch. 15, ASHA guidelines, and all available knowledge sources.
        - First sentence must directly answer the question. Be a helpful SLP clinical and compliance chatbot.
        - Cite regulations inline by natural name. Plain text only -- no JSON or citation tokens.
        - Be complete for audits; concise for simple Q&A. End with: Clinical review required. Non-Device CDS only.
      responseCaptureType: FullResponse
      applyModelKnowledgeSetting: true
    - kind: ConditionGroup
      id: has-answer-check
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: SendActivity
              id: send-answer
              activity: =Topic.Answer
            - kind: EndDialog
              id: end-with-answer
              clearTopicQueue: true
      elseActions:
        - kind: SendActivity
          id: send-fallback
          activity: I don't have specific information on that in my SLP knowledge sources. Could you rephrase your question about SLP documentation compliance, Medicare guidelines, or clinical standards?
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
inputType: {}
outputType: {}
```

### For OT_Specialist
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: SearchAndSummarizeContent
      id: search-cb
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Answer the user's OT clinical or compliance question using CMS Ch. 15, AOTA standards, and all available knowledge sources.
        - First sentence must directly answer the question. Be a helpful OT clinical and compliance chatbot.
        - Cite regulations inline by natural name. Plain text only -- no JSON or citation tokens.
        - Be complete for audits; concise for simple Q&A. End with: Clinical review required. Non-Device CDS only.
      responseCaptureType: FullResponse
      applyModelKnowledgeSetting: true
    - kind: ConditionGroup
      id: has-answer-check
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: SendActivity
              id: send-answer
              activity: =Topic.Answer
            - kind: EndDialog
              id: end-with-answer
              clearTopicQueue: true
      elseActions:
        - kind: SendActivity
          id: send-fallback
          activity: I don't have specific information on that in my OT knowledge sources. Could you rephrase your question about OT documentation compliance, Medicare guidelines, or clinical standards?
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
inputType: {}
outputType: {}
```

### For PT_Specialist
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: SearchAndSummarizeContent
      id: search-cb
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Answer the user's PT clinical or compliance question using CMS Ch. 15, APTA standards, and all available knowledge sources.
        - First sentence must directly answer the question. Be a helpful PT clinical and compliance chatbot.
        - Cite regulations inline by natural name. Plain text only -- no JSON or citation tokens.
        - Be complete for audits; concise for simple Q&A. End with: Clinical review required. Non-Device CDS only.
      responseCaptureType: FullResponse
      applyModelKnowledgeSetting: true
    - kind: ConditionGroup
      id: has-answer-check
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: SendActivity
              id: send-answer
              activity: =Topic.Answer
            - kind: EndDialog
              id: end-with-answer
              clearTopicQueue: true
      elseActions:
        - kind: SendActivity
          id: send-fallback
          activity: I don't have specific information on that in my PT knowledge sources. Could you rephrase your question about PT documentation compliance, Medicare guidelines, or clinical standards?
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
inputType: {}
outputType: {}
```

### For TDA
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: SearchAndSummarizeContent
      id: search-cb
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Answer the user's therapy documentation audit question using CMS Ch. 15, APTA, AOTA, ASHA standards, and all available knowledge sources.
        - First sentence must directly answer the question. Be a helpful therapy compliance chatbot.
        - Cite regulations inline by natural name. Plain text only -- no JSON or citation tokens.
        - Be complete for audits; concise for simple Q&A. End with: Clinical review required. Non-Device CDS only.
      responseCaptureType: FullResponse
      applyModelKnowledgeSetting: true
    - kind: ConditionGroup
      id: has-answer-check
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: SendActivity
              id: send-answer
              activity: =Topic.Answer
            - kind: EndDialog
              id: end-with-answer
              clearTopicQueue: true
      elseActions:
        - kind: SendActivity
          id: send-fallback
          activity: I don't have specific information on that in my therapy documentation knowledge sources. Could you rephrase your question about compliance, Medicare guidelines, or clinical documentation standards?
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
inputType: {}
outputType: {}
```
