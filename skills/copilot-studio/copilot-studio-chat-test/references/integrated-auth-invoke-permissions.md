# Integrated-auth Copilot Studio chat: invoke permissions diagnostic

Use when a published Copilot Studio agent is M365/integrated-auth mode and chat invocation fails even though PAC/Dataverse operations work.

## Symptom

`chat-with-agent.bundle.js` can detect the agent mode, but sending a message starts auth loops, hangs at `Starting new conversation...`, or the raw conversation endpoint returns:

```json
{
  "code": "Forbidden",
  "message": "The caller is not authorized to perform the request.",
  "innererror": {
    "code": "InsufficientDelegatedPermissions",
    "message": "Authorization denied: Application missing required delegated permissions: [CopilotStudio.Copilots.Invoke, All.All.ReadWrite]"
  }
}
```

This means Dataverse/PAC access is sufficient to patch/publish/list the bot, but not sufficient to invoke integrated-auth chat.

## Fast diagnostic

1. Confirm detect-only works:

```bash
cd "D:/my agents copilot studio/pipeline"
node scripts/chat-with-agent.bundle.js --detect-only \
  --agent-dir "<agent workspace>"
```

Expected for M365 auth:

```json
{
  "status": "ok",
  "mode": "m365",
  "authenticationmode": 2,
  "schemaName": "<live schema>"
}
```

2. If chat auth is blocked, probe the raw endpoint with a Power Platform token to get the real HTTP error. Endpoint format:

```text
https://<environment-guid-no-dashes-minus-last-2>.<last-2>.environment.api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/<live-bot-schema>/conversations?api-version=2022-03-01-preview
```

Body:

```json
{"emitStartConversationEvent": true}
```

Headers:

```text
Authorization: Bearer <token for https://api.powerplatform.com>
Content-Type: application/json
Accept: text/event-stream
```

If this returns HTTP 403 with `InsufficientDelegatedPermissions`, stop retrying device codes. The issue is app/user permission, not local files.

## Known Power Platform API identifiers

Power Platform API resource app ID:

```text
8578e004-a5c6-46e7-913e-12f58912df43
```

Delegated scope needed for integrated-auth chat invoke:

```text
CopilotStudio.Copilots.Invoke
scope id: 204440d3-c1d0-4826-b570-99eb6f5e2aeb
```

Application role also exists for app-only scenarios:

```text
CopilotStudio.Copilots.Invoke
app role id: 38c13204-7d79-4d83-bdbb-b770e28400df
```

## Alternate route checks

### Dataverse `PvaGetDirectLineEndpoint` is not enough for integrated-auth bots

Dataverse may expose a bound action that returns an official DirectLine token endpoint:

```http
POST /api/data/v9.2/bots(<botId>)/Microsoft.Dynamics.CRM.PvaGetDirectLineEndpoint
```

For an integrated-auth/M365 bot this can succeed, and the returned endpoint can mint a DirectLine token. However, sending `startConversation` or a message over DirectLine still fails at runtime with:

```text
IntegratedAuthenticationNotSupportedInChannel
```

This proves Dataverse can reach channel/token metadata, but DirectLine cannot execute the integrated-auth bot. Do not treat a successful DirectLine token as a successful chat path.

The unbound Dataverse action `PvaStartConversation` exists, but metadata only exposes an opaque `Request: mscrm.crmbaseentity`. Tested minimal `bot` payloads return backend 404/shape errors, not a usable chat response. It is not a practical bypass for missing `CopilotStudio.Copilots.Invoke`.

### Evaluation API is also permission-gated

The PPAPI evaluation endpoints can fail with the same class of delegated-permission error. Example missing scopes:

```text
CopilotStudio.MakerOperations.Read
All.All.ReadWrite
```

So evaluation REST is not a guaranteed bypass for a user/app that lacks Copilot Studio delegated permissions.

## Repair paths

### Preferred: tenant app registration

Requires Entra permission to create/update app registrations and usually admin consent.

Create or use an app registration with:

- Platform: public client/native
- Redirect URI: `http://localhost`
- API permissions: Power Platform API
- Delegated permission: `CopilotStudio.Copilots.Invoke`
- Admin consent granted if tenant policy requires it

Then run:

```bash
node "D:/my agents copilot studio/pipeline/scripts/chat-with-agent.bundle.js" "hello" \
  --agent-dir "<agent workspace>" \
  --client-id "<that app registration client id>"
```

If `az ad app create` fails with `Insufficient privileges to complete the operation`, the current user cannot fix this directly. Escalate to Entra admin rather than looping auth.

### Do not silently weaken live bot auth

Changing an integrated-auth live bot to no-auth/DirectLine-compatible mode can be a valid temporary test tactic, but it changes live security posture. Only do this after explicit user approval and record a rollback plan before changing anything.

## Messaging to user

Be direct:

- "The bot is published/active and detect-only works."
- "Actual chat invoke is blocked by Entra/Power Platform delegated permissions."
- "This account can patch/publish Dataverse records but cannot invoke integrated-auth chat through the API."
- "Fix requires an Entra admin to grant/create an app with `CopilotStudio.Copilots.Invoke`, or explicit approval to temporarily change auth for testing."
