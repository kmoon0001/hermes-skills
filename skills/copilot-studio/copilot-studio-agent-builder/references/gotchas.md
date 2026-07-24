# Gotchas — Compiled Pitfalls from All 41 Copilot Studio Skills

## Data Integrity

1. **`data` vs `content` field**: Only `data` is patchable via API. `content` is UI-only. PATCHing `content` = HTTP 400.
2. **Line endings**: Dataverse stores YAML with `\r\n` (CRLF). `\n` alone causes double-CR artifacts. Always normalize.
3. **BOM characters**: `\uFEFF` at file start breaks js-yaml. Strip before PATCH.
4. **System topics**: PATCHing system topic data breaks publish with `SynchronizationSystemError`. Use UI code editor only.
5. **Two JSON objects on one line**: Knowledge graph `.jsonl` corruption — use brace-counting to detect and fix.
6. **Python 3.13 `_validate_path`**: OData filter URLs with spaces fail. Use `urllib.parse.quote()` or `az rest`.

## Auth Tokens

7. **Token mix-up**: Dataverse token (resource `.dynamics.com/`) vs Gateway token (resource `96ff4394-...`). Using wrong one = HTTP 403.
8. **Token scope trailing slash**: Dataverse resource MUST end with `/`.
9. **PPAPI token expiry**: ~15 min. Refresh mid-run for long eval polls.
10. **X-CCI-TenantId**: Must be FULL GUID. Short prefix = `BadRoutingHeaderValue` / 4002.

## Knowledge Sources

11. **API CANNOT upload files**: Only PublicSiteSearchSource (web-crawl) and SharePoint via API. File uploads = UI only. Do not attempt.
12. **KS YAML line endings**: MUST be `\r\n`. `\n` causes artifacts.
13. **schemaname prefix**: New KS must use agent's customization prefix. Find via existing topic schemaname.
14. **Empty conversation starter**: `conversationStarters: [{}]` blocks publishing. Replace with valid starter.

## Topics

15. **Missing `responseCaptureType: FullResponse`**: Causes incomplete eval responses. Required on every SASC node.
16. **Question nodes in audit topics**: Kills SR eval — grader sees question not answer.
17. **Missing `EndDialog` + `clearTopicQueue: true`**: Context bleed between topics.
18. **`applyModelKnowledgeSetting: true` without KS binding**: Agent leans on model memory, ignores KBs entirely.
19. **System topic PATCH**: Returns 204 but breaks publish. Recovery: revert data + UI edit.
20. **Conversational boosting hollow handoff**: SASC→EndDialog without SendActivity = silent failure for unmatched queries.
21. **SearchSpecificFiles with empty list**: Blocks ALL KB retrieval. Symptom: 0% eval scores.
22. **Topic display name with periods or trailing spaces**: Causes YAML parse issues.

## Publishing

23. **Gateway publish empty body**: MUST send `{}`. Empty body = error.
24. **PvaPublish staleness**: Returns cached timestamps. Gateway publishv2 is freshest.
25. **PAC publish cache quirk**: May show old failure timestamp. Check `publishedon` in Dataverse.
26. **Region discovery**: Gateway regions vary per env. us-il106 works for Therapy AI Dev.

## Evals

27. **0/0 scored while InProgress**: Normal. Scores populate at end of run.
28. **Details endpoint 404**: Use list endpoint + aggregatedGraderResults.
29. **Conv first, then SR**: Conv is faster (20 cases, ~15 min). SR is 100 cases, ~45 min.
30. **20 runs/day limit**: Per agent. Plan iterations accordingly.
31. **Grader is LITERAL-EXTRACTION**: Wants exact values from pasted text. KB-searched approximations fail.
32. **17 of 28 failures hit NO topic**: Topic-level edits can't reach them. Fix instructions + boosting.
33. **Per-case failure reason**: Lives at `details.testCases[].graderMetrics.queryResponseMetrics[].properties` NOT at `case.metrics.evaluationResult`.

## Agent Instructions

34. **Route D rules buried deep**: Don't reach catch-all path. Put at top.
35. **responseInstructions overrides instructions**: Settings box contradicts main instructions = eval failures.
36. **2000-6000 char sweet spot**: <2000 = under-specified. >8000 = eval slowdown.
37. **No unconditional length caps**: "Under 800 chars" + "prioritize completeness" = Conv drops 20pp.
38. **No "No headers or markdown"**: Blocks structured formatting for compliance audits.
39. **authMode=None for general questions**: Integrated auth gate = 40-67% SR failures.

## MCP / Knowledge Graph

40. **JSONL format**: One JSON object per line. Two objects on one line = corruption.
41. **MEMORY_FILE_PATH**: Must be set for shared graph. Omitted = isolated graph in npx cache per agent.
42. **Forbidden leading/trailing whitespace**: Notion API path validation is strict.

## Notion

43. **Database ID ≠ Data Source ID**: Use `database_id` for page creation, `data_source_id` for querying.
44. **Page must be shared with integration**: 404 = page not shared with the integration named in the API key.
45. **Two separate integrations**: "Hemres" and "hermes" are different. Must share with the right one.
