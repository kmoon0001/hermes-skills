# Integrated-auth Copilot Studio chat workaround decision tree

Use when a Copilot Studio agent is published/active, detect-only works, but API chat/eval invocation fails with delegated-permission errors such as `InsufficientDelegatedPermissions` or DirectLine returns `IntegratedAuthenticationNotSupportedInChannel`.

## Key distinction

Dataverse/PAC permissions are not equivalent to Copilot Studio chat invocation permissions.

A user/app can often:
- patch topic data in Dataverse,
- publish the bot,
- list the bot with PAC,
- call Dataverse actions such as `PvaGetDirectLineEndpoint`,

while still being unable to:
- start an integrated-auth Copilot Studio SDK conversation,
- run PPAPI evaluation endpoints,
- invoke the bot through DirectLine.

## Fast probes and what they mean

### 1. Detect-only

```bash
node scripts/chat-with-agent.bundle.js --detect-only --agent-dir "<agent-dir>"
```

If output says:

```json
{"mode":"m365","authenticationmode":2}
```

then the bot is integrated-auth/M365 mode. Continue with the decision tree below; do not assume DirectLine will work.

### 2. Authenticated Copilot Studio conversation endpoint

Raw endpoint shape:

```text
https://<env-guid-derived>.environment.api.powerplatform.com/copilotstudio/dataverse-backed/authenticated/bots/<schema>/conversations?api-version=2022-03-01-preview
```

If it returns:

```text
403 InsufficientDelegatedPermissions
missing [CopilotStudio.Copilots.Invoke, All.All.ReadWrite]
```

then the current app/user cannot invoke integrated-auth chat through the API. Repeating device codes or using Dataverse tokens will not fix it.

### 3. PPAPI evaluation endpoints

If evaluation REST endpoints return:

```text
403 InsufficientDelegatedPermissions
missing [CopilotStudio.MakerOperations.Read, All.All.ReadWrite]
```

then evaluation API is also gated by Copilot Studio delegated permissions. It is not a bypass for chat-invoke permissions.

### 4. Dataverse `PvaGetDirectLineEndpoint`

Dataverse can return a token endpoint:

```http
POST /api/data/v9.2/bots(<botId>)/Microsoft.Dynamics.CRM.PvaGetDirectLineEndpoint
```

This can succeed even for integrated-auth bots. If a DirectLine conversation then returns:

```text
IntegratedAuthenticationNotSupportedInChannel
```

that is expected: DirectLine token acquisition worked, but runtime execution is blocked by the bot's integrated-auth mode.

## Workaround hierarchy

### A. Preferred no-security-change workaround: Copilot Studio UI/evaluation/test pane

Use the user's normal browser/Copilot Studio session and drive the UI. This can work when raw API invocation is blocked because Microsoft's UI handles its own auth/session.

Practical checks:
- Look for persistent browser auth exports such as `C:\Users\kevin\.hermes-browser-session\auth.json`.
- If stale, have the user sign in in the normal browser/Copilot Studio UI, then save/export fresh browser state if the workflow supports it.
- Use the Evaluation UI/test pane workflow rather than `chat-with-agent.bundle.js` when API scopes are missing.

### B. Temporary auth/channel flip for smoke testing

Only after explicit user approval, temporarily change the bot from integrated-auth/always-auth to a DirectLine-testable/no-auth mode, publish, run DirectLine smoke test, then revert and publish again.

This is fast but changes live bot security. Do not do it silently.

Rollback requirements before changing:
- back up current `settings.mcs.yml`/live auth fields,
- record current `authenticationMode`, `authenticationTrigger`, channels, access policy,
- publish after both the test flip and the revert,
- verify final state is back to integrated auth.

### C. Proper long-term fix: Entra/admin app permissions

Ask an Entra admin to create or approve an app registration with:
- public/native client platform,
- redirect URI `http://localhost`,
- Power Platform API delegated scope `CopilotStudio.Copilots.Invoke`,
- admin consent if required by tenant policy.

For evaluation REST, the app/user may also need maker-operation scopes such as `CopilotStudio.MakerOperations.Read` and broad tenant policy may report `All.All.ReadWrite`.

## Stop conditions

Stop generating device codes when the user says they do not have access or when raw endpoint probes show `InsufficientDelegatedPermissions`. At that point the next useful step is one of: UI session workaround, explicit temporary auth flip, or admin permission grant.
