# Pacific Coast QM Coach V2 — new-experience audit + fix pass (2026-07-17)

**Bot:** `ea52ad9c-8233-f111-88b3-6045bd09a824` (Therapy AI Dev / orgbd048f00)  
**Type:** New-experience (Topic V2, Custom GPT ct=15, Knowledge Source ct=16)  
**Publish:** Succeeded 2026-07-17T09:04:47Z (02:04 AM PT)

## Discovery recipe (live-only)

1. `pac auth` → Therapy AI Agents Dev.
2. Inventory: FetchXML `parentbotid eq <botId>` via `pac org fetch` works for names/types, but output is a **text table**, not JSON.
3. For full YAML/data: Dataverse Web API with:
   - Filter: `_parentbotid_value eq <botId>` (NOT `parentbotid eq` — OData type error: bot vs Guid).
   - Select: `botcomponentid,name,componenttype,schemaname,statecode,data,content,category`
4. Type map observed: 9=Topic, 14=Bot File, 15=Instructions, 16=KB, 18=Settings, 19=Eval cases, 11=Entity, 12=Variable.

## Authoritative field

New-exp topics often have **both** `data` and `content`:
- `data` = generative/SASC pipeline (authoritative for live behavior).
- `content` = older hardcoded SendActivity tree (can diverge).
Audit and PATCH **`data` only** unless UI still mirrors content.

## False positives to suppress

| Check | When NOT a defect |
|-------|-------------------|
| Missing `kind: EndDialog` | System topics (OnConversationStart, OnUnknownIntent, OnError, Greeting with CancelAllDialogs, etc.) |
| Empty KB `description` via JSON grep | Descriptions are YAML `description:` — most KBs had them; only incomplete ones failed |
| Agent "in good shape" | Can still have: corrupted instructions, format bans, apology Fallback, missing FullResponse |

## P0 package that applied cleanly (all 204 + re-GET)

1. **Instructions rewrite** — remove mid-word splice (`analy## ROLE`) + duplicated `##` sections; identity Pacific Coast not SimpleLTC; conditional format; EVALUATION CONTEXT; no hard "no markdown / under N sentences".
2. **Fallback rewrite** — SASC FullResponse + capability list + EndDialog; kill "I'm not sure how to help".
3. **SASC sextet** — add `responseCaptureType: FullResponse`, `allowLatencyMessage: false`, `variable: Topic.Answer`, `SendActivity activity: =Topic.Answer` before EndDialog.
4. **Conversation Start** — welcome naming agent + EndDialog(clearTopicQueue:true) after custom SendActivity.
5. **KB descriptions** — Chapter 15 + AAPACN only needed displayName/description/isOfficial (others already good).
6. **Name cascade** — On Error / Feedback / Content Mod still said SimpleLTC or TheraDoc.
7. **Dup Bot Files** — disable no-ext twin when `.md`/`.pdf`/`.docx` exists (`statecode=1`, `statuscode=2`).
8. **Broken cross-agent flow** — `InvokeFlowAction` with `action: snf_ai_dashboard.action.CrossAgentAuditLog` not present in env; remove call so On Error still completes.

## Publish verification

`pac copilot publish` may print a **stale** "Succeeded [old date]". Always read:

```
GET /bots({id})?$select=publishedon,synchronizationstatus
```

Require `lastFinishedPublishOperation.status == "Succeeded"` and today's `publishedon`.

## Artifacts (repo)

- `QMCOACH_AUDIT_REPORT.md`
- `QMCOACH_FIX_PASS_2026-07-17.md`
- `scripts/fix_qmcoach_v2.py`
- Backups: `backups/qmcoach_v2_20260717_020341/`
