---
name: copilot-studio-live-patch
description: Live-patch a Copilot Studio topic/instructions component via Dataverse REST API (botcomponents PATCH), publish, and verify — including the SASC source-of-truth binding fix. Use when Kevin wants a surgical live change to a topic or agent instructions without the VS Code LSP path.
tags: [copilot-studio, dataverse, patch, publish, sasc, knowledge-sources, verify]
---

> **For standard PATCH workflows and topic YAML patterns, load `copilot-studio-agent-builder` first (Phase 3/4 + templates).** This skill provides the full Python implementation with CRLF handling and URL encoding workarounds.

# Copilot Studio Live Patch (Dataverse REST)

Surgical live edit of a Copilot Studio agent component (topic YAML or instructions) via the
Dataverse Web API, then publish + verify. This is the path used for all live fixes to the
Therapy AI Dev agents (orgbd048f00). It avoids the VS Code extension and works from terminal/Python.

## When to use
- Add/fix a node in a topic (e.g. bind SASC to knowledge sources, add instructions).
- Patch agent instructions (componenttype 15) — note: `instructions` lives on the botcomponent,
  NOT on the `bots` record (querying `bots?$select=instructions` returns HTTP 400).
- Any change where "Live UI = source of truth" and you must edit live, not local.

## CRITICAL GOTCHAS (learned the hard way)
1. Line endings: Dataverse returns `data` with `\\r\\n`. `read_text()` in Python STRIPS `\\r`,
   so an anchor found in the file may not match the live bytes. Always re-pull via urllib and
   operate on the RAW response string (which keeps `\\r\\n`) before building the patch payload.
2. Anchor matching: inspect the actual `repr()` of the slice around your target BEFORE asserting.
   Indentation/blank-line counts differ between topics. Use `d.find('substring')` + `repr()` to
   confirm, then build the replacement from the confirmed anchor.
3. **Python 3.13 `_validate_path` URL encoding:** Python 3.13's `urllib.request` has a strict
   `_validate_path` that raises `InvalidURL` on unquoted spaces or control characters in the URL
   path. When building OData filter URLs with Python 3.13, ALWAYS `urllib.parse.quote()` the
   path portion after `urlparse()` and set `req.selector` and `req.full_url` to the encoded URL.
   The cleanest workaround: use `"az rest"` for queries (it handles encoding), and only use
   Python `urllib` for PATCH operations where the URL has no query string.
4. CRLF for PATCH: send payload with normalized CRLF
   (`d2.replace('\\r\\n','\\n').replace('\\r','\\n').replace('\\n','\\r\\n')`) to avoid YAML parse drift.
5. Bot GUID: the FULL botid is needed for publish. The memory note's shortened
   prefix is STALE — always pull the live botcomponent schemaname to confirm the real bot.
6. **Stale audit state when resuming interrupted work** — if continuing from a prior
   session's audit ("yes fix them all"), always re-pull live data before PATCHing.
   Another session, agent, or manual edit may have already applied the fixes.
   An audit report from hours ago is a snapshot, not current truth.
7. `bots` select error: never `$select=instructions` on `bots`. Instructions are on the
   `botcomponents` row (componenttype 15).
8. DNS quirk: `<org>.api.crm.dynamics.com` intermittently fails DNS. Use the generic
   `api.crm.dynamics.com` host for the Web API calls (it resolves reliably).
9. **`az` PATH on Windows:** `az` at the git-bash level is a shell script
   (`/c/Program Files/Microsoft SDKs/Azure/CLI2/wbin/az`), NOT an `.exe` on the system `PATH`.
   System Python's `subprocess.run(['az',...])` raises `FileNotFoundError`. **Fix:** use the
   full `.cmd` path: `AZ = r'C:\\Program Files\\Microsoft SDKs\\Azure\\CLI2\\wbin\\az.cmd'`, or
   write token from terminal `az ... > az_token.txt` and `open()` it in Python.
10. **Non-UTF-8 bytes in Dataverse responses:** Long text fields (e.g. `responseInstructions`)
    can contain byte `0x97` (end-of-guarded-area control char) breaking `json.loads()` with
    `UnicodeDecodeError`. **Fix:** `resp.read().decode('utf-8', errors='replace')` or save
    `az rest -o json > file.json` and read via `open('f.json', 'rb').read().decode('utf-8', errors='replace')`.
11. **Batch OData `contains` filter:** To find all components with an old name across types:
    `$filter=_parentbotid_value eq <bot> and (contains(name,'OldName1') or contains(name,'OldName2'))`.
    Returns instructions (ct=15), settings (ct=18), eval markers (ct=19), and bot files (ct=14)
    in one query. Iterate + PATCH each `name` field individually.

## Standard procedure (Python via urllib)
```python
import json, urllib.request, urllib.parse, subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta

AZ = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
ORG = 'orgbd048f00'
BASE = f'https://{ORG}.crm.dynamics.com/api/data/v9.2'   # or api.crm.dynamics.com if DNS fails
BOT = '<FULL-BOTID>'

# 1. token
tok = json.loads(subprocess.run([AZ,'account','get-access-token',
        '--resource', f'https://{ORG}.crm.dynamics.com','-o','json'],
        capture_output=True, text=True).stdout)['accessToken']
H = {'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json',
     'OData-MaxVersion': '4.0', 'OData-Version': '4.0', 'Accept': 'application/json'}

# 2. find component
flt = "contains(schemaname,'<TopicSchemaName>')"
url = f"{BASE}/botcomponents?$select=botcomponentid,name,schemaname,data&$filter={urllib.parse.quote(flt)}"
req = urllib.request.Request(url, headers=H)
with urllib.request.urlopen(req, timeout=90) as resp:
    v = json.loads(resp.read().decode()).get('value', [])
cid = v[0]['botcomponentid']
d = v[0]['data']                     # RAW, keeps \r\n
Path(r'C:\Users\kevin\Desktop\<topic>_before_patch.yaml').write_text(d)

# 3. inspect + patch (use repr to confirm anchors)
i = d.find('SearchAndSummarizeContent'); print(repr(d[i:i+500]))
# build d2 with string replace on confirmed \r\n anchors

# 4. PATCH
d2c = d2.replace('\r\n','\n').replace('\r','\n').replace('\n','\r\n')
req = urllib.request.Request(f"{BASE}/botcomponents({cid})",
        data=json.dumps({'data': d2c}).encode(), method='PATCH', headers=H)
with urllib.request.urlopen(req, timeout=120) as resp:
    print('PATCH', resp.status)     # expect 204

# 5. publish
r = subprocess.run(['pac','copilot','publish','--environment',
        f'https://{ORG}.crm.dynamics.com','--bot', BOT], capture_output=True, text=True)
print(r.stdout)

# 6. verify
req = urllib.request.Request(f"{BASE}/bots({BOT})?$select=publishedon,synchronizationstatus", headers=H)
with urllib.request.urlopen(req, timeout=60) as resp:
    b = json.loads(resp.read().decode())
j = json.loads(b['synchronizationstatus']) if isinstance(b.get('synchronizationstatus'),str) else b.get('synchronizationstatus')
print('status', (j.get('lastFinishedPublishOperation') or {}).get('status'))
PT = timezone(timedelta(hours=-7))
if b.get('publishedon'):
    print('Pacific', datetime.fromisoformat(b['publishedon'].replace('Z','+00:00')).astimezone(PT).strftime('%Y-%m-%d %I:%M %p %Z'))
```

## Knowledge Source Restriction Removal (inverse pattern)

When a SASC node uses `SearchSpecificFiles` or `SearchSpecificKnowledgeSources` (empty),\nit restricts KB search to only those named files/sources — everything else is blocked.

**CRITICAL — check BOTH topics, not just the main one:**\nThe same SearchSpecificFiles/SearchSpecificKnowledgeSources restriction can exist on the\nmain custom topic AND on the Conversational boosting (catch-all, `topic.Search`)\ntopic. The catch-all is priority -1 (OnUnknownIntent) and handles anything that doesn't\nmatch a specific topic trigger. If the catch-all is restricted, ALL non-trigger queries fail\nKB search — producing 0% eval scores even after fixing the main topic.

**Verification pattern (validated Doc Defense Agent, pccapackage, 2026-07-18):**\n1. Pull ALL componenttype=9 topics for the bot\n2. For EACH topic with a SASC node, check for SearchSpecificFiles / SearchSpecificKnowledgeSources / applyModelKnowledgeSetting: true\n3. Fix ALL of them, not just the main topic — the catch-all is the one that causes 0% scores\n4. Re-run evals after fixing both — 0% → measurable score (observed: 0% → pending after fix)\n\n**Detect:**\n`grep -E 'SearchSpecificFiles|SearchSpecificKnowledgeSources|applyModelKnowledgeSetting: true' topic_data.txt`\n\n**Fix — replace all three patterns:**\n```python\n# 1. Replace SearchSpecificFiles (with file list) → SearchAllFiles\n# Find the fileSearchDataSource block from 'fileSearchDataSource:' to the next 'knowledgeSources:'\n# Replace with:  fileSearchDataSource:\\n        searchFilesMode:\\n          kind: SearchAllFiles\n\n# 2. Replace SearchSpecificKnowledgeSources → SearchAllKnowledgeSources\ndata = data.replace('kind: SearchSpecificKnowledgeSources', 'kind: SearchAllKnowledgeSources')\n\n# 3. Remove applyModelKnowledgeSetting: true (leans on model memory, ignores KBs)\ndata = data.replace('\\r\\n      applyModelKnowledgeSetting: true\\r\\n', '\\r\\n')\n```\n\n**Why this matters:**\n- `SearchSpecificFiles` with a 14-file list blocks any new file added later\n- `SearchSpecificKnowledgeSources` with NO sources listed blocks ALL KB retrieval\n- `applyModelKnowledgeSetting: true` leans on model memory, ignoring KBs entirely\n- The grader penalizes groundedness=No when answers lack KB citations\n- **0% eval score is the signature symptom** — all cases fail because KB search is blocked\n- Verified: Doc Defense Agent (pccapackage, 2026-07-18) — fixing only the main topic left\n  the catch-all broken (0% persisted). Fixing the catch-all too was required.

## The SASC source-of-truth binding fix (most common patch)
A generative-answers / `SearchAndSummarizeContent` node with ONLY `applyModelKnowledgeSetting: true`
leans on MODEL MEMORY — it will NOT read uploaded docs or cite the agent KBs. To make the
configured knowledge sources the source of truth, inject these two blocks into the SASC node
(right after `responseCaptureType: FullResponse`):
```
      fileSearchDataSource:
        searchFilesMode:
          kind: SearchAllFiles
      knowledgeSources:
        kind: SearchAllKnowledgeSources
```
Then optionally upgrade `additionalInstructions` to name the sources as source of truth and require
citing the specific standard (e.g. "42 CFR 483.25 / F-tag 686", "Ch.15 §220.2", "Jimmo Settlement
Agreement"). MS Learn: a generative-answers node must have the knowledge sources incorporated at the
node level or it searches only agent-level KBs (and with model-knowledge on, may ignore them).

## Agent Rename Workflow

Renaming an agent (display name + all internal references) requires PATCHing multiple component
types. Do NOT just change `displayName` in instructions — references to the old name live in the
instructions body, Fallback, settings names, eval markers, and the `bots` table itself.

### Component types to update

| Component | What to PATCH | Detail |
|-----------|--------------|--------|
| Instructions (ct=15) | `data` field | `displayName:` + all self-references in instructions text |
| Instructions (ct=15) | `name` field | Component name visible in Dataverse |
| Fallback (ct=9) | `data` field | `description:` and `additionalInstructions:` may reference old name |
| Settings (ct=18) | `name` field | Both Feedback and Content Moderation components |
| Eval markers (ct=19) | `name` field | Test case names like `"Evaluate {OldName}"` |
| Bot files (ct=14) | `statecode: 1` | Disable duplicate uploads (not rename, but often done together) |
| Bots table | `name` field | The bot's name in the Copilot Studio interface |

### Batch rename pattern (Python)

```python
# 1. Find all components with old names in one query
flt = urllib.parse.quote(
    f"_parentbotid_value eq {BOT} and "
    f"(contains(name,'{OLD_NAME}') or contains(name,'{OTHER_OLD_NAME}'))"
)
url = f"{BASE}/botcomponents?$filter={flt}&$select=botcomponentid,name,componenttype"

# Fix Python 3.13 URL encoding
p = urllib.parse.urlparse(url)
ep = urllib.parse.quote(p.path, safe='/@:$&?=%,')
safe_url = urllib.parse.urlunparse(p._replace(path=ep))
req = urllib.request.Request(safe_url, headers=H)
req.selector = ep
req.full_url = safe_url

with urllib.request.urlopen(req, timeout=90) as resp:
    raw = resp.read().decode('utf-8', errors='replace')  # GOTCHA: non-UTF-8 bytes
    vals = json.loads(raw)['value']

# 2. PATCH each component's name field
for v in vals:
    old_name = v['name']
    new_name = old_name.replace(OLD_NAME, NEW_NAME)
    if new_name == old_name:
        continue  # content mention, not a name — skip
    payload = json.dumps({'name': new_name}).encode()
    req2 = urllib.request.Request(
        f"{BASE}/botcomponents({v['botcomponentid']})",
        data=payload, method='PATCH', headers=H
    )
    with urllib.request.urlopen(req2, timeout=60) as resp:
        assert resp.status == 204

# 3. PATCH the bots table name (optional — changes Copilot Studio display name)
req = urllib.request.Request(
    f"{BASE}/bots({BOT})",
    data=json.dumps({'name': NEW_NAME}).encode(),
    method='PATCH', headers=H
)
with urllib.request.urlopen(req, timeout=60) as resp:
    assert resp.status == 204
```

### Publish after rename
After all PATCHes, publish via PvaPublish or `pac copilot publish`. Verify the published
name via `GET /bots({id})?$select=name,publishedon,synchronizationstatus`. The `name`
field on the `bots` table is what shows in Copilot Studio UI.

### Pitfalls
- **Instructions text may have more references than displayName** — search for all occurrences
  of the old name string in the `data` field, not just `displayName:`. The role statement
  (`"You are X..."`) is the most common extra reference.
- **Fallback instructions** are separate from agent instructions. PATCH the Fallback
  topic's `data.additionalInstructions` independently.
- **Eval markers (ct=19)** with names like `"Evaluate {OldName}"` don't affect eval
  functionality — they're cosmetic in reports. Still worth updating for consistency.
- **Trigger question content** that mentions the old name as a product reference (e.g.
  "interpret our SimpleLTC export") should NOT be changed — that's the actual product
  name, not a self-reference.
- **TheraDoc/SimpleLTC/LegacyName** residue: check settings disclaimer text and Content
  Moderation response text, not just the displayName.

## Verify after publish
- Re-pull the component and assert changes stuck — a 204 does NOT guarantee the data was written.
  Use `GET /botcomponents({id})?$select=data` and `assert NEW_VALUE in data`.
- Shift+Reload the Copilot Studio tab (UI cache otherwise shows stale topic).
- Test in the Test pane: send a real prompt, confirm real response (not "Loading up..." hang).
- For SASC patches: upload a doc + ask a KB-grounded question — should cite the source.
- For rename: `GET /bots({id})?$select=name,publishedon,synchronizationstatus` — confirm name and that publishedon updated.

## Conversational boosting topic
Schema name is usually `<schema>.topic.Search` (e.g. `crbee_PacCoastDocumentationDefenseAgent.topic.Search` or `auto_agent_aaamq.topic.Search`).
It is the OnUnknownIntent catch-all (priority -1). Patch it the same way as any topic.

**Hollow handoff (before surgical flag-only patches):** If many custom leaves only `BeginDialog` into `topic.Search`, fixing Search alone is mandatory — leaves inherit its silence. Require Pattern L package: FullResponse + allowLatencyMessage:false + variable Topic.Answer + **SendActivity =Topic.Answer** + EndDialog. Never leave SASC→EndDialog without SendActivity (Report Prep V2 2026-07-17).

**Inactive flow check:** Before keeping any `flowId` on On Error / TaskDialog actions, `GET /workflows({id})` and require `statecode=0`. Inactive-while-wired is P0.

**New topic POST via Dataverse (validated Therapy Report Prep V2 2026-07-17):**

When creating a brand new topic (not patching an existing one), use POST on the
botcomponents collection. Key differences from PATCH:

- Do NOT include `If-Match` — POST rejects it with `0x80060888`
- Use `parentbotid@odata.bind: f'/bots({BOT_ID})'` not `_parentbotid_value`
- Include `"statecode": 0, "statuscode": 1`
- Response is 204 (empty body) — component ID is in `OData-EntityId` response header
- Verify with `$filter=schemaname eq '<name>'` AND confirm `_parentbotid_value`

**Publish CLI staleness:** `pac copilot publish` may print an old Succeeded timestamp. Always re-GET bot `publishedon` + `lastFinishedPublishOperation.status` and report **Pacific** time.

**Commit scope:** On multi-agent dirty repos, commit only this bot's audit/fix files before PATCHing (not full workspace). Validated QM Coach V2 full fix batch 2026-07-17 (all 204 + publish Succeeded).
