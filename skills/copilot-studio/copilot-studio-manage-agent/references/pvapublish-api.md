# PvaPublish API — Direct Publish via Dataverse Bound Action

## Endpoint

```
POST https://<org>.crm.dynamics.com/api/data/v9.2/bots(<botId>)/Microsoft.Dynamics.CRM.PvaPublish
```

## Headers
- `Authorization: Bearer <dataverse-token>`
- `Accept: application/json`
- `Content-Type: application/json`
- `OData-Version: 4.0`
- `OData-MaxVersion: 4.0`

## Body
**Empty JSON — no parameters.** The PvaPublish action does NOT accept an `asyncPublish` parameter:
```json
{}
```

## Response

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| 200 | Action executed | Check `PublishedBotContentId` in response body |
| 400 | Bad request — likely wrong params | Remove any parameters, retry with empty body |

## Response Body Shape
```json
{
    "@odata.context": "...",
    "PublishedBotContentId": "<guid or empty string>",
    "PublishBotJobResponse": null
}
```

## Known Issues

### `PublishedBotContentId` is empty string
The action succeeded (HTTP 200) but publish may have silently failed. This can happen when:
- The publish was a no-op (no changes to publish)
- A previous publish was still in progress
- A cached publish failure blocked the new publish

**Resolution:** Check `pac copilot list --environment <orgUrl>` for the Published state, or use the gateway publishv2-operations API instead.

### `"The parameter 'asyncPublish' is not a valid parameter"`
The request body included parameters. PvaPublish takes NO parameters — send `{}`.

### PAC CLI crashes after PvaPublish
If `pac copilot publish --environment --bot` crashes with `System.ArgumentException` after calling PvaPublish, the synchronizationstatus on the bot entity may be corrupt. Use the gateway publishv2-operations API to reset and re-publish.

## Preferred Alternative

The **gateway publishv2-operations API** (`/publishv2-operations`, POST to trigger, GET to poll) is more reliable than PvaPublish because:
- It supports `isInFinalState` + state polling
- It returns validation failure details (though generic)
- It doesn't corrupt pac CLI state
- It works with PVA-scoped tokens (`96ff4394-9197-43aa-b393-6a41652e21f8`)
