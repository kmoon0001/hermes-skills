# Generative AI Responses Template — API Gap

## The Gap
The **Settings → Generative AI → Responses** field in Copilot Studio is NOT accessible via the Dataverse API. No `botcomponent` or `bot` field exposes this template. It's a UI-only configuration stored client-side or in a non-queryable backend service.

## CRITICAL: Override Behavior
The UI states: **"If these conflict with other instructions for this agent, these will override."** This field takes precedence over the main Instructions field AND topic-level instructions.

**Real bug found Jul 2026:** The text "No headers or markdown" in this field overrode the Route A DOCUMENT REVIEW OUTPUT CONTRACT (requires markdown headers, tables, 🔴🟡🟢). Every audit response came out as plain text with no formatting.

## How to Read/Write
- **Read:** Copilot Studio → Settings → Generative AI → Responses
- **Write:** Same UI — paste into the rich text editor. No API path exists as of Jul 2026
- **Automation fails:** UIA ValuePattern.SetValue and SendInput both fail to trigger the SPA's onChange handler. Must be done manually.

## Medicare Part B Agent — Current (problematic):
```
Respond concisely. Use 2-3 bullet points with inline citations. No headers or markdown. Keep responses under 4 sentences for simple questions.
```

## Recommended Replacement (~380 chars):
```
Follow your route-specific output contracts:
• Document audits — markdown headers, tables, 🔴🟡🟢 risk ratings, inline citations
• General questions — 2–3 concise bullet points with citations
• Missing docs — state what's needed, invite paste

Cite sources, disclose AI status, keep simple answers under 4 sentences.
```

## Agent aISettings (Dataverse API-readable):
```json
{
  "contentModeration": "Low",
  "isFileAnalysisEnabled": true,
  "isSemanticSearchEnabled": false,
  "useModelKnowledge": false
}
```
