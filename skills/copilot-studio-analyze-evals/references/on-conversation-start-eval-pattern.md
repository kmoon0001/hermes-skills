# OnConversationStart Eval Pattern (Validated 2026-07-09)

## The Problem

A topic with `beginDialog.kind: OnConversationStart` fires on **every new conversation**. If the topic starts with a `Question` node showing a `ClosedListEntity` menu (e.g., "Choose document type"), the agent **always responds with a menu prompt** before answering anything.

**Eval impact:** For Single-Response evals, ~50% of questions are coaching/how-to queries like "How do I document goals?" The agent answers these with a menu prompt instead of a direct answer — instant fail. This alone can cause a 10-15 point SR drop.

## Why It Gets Deactivated

The obvious fix is to set `statecode=1` (inactive). This works but the routing logic (6 BeginDialogs to audit topics, SearchAndSummarizeContent for general Qs) is lost. The agent's raw GPT handles everything without structured routing.

## The Correct Fix (not reactivation)

**Do NOT blindly reactivate.** Instead, change the trigger:

```yaml
# FROM:
beginDialog:
  kind: OnConversationStart

# TO:
beginDialog:
  kind: OnRecognizedIntent
  intent:
    displayName: Document Upload Intake
    triggerQueries:
      - upload a document
      - review my documentation
      - I need a document review
      - evaluate my progress report
      - check my discharge note
      - audit my plan of care
      - review my treatment note
      - check my recertification
      - evaluate my episode of care
      - i have a document to upload
      - therapy documentation review
      - document intake
      - i need compliance review
```

This makes the intake menu **opt-in** (only fires when user mentions document upload) instead of **forced** (on every conversation). All routing logic (BeginDialogs, elseActions SearchAndSummarizeContent, EndDialog+CTQ) stays unchanged.

## API Safety

Unlike true system topics (OnEscalate, OnError, OnSystemRedirect), OnConversationStart is a **custom topic** that uses a system trigger kind. The root-level `kind: AdaptiveDialog` makes it API-safe:

```python
# This WORKS for OnConversationStart topics:
PATCH /api/data/v9.2/botcomponents({topicId})  # HTTP 204, publish OK

# This BREAKS publish for true system topics:
PATCH /api/data/v9.2/botcomponents({escalateId})  # HTTP 204, publish FAILS
```

## ⚠️ CRITICAL REGRESSION: OnRecognizedIntent Change Caused Conv Score Drop (Validated 2026-07-09)

**Finding:** Changing `OnConversationStart` to `OnRecognizedIntent` with trigger phrases caused a **15-point Conv regression** (45% → 30%) on the Medicare Part B Compliance Agent, while SR stayed roughly stable (81% → 78%).

**Root cause analysis:** The trigger-phrases approach doesn't match multi-turn conversation flows. Conv test cases often start with a general request like "I need my documentation reviewed" which SHOULD match a trigger phrase, but:
- The first user message in a Conv scenario doesn't always match the trigger phrases precisely
- After the first turn, the conversation context changes — the topic won't fire again for follow-ups
- The ClosedListEntity menu in the Conversation Start topic causes routing confusion when triggered mid-conversation

**Current best understanding:** OnConversationStart topics are best left DEACTIVATED (`statecode=1`) for agents that need high Conv scores. The deactivation costs ~5-10 points on SR (fixed by instructions) but avoids a larger Conv penalty.

**Recommended strategy:**
1. Do NOT reactivate deactivated OnConversationStart topics
2. Fix the SR coaching questions via conditional instructions format (additive, +10 pts SR, no Conv impact)
3. Fix Conv via EndDialog+CTQ on system topics
4. Accept that the OnConversationStart routing hub is not recoverable for Conv-heavy agents

**Alternative experiment (not yet validated):** Strip the ClosedListEntity `Question` node from OnConversationStart entirely — keep only a SendActivity welcome message + elseActions routing. This would avoid the menu hijack while keeping the routing. Risk: unpredictable.

## Verification

## Multi-Bot Org — Conversation Start Belongs to Specific Agent (Validated 2026-07-14)

In a multi-agent org (Therapy AI Agents Dev), the Conversation Start topic (`OnConversationStart` type=9) belongs to a SPECIFIC bot via `_parentbotid_value`. It does NOT automatically apply to sibling bots.

**Org inventory (Therapy AI Agents Dev):**
- `b0346795` = Medicare Part B Compliance Agent — NO Conversation Start
- `f5a9bca6` = Therapy Documentation Assistant (schema `cr917_TherapyDocuementationAssistant`) — NO Conversation Start, bare agent (0 custom components)
- `66b20e43` = Therapy Documentation Feedback B (schema `cr53f_TherapyDocumentationFeedbackB`) — HAS Conversation Start (state=0 ACTIVE)

**Conversation Start content (Therapy Documentation Feedback B, 366 chars):**
```yaml
kind: AdaptiveDialog
beginDialog:
  kind: OnConversationStart
  id: main
  actions:
    - kind: SendActivity
      id: sendMessage_M0LuhV
      activity:
        text:
          - "Hello, I'm {System.Bot.Name}. How can I help?"
        speak:
          - "Hello and thank you for calling {System.Bot.Name}, powered by generative AI. How may I help you today?"
```

This is a simple greeting with NO routing, NO BeginDialogs, NO document-type Question. It just says hello and exits — the conversation falls through to standard intent matching. This pattern is safe for eval scores because a one-line greeting only costs one turn before the real answer. However, it adds no routing value.

**Investigation workflow for checking Conversation Start:**
```python
# 1. List all bots in the org
GET /api/data/v9.2/bots?$select=name,botid,schemaname

# 2. Find Conversation Start topics
GET /api/data/v9.2/botcomponents?$top=500&$select=...,data
# Filter client-side: name='Conversation Start', componenttype=9

# 3. Check if the topic has routing
data = comp.get('data','')
routing = 'BeginDialog' in data or 'Question' in data
menu = 'ClosedListEntity' in data
```

**Key insight:** A Conversation Start that only sends a greeting (no Question, no ClosedListEntity) does NOT hurt eval scores — it just adds a hello before the real answer. One that asks "What type of document?" via a Question node with entity selection WILL fail SR evals (every test case gets the menu instead of an answer).
