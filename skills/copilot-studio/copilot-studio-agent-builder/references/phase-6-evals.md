# Phase 6 — Evals

## Eval API (Gateway)

Same auth as publishing but different endpoints.

```bash
TOKEN=$(az account get-access-token \
  --resource '96ff4394-9197-43aa-b393-6a41652e21f8' \
  --query accessToken -o tsv)
TENANT="03cc92c3-986c-4cf4-ae27-1478cf99d17f"
GATEWAY="https://powervamg.us-il106.gateway.prod.island.powerapps.com"
ENV="a944fdf0-0d2e-e14d-8a73-0f5ffae23315"
BOT="7667e9b4-cb86-f111-ab0f-70a8a5ae56f8"
```

## List Test Sets

```bash
curl -s "${GATEWAY}/api/botmanagement/v1/environments/${ENV}/bots/${BOT}/makerevaluations?api-version=2025-06-01" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-CCI-TenantId: $TENANT" \
  -H "x-cci-applicationsource: Web"
```

## Start an Eval Run

```bash
# Single-turn (SR) — use test set ID for single-turn
curl -s -X POST "${GATEWAY}/api/botmanagement/v1/environments/${ENV}/bots/${BOT}/makerevaluations?api-version=2025-06-01" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-CCI-TenantId: $TENANT" \
  -H "x-cci-applicationsource: Web" \
  -H "Content-Type: application/json" \
  -d '{"testSetId": "{testSetId}"}'
# Returns run ID for polling
```

## Poll for Results

```bash
curl -s "${GATEWAY}/api/botmanagement/v1/environments/${ENV}/bots/${BOT}/makerevaluations/{runId}?api-version=2025-06-01" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-CCI-TenantId: $TENANT" \
  -H "x-cci-applicationsource: Web"
# Check: state, aggregatedGraderResults
```

## Eval Loop (Proven Pattern)

```
Apply fix → Start Conv eval (20 cases, ~15 min) → Poll → Analyze → Fix
         → Start SR eval (100 cases, ~45 min) → Poll → Analyze → Repeat
```

Run Conv FIRST (faster feedback), then SR.

### Run Limits
- Max 20 runs per agent per 24 hours
- 1 active run at a time
- Cancel blocked runs via PATCH to Gateway

## Failure Classification

| Type | Symptom | Root Cause |
|------|---------|------------|
| abstention | Agent refused to answer | Guardrails or model safety |
| incomplete | Answer truncated or missing elements | Missing responseCaptureType or short answer |
| groundedness | Not supported by knowledge sources | KB gap, wrong topic matched |
| relevance | Wrong topic matched | Trigger phrases or modelDescription weak |
| format | Wrong output format | Instructions conflict |

## Fix Priority

| Order | Fix | Impact |
|-------|-----|--------|
| 1 | Instructions: EVAL CONTEXT + Route D expansion | +5-15 pts SR |
| 2 | Conversational boosting additionalInstructions | +5-10 pts |
| 3 | Remove unconditional length caps from responseInstructions | +10-15 pts Conv |
| 4 | Knowledge source binding (SASC fix) | +5-15 pts |
| 5 | KB gap fill for groundedness failures | +5-10 pts SR |
| 6 | Fallback reprompt | +3-5 pts |
| 7 | authMode=None | +40-67 pts if connector gate active |

## Score Targets

| Metric | Target | Critical |
|--------|--------|----------|
| SR (Single Response) | ≥ 95% | < 80% |
| Conv (Conversational) | ≥ 95% | < 80% |
| Up to 5% variance between runs is normal | | |

## Eval Gotchas

- **0/0 scored while InProgress**: Normal — scores populate at end
- **Conv takes 15-20 min, SR 45-75 min**: Set poll timeouts accordingly
- **Details endpoint 404**: Use list endpoint + aggregatedGraderResults instead
- **Token expiry**: PPAPI eval token ~15 min — refresh mid-run if needed
- **Stuck runs**: Cannot always cancel; wait for timeout
- **Grader is LITERAL**: Wants exact values from pasted text, not KB-searched approximations
