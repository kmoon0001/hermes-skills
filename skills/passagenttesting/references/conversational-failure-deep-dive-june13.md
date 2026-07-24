# Conversational Failure Deep Dive — June 13 Pattern

Use this reference when Copilot Studio single-response scores recover but conversational evaluations remain below target.

## Score shape that triggered this pattern

- SR mostly recovered while Conv lagged: e.g. OT SR 88 / Conv 75, PT SR 91 / Conv 85, SLP SR 89 / Conv 90, TDA SR 97 / Conv 85.
- This means the remaining issue is usually not only KB quality. Multi-turn tests are sensitive to routing, action/tool finalization, partial-answer behavior, citations, and default system topics.

## Failure signatures and fixes

### 1. Raw tool/action leakage

**Evidence pattern:** Evaluation details show the agent response as JSON/function-call text such as:

```json
{"recipient_name":"functions.Analyze-PT-Recertification-Note","parameters":{"explanation_of_tool_call":"..."}}
```

**Grader wording:** "The agent refuses to help by not providing an analysis and only describing the tool call."

**Fix:** Add an instruction-level rule to the affected specialist and any router agent:

> Never output raw tool calls, JSON function calls, `recipient_name`, `parameters`, or `explanation_of_tool_call` text. If a tool/action is invoked, summarize the final clinical/compliance answer in natural language.

Then inspect the topic/action that triggered. The topic may be returning action metadata instead of a final Message node.

### 2. Record not found / no document becomes a refusal

**Evidence pattern:** Agent says it cannot locate `record_id` or cannot verify because no document is available, then gives a generic checklist. Even helpful checklists can fail because the first sentence is framed as inability/refusal.

**Grader wording:** "Refuses to directly check the record because it cannot find it... counts as a refusal to help with the main request."

**Fix instruction:**

> If a record_id or document is referenced but the record cannot be retrieved, do NOT say you cannot help or stop. State that direct verification is limited, then provide a partial compliance review/checklist based on the document type, likely risk areas, required elements, and next documentation steps.

Lead with useful partial analysis, not inability.

### 3. Relevant/complete but missing citations

**Evidence pattern:** Grader says "Seems relevant" and sometimes "Seems complete" but still fails with "One or more answers didn't cite knowledge sources."

**Fix instruction:**

> Every conversational answer must include at least one natural source anchor when discussing Medicare, documentation, caregiver training, fall risk, skilled justification, recertification, LCR, or denial risk. Use natural anchors like "Per CMS Chapter 15..." or "APTA/ASHA/AOTA documentation guidance...". Do not output internal citation metadata tags.

Also verify the relevant knowledge source is selected/retrieved for that topic.

### 4. Default escalation topic overrides good routing instructions

**Evidence pattern:** TDA/router agent fails representative/escalation case with:

> "Escalating to a representative is not currently configured for this agent..."

**Grader wording:** "The agent refuses to help and does not provide any information or guidance for contacting a representative."

**Fix topic text:** Replace/enable the live representative/escalation topic with:

> For audit support or escalation, contact your facility rehab director/clinical leader first, then your therapy compliance or regional clinical support team if the issue involves Medicare defensibility, denial risk, LCR requirements, payer review, or audit exposure.
>
> If you need help preparing the escalation, provide the discipline (PT/OT/SLP), document type, payer/setting, record_id, and the specific compliance concern. I can summarize the issue, list missing documentation elements, assign a preliminary risk level, and draft the questions to send to the reviewer.
>
> I do not have a specific phone number or email configured in this agent, but I can draft the escalation summary and identify who should review it.
>
> Timeline guidance: urgent safety/compliance issue = same business day to rehab/clinical leadership; routine documentation review = within 1-2 business days; payer denial/audit deadline = escalate immediately and include due date.

If an exported YAML already has this but live agent still fails, the fixed topic is not live, disabled, not published, or overridden by the default system topic.

## Browser extraction workflow

1. Navigate to `/evaluation` for each bot and wait ~30s for SPA rendering.
2. Parse recent run rows: conversation runs show `20 test cases • Data type: conversation`.
3. Click the run-name button itself, not the row center. In Fluent UI grids, the row center may not navigate while the left run-name button does.
4. On run details, capture `Pass (N)` / `Fail (N)` and rows.
5. Click a failed row and save details. Key text appears under `Test case details`:
   - grader reason lines
   - `Question:`
   - `Agent response:`
   - `Knowledge sources`
   - `Topics`
6. If a specific agent's detail row refuses to open, proceed with systemic fixes and mark that agent for manual drill-in rather than blocking the whole fleet.

## Long-running update behavior for this user

During these Copilot Studio deep dives, give periodic progress updates before/after long browser automation runs. The user explicitly asked for periodic updates and gets frustrated when tool calls are executed with empty assistant responses. Never return an empty message after tool calls; summarize what was learned and continue.