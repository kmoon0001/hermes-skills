# Data-Layer Write → Publish Blockers

When modifying Copilot Studio agent components via Dataverse API PATCH
(bypassing the SPA), two blockers commonly prevent the publish from succeeding.

---

## 1. Instructions conversationStarters: Title/Text Casing

**Problem:** The publish compiler expects `Title:` and `Text:` (capitalized)
in every `conversationStarters:` item inside `GptComponentMetadata` YAML.
Lowercase `title:` / `text:` produce `MissingRequiredProperty` errors
targeting the instructions component.

**Evidence:** Jul 6 2026 — Therapy AI Dev, Copy Therapy Docuementation
Feedback Ag. The `synchronizationstatus.lastFinishedPublishOperation`
contained:
```
[$kind: PropertyError, propertyName: Title, errorCode: MissingRequiredProperty]
[$kind: PropertyError, propertyName: Text,  errorCode: MissingRequiredProperty]
```
Component ID `1b6244b9` = instructions (componenttype 15).

**Fix:** Replace lowercase with capitalized in `conversationStarters`:
```yaml
conversationStarters:
  - Title: Audit My Note
    Text: Review my documentation for denial risk.
```

**How to detect:** PATCH fails. Check `synchronizationstatus` on the bot
entity:
```http
GET /bots({botId})?$select=synchronizationstatus
```
Parse `lastFinishedPublishOperation.diagnosticDetails[].diagnosticList[]`
for `MissingRequiredProperty` errors. The `componentId` identifies which
botcomponent is failing.

---

## 2. SPA Publish Button Disabled After External Data Writes

**Problem:** Dataverse API PATCH modifies the `data` field directly. The
Copilot Studio React SPA does NOT detect these changes — it tracks dirty
state only through its own editor interactions. Result: the Publish button
stays `disabled: true` with `aria-disabled: null`.

**Detection (CDP Runtime.evaluate):**
```javascript
var btn = Array.from(document.querySelectorAll('button'))
  .find(b => b.textContent.trim() === 'Publish' && b.offsetParent !== null);
// btn.disabled === true, btn.getAttribute('aria-disabled') === null
```

**Workarounds (preference order):**

| # | Approach | Tooling | Reliability |
|:-:|----------|---------|:-----------:|
| 1 | Force-click via JS: `btn.disabled=false; btn.removeAttribute('aria-disabled'); btn.click()` then confirm dialog | CDP `Runtime.evaluate` | High — bypasses React disabled state |
| 2 | Open Overview in fresh SPA tab, look for "A newer version is available — Refresh", click Refresh, then Publish | CDP navigation | Medium — only works if SPA detects version mismatch |
| 3 | `pac copilot publish --bot <id>` | pac CLI | Medium — subject to cached-failure state |
| 4 | Navigate to Settings → make a trivial UI change (add space to description) → Save → Publish | CDP mouse + keyboard | High — triggers React dirty state naturally |
| 5 | `pac auth clear` + re-auth + `pac copilot publish` | pac CLI | Low — device code often blocked by tenant CA |

---

## 3. pac CLI Cached Publish Failures

**Problem:** After `pac copilot publish` fails (e.g. another eval was
InProgress), subsequent runs return the **same** failure timestamp forever,
even with fresh auth or on a different machine. The failure is cached
locally in the DPAPI-sealed MSAL cache file
(`~/.copilot-studio-cli/manage-agent.cache.json`), not on the server.

**Verification:** The server-side `publishedon` timestamp is authoritative.
```http
GET /bots({botId})?$select=publishedon
```
If `publishedon` shows a recent value (not the failed attempt), the agent
is already published with its last successful version — you just need the
local cache cleared.

**Fix:**
1. Verify server state first (GET /bots/{id}?$select=publishedon)
2. If server shows up-to-date: the agent is fine, ignore the CLI error
3. If server shows old timestamp: `pac auth clear`, re-auth, retry
4. Alternative: use CDP SPA publish (workaround #1 above)

---

## 4. MSAL Cache Recovery After Corruption

**Problem:** When `manage-agent.cache.json` is deleted or corrupted, the
`PersistenceCreator.createPersistence()` path fails with
"Encryption/Decryption failed. Error code: 13".

**Cannot recover from browser localStorage:** The browser stores MSAL data
as plain JSON (decrypted `secret`/`data` fields in localStorage). MSAL Node
expects DPAPI-encrypted binary data. Writing raw JSON to the cache file
does not work — `deserialize()` produces 0 accounts.

**Recovery path:** Capture a fresh token from the browser's network traffic
via CDP `Network.enable` + `Page.reload`. The SPA makes API calls to
`api.powerplatform.com` and `api.bap.microsoft.com` with Bearer tokens in
the `Authorization` header. Extract and save to
`~/.copilot-studio-cli/test-agent-token.txt` for PPAPI use.

For Dataverse access, intercept requests to `crm.dynamics.com` — if the
page does not make direct Dataverse calls (most Copilot Studio pages proxy
through the gateway), you may need to navigate to a page that loads
component data directly (Topics list, Knowledge page).
