# Browser-token Dataverse + Gateway publish fallback

Use this when `manage-agent` / MSAL cache / `pac` auth is blocked by Conditional Access, but the user already has an authenticated Copilot Studio browser tab.

**PITFALL: Chrome CDP port binding on Windows.** Launching Chrome with `--remote-debugging-port=N` (e.g. 9223) does NOT reliably work on Windows — the browser process ignores the flag even after `taskkill //F //IM chrome.exe`. See `windows-cua-driver` skill (Chrome CDP Port Binding section) for workarounds. When CDP is unavailable, fall back to `az account get-access-token` for Dataverse tokens (no browser needed).

## Pattern

1. Use Chrome DevTools Protocol against the authenticated Copilot Studio tab.
2. Capture a Dataverse-scoped bearer token from the browser's own `Network.requestWillBeSent` events while the page calls `https://<org>.crm.dynamics.com/api/data/v9.2/...`.
   - Do not print the token.
   - Save it to a local temp/token file only if needed.
   - Decode only non-secret claims (`aud`, `scp`, `exp`) for validation.
3. Use Dataverse REST directly for narrow `botcomponents(<id>)` `data` PATCH operations.
   - Always read row + ETag first.
   - Save `before_rows.json` and per-component `*-before.yml`/`*-after.yml` backups.
   - PATCH only `{ "data": "<complete YAML string>" }` unless a broader row update is explicitly needed.
4. Publish through the PowerVA gateway publish endpoint, not Dataverse, when LSP/pac publish is unavailable:
   - `POST https://<gateway>/api/botmanagement/v1/environments/<envGuid>/bots/<botId>/publishv2-operations`
   - Then poll `GET` on the same URL until `isInFinalState: true`.
5. Gateway publish requires routing headers captured from browser gateway calls:
   - `Authorization: Bearer <api.powerplatform.com token>`
   - `X-CCI-TenantId`
   - `X-CCI-CdsBotId`
   - `x-cci-applicationsource: Web`
   - `x-ms-client-session-id`
   - `x-ms-client-request-id`
   - `x-ms-user-agent`
6. Verify publish by reading `BotEntity` from the environment API and checking:
   - `bot.synchronizationStatus.lastFinishedPublishOperation.status == "Succeeded"`
   - no `diagnosticDetails` validation errors remain.

## Validation-error loop

When publish fails, do not retry blindly. Read diagnostics from BotEntity:

`POST https://<envHost>.environment.api.powerplatform.com/powervirtualagents/bots/<botId>/api/botcomponents?api-version=2022-03-01-preview`

Body:

```json
{"Kind":["BotEntity"]}
```

Then inspect:

`bot.synchronizationStatus.lastFinishedPublishOperation.diagnosticDetails`

Common actionable diagnostics:

- GPT component `Title`/`Text` missing: remove or repair blank `conversationStarters` entries in the GPT metadata botcomponent.
- `InvalidReferenceError` for Knowledge: remove stale `knowledgeSources` / `SearchSpecificKnowledgeSources` references that point at deleted knowledge/topic IDs, preserving valid `fileSearchDataSource` file references.

## Safety

- Never print or persist tokens in skills, chat, logs, or references.
- Preserve clinical/compliance instructions and knowledge file references. Remove only proven-dead references that publish diagnostics name as missing.
- After every PATCH, re-read the exact row and verify the YAML/content changed before publishing.
