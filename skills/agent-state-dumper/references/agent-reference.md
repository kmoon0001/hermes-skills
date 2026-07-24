# Copilot Studio Agent Component IDs & Quick Reference

## Environment
- **Dev:** Default-03cc92c3 / org3353a370 / Therapy AI Agents Dev
- **Prod:** 6951ccc2-3791-ecf4-987f-3dab97bdc716 / Therapy AI Agents Prod

## Agent Component IDs (instructions, componenttype 15)

| Agent | Bot ID | Component ID | Model | Notes |
|-------|--------|-------------|-------|-------|
| OT_Specialist | 73b45e98-...8530 | 28c4402c-2a2b-45d7-888d-e3ef81b2f401 | GPT5Chat | ~8889 chars |
| PT_Specialist | 593407f3-...c81 | a6575469-8269-41ae-9e6e-dabd14e8ca63 | GPT5Chat | ~6612 chars |
| SLP_Specialist | 6e437a77-...0006 | 9a5e1289-baf3-44be-bb76-ce9d410c91dc | Sonnet46 | ~2933 chars |
| TDA_Orchestrator | 4d0ed0d3-...eba2 | ff00b80a-321b-44be-80a4-40c78072ffe3 | GPT5Chat | ~14K chars |

## Dataverse API Pattern

```
PATCH https://org3353a370.crm.dynamics.com/api/data/v9.2/botcomponents(<compId>)
Headers: Authorization: Bearer <token>, Content-Type: application/json, If-Match: *
Body: {"data": "<new instructions YAML>"}
```

## Quick Health Check

Run `node dump_agent_full.cjs <botId>` and check summary:
- `hasResponseFormat` MUST be true
- `hasNoCaveat` MUST be true
- `hasEvalSafe` MUST be true (for TDA)
- `conversationStarters` MUST be present
- `model` — prefer Sonnet46 if scoring low with GPT5Chat
