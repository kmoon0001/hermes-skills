# Copilot Studio Publish Workflow

## Publish via pac CLI (Preferred)

Fastest and most reliable method — no browser automation needed:

```bash
pac copilot publish --environment <environment-guid> --bot <bot-guid>
```

- `--environment` accepts GUID or absolute https URL (alias: `-env`)
- `--bot` accepts the bot GUID (NOT schema name — `--bot schemaName` returns "not found")
- The bot GUID is the one from the Copilot Studio URL: `/environments/<env-id>/bots/<bot-guid>`

Example:
```bash
pac copilot publish --environment 077422cf-d088-e3d7-917e-5c9a9b64710c --bot 9e7b871d-1d80-f111-ab0f-000d3a5b0d6c
```

**Output on success:**
```
Published successfully! <bot-guid> Succeeded [<timestamp>].
```

## Publish via UI

1. Navigate to the agent in Copilot Studio
2. Click the **Publish** button in the top toolbar
3. Wait for confirmation ("Published successfully")

## Verify Publish Took Effect

Check the `publishedon` timestamp on the bot record via Dataverse:

```bash
TOKEN=$(cat /c/Users/kevin/Desktop/az_token.txt)
curl -s -H "Authorization: Bearer $TOKEN" -H "Accept: application/json" \
  "https://<org>.crm.dynamics.com/api/data/v9.2/bots(<bot-guid>)?\$select=publishedon"
```

If `publishedon` updates to the current time, the publish succeeded. The timestamp is in UTC.

## Fix Priority Order for Pre-Publish Deployment

Apply fixes in this order before publishing. Each depends on the previous being live:

| Priority | Fix | Domain |
|----------|-----|--------|
| 1 | responseCaptureType: FullResponse on all SASC nodes | D3.4 — prevents eval truncation |
| 2 | EVALUATION CONTEXT block in instructions | D1.3 — prevents abstention failures |
| 3 | Model name typo fix (GPT55Chat → GPT5Chat, etc.) | D1.8 — correct inference model |
| 4 | responseInstructions format restrictions removed | D1.4 — unblocks professional formatting |
| 5 | modelDescription on all custom topics | D4.2 — improves topic routing |
| 6 | Restore empty SASC nodes (full pipeline) | D3.4 — fixes broken topics |
| 7 | allowLatencyMessage: false on all SASC nodes | D3.4 — prevents latency UI issues |
| 8 | Fallback avoidance language fix | D8.2 — prevents abstention on unmapped queries |
| 9 | Upload missing KB files referenced in instructions | D2.3 — prevents ungrounded answers |

## Publish After Dataverse PATCH Operations

When you use Dataverse PATCH to fix instructions, topics, or settings, the changes are stored in Dataverse but NOT live until you publish. Always follow a PATCH batch with a publish command:

```bash
# After all PATCH operations complete:
pac copilot publish --environment <env-id> --bot <bot-guid>

# Verify
az account get-access-token --resource 'https://<org>.crm.dynamics.com' \
  --query accessToken -o tsv > "C:/Users/kevin/Desktop/az_token.txt"
TOKEN=$(cat /c/Users/kevin/Desktop/az_token.txt)
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://<org>.crm.dynamics.com/api/data/v9.2/bots(<bot-guid>)?\$select=publishedon"
```

## Pitfalls

- `pac copilot publish --bot schemaName` returns "Copilot with ID 'xxx' not found." Use the GUID.
- The `publishedon` timestamp is in UTC — the pac CLI output shows local time.
- Publish can take 30-90 seconds depending on agent complexity.
- If publish fails, check `synchronizationstatus.lastFinishedPublishOperation.diagnosticDetails` on the bot record for the exact error.
- MissingRequiredProperty:Title on instruction component = `conversationStarters` field needs both `title:` and `text:` sub-fields.
