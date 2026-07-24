# YAML-First Publish/Eval Pipeline (5-Layer Architecture)

Long-term, source-controlled replacement for the SPA-click + Monaco-injection +
timeout-and-hope workflow. Built bottom-up on Microsoft Learn — every API
endpoint and payload schema below has a citation.

## User preference — MS Learn is the source of truth

When working on Copilot Studio eval/publish, ground every API call, payload
schema, or invariant in Microsoft Learn before authoring. Use
`mcp_microsoft_learn_microsoft_docs_search` for this, not web search. If MS Learn
disagrees with what Dataverse returns, MS Learn wins; flag the discrepancy in a
note for follow-up.

If a piece of CS work can't be grounded in MS Learn (Cosmos schema, Mooncake
internal flows, etc.), call it out and either find the closest MS Learn surface
or stop and ask. Don't invent endpoints.

## The 5 layers (do not collapse them)

1. **Author**  — `topic_templates/*.yaml` + `routing_matrix.json` in git.
2. **Lint**    — `topic_lint.cjs` (see `scripts/topic_lint.cjs`). Pre-publish, blocking.
3. **Deploy**  — auth → Dataverse upsert (idempotent) → `pac copilot publish`.
4. **Eval**    — REST API trigger + poll (see references below).
5. **Gate**    — `eval_history.jsonl` records every run with score + delta
                 vs last 3; pipeline exits 1 if SR < 85% or Conv < 70%.

Each layer is independently useful. Don't try to ship full CI/CD before #1 and
#2 work — they're the lowest-effort, highest-leverage pieces.

## YAML parser pitfalls (learned the hard way)

Do NOT hand-roll a YAML parser for Copilot Studio topic YAMLs.

Working knowledge:
- `js-yaml.load()` handles single-doc reliably.
- `js-yaml.loadAll()` handles YAML files with `---` separators.
- Hand-concatenated multi-topic source files (e.g. `all_topics_consolidated.yaml`)
  have multiple `kind: AdaptiveDialog` keys at column 0 *with* `# TOPIC: ...`
  comment headers but no `---` separators. js-yaml rejects them as duplicate
  keys. The fallback: split the file on top-level-key restart at column 0, then
  re-parse each block independently.
- Strip `.yaml`/`.yml` from filenames before treating the basename as a topic
  NAME — periods in topic names break solution export (per MS Learn).

## Endpoint reference (validated against MS Learn, June 2026)

### Auth — Entra ID client credentials flow

```
POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={CLIENT_ID}
&scope=https://api.powerplatform.com/.default
&client_secret={SECRET}
&grant_type=client_credentials
```

Returns `{access_token, expires_in: 3599}`. Service principal must have RBAC
role on the target environment (not just AAD app registration).

### Eval API — list test sets

```
GET https://api.powerplatform.com/copilotstudio/environments/{envId}/bots/{botId}/api/makerevaluation/testsets?api-version=2024-10-01
Authorization: Bearer {token}
```

Returns array of test sets with `id`, `displayName`, `state`, `totalTestCases`.

### Eval API — trigger run

```
POST https://api.powerplatform.com/copilotstudio/environments/{envId}/bots/{botId}/api/makerevaluation/testsets/{testSetId}/run?api-version=2024-10-01
Authorization: Bearer {token}
```

Returns `runId`. Async — poll next endpoint.

### Eval API — poll run status

```
GET https://api.powerplatform.com/copilotstudio/environments/{envId}/bots/{botId}/api/makerevaluation/testruns/{runId}?api-version=2024-10-01
Authorization: Bearer {token}
```

`state` cycles: Started → InProgress → Completed (or Failed).
`testCasesResults[]` contains per-case `metricsResults[]` with `type` (test
method) and `result.data` (abstention, score, grader reasoning).

### Publish — PAC CLI

```
pac copilot publish --bot {botId} --environment {envId}
```

Returns publish ID string. Run from a directory where `pac auth create` has
been completed (token expires ~6/10 per session — re-auth if needed).

### Topic upsert — Dataverse Web API

The `botcomponent` table holds topic YAML. Create via:

```
POST https://{org}.crm.dynamics.com/api/data/v9.2/botcomponents
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Topic Display Name",
  "_parentbotid_value": "{botId}",
  "componenttype": 9,       // Topic (V2) — value 9 per MS Learn botcomponent ref
  "content": "<YAML escaped in JSON string>",
  "data": "<same or empty>",
  "schemaname": "<prefix>_<name_with_underscores>",
  "statecode": 0,
  "statuscode": 1
}
```

For updates: PATCH `/botcomponents({id})` with the same fields. Required:
`name`, `_parentbotid_value`, `componenttype`, `schemaname`.

## Threshold defaults (Kevin's gate)

- SR floor: 85% (block on drop)
- Conv floor: 70% (block on drop)
- Variance alarm: >10% from rolling avg (3 runs) means investigate grader before
  re-running — do not retry blindly unless you have a reason to suspect flakiness
- HC agents: keep "Allow ungrounded" OFF, CB ON, Compare Meaning at 0.50 for SR
  sets, accept 80-90% conv ceiling (MS Learn documented platform limit)

## eval_history.jsonl format

One JSON object per line. Don't pretty-print; this file is append-only.

```json
{"ts":"2026-06-21T12:34:56Z","bot":"ea52ad9c-...","env":"a944fdf0-...","testSet":"GUID","runId":"GUID","sr":0.93,"conv":0.71,"duration_s":312,"commit":"abc1234","model":"gpt-5-chat"}
```

Plot deltas vs last 3 on every run. No plotting framework required — plain
shell + awk + diff is enough for the "did this regress?" question.

## Failure mode → root cause map (session-memory encoded)

| Symptom                          | Most likely cause               | Cheap check                    |
|----------------------------------|----------------------------------|--------------------------------|
| SR jumped from 95% to 12%        | Question node w/o EndDialog     | `topic_lint.cjs` flags R4      |
| Publish fails with no clear err  | OnUnknownIntent override        | `topic_lint.cjs` flags R2      |
| Topic fires wrong case           | Trigger phrase overlap > 60%    | `topic_lint.cjs` flags R5      |
| Empty AdaptiveDialog in tenant   | Stub topic shipped               | `topic_lint.cjs` flags R3      |
| Eval run completes 0 cases       | mcsConnectionId missing / wrong | pass `mcsConnectionId` in POST |

## Related skills / files

- `scripts/topic_lint.cjs` — actual linter, runnable now
- `references/evaluation-rest-api.md` — fallback when SPA extraction fails
- `copilot-studio-topic-yaml-fixes` — surgical topic patches once lint passes
- `copilot-studio-topic-assessment` — decide whether a topic belongs at all
