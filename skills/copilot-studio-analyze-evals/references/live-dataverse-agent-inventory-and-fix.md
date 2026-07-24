# Live Dataverse Agent Inventory & Fix Workflow

## Problem
An agent exists in `pac copilot list` (Published/Active) but has NO local workspace on disk. No `agent.mcs.yml`, no `topics/`, no `.mcs/conn.json`. You need to assess and fix it live.

## The Core Technique

Use **Python + urllib** (NOT `az rest` from bash) for Dataverse queries. `az rest` breaks on `$select` in bash because the `$` gets shell-interpreted. Python avoids this entirely:

```python
import subprocess, json, os, urllib.request, urllib.parse

# Step 1: Get Dataverse token via az.cmd
AZ = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
AZP = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'
env = dict(os.environ)
env['PATH'] = AZP + ';' + env.get('PATH', '')

r = subprocess.run([AZ, 'account', 'get-access-token',
    '--resource', 'https://orgbd048f00.crm.dynamics.com/'],
    capture_output=True, text=True, env=env)
token = json.loads(r.stdout)['accessToken']
h = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

BASE = 'https://orgbd048f00.crm.dynamics.com/api/data/v9.2'
BOT = '<bot-guid>'

# Step 2: Query botcomponents with URL-encoded $filter
params = urllib.parse.urlencode({
    '$filter': f"_parentbotid_value eq '{BOT}'",
    '$select': 'name,componenttype,statecode,botcomponentid'
})
req = urllib.request.Request(f'{BASE}/botcomponents?{params}', headers=h)
with urllib.request.urlopen(req, timeout=30) as resp:
    comps = json.loads(resp.read())
```

## Full Inventory Workflow

### 1. Get Bot Record (authentication mode, publish state)
```python
req = urllib.request.Request(f'{BASE}/bots({BOT})?$select=name,statecode,statuscode,authenticationmode,publishedon,synchronizationstatus', headers=h)
bot = json.loads(urllib.request.urlopen(req).read())
print(bot['authenticationmode'])  # 0=None, 1=Manual, 2=Integrated
```

### 2. Get Component Inventory
```python
params = urllib.parse.urlencode({
    '$filter': f"_parentbotid_value eq '{BOT}'",
    '$select': 'name,componenttype,statecode,botcomponentid'
})
req = urllib.request.Request(f'{BASE}/botcomponents?{params}', headers=h)
with urllib.request.urlopen(req, timeout=30) as resp:
    comps = json.loads(resp.read())

from collections import Counter
types = Counter(c.get('componenttype') for c in comps['value'])
# 9=topic, 12=answer, 14/16=knowledge, 15=instructions, 19=eval/test cases
```

### 3. Structural Topic Scan
For each type-9 topic, fetch its data and check structural flags:
```python
topics = [c for c in comps['value'] if c.get('componenttype') == 9]
for t in topics:
    req = urllib.request.Request(f'{BASE}/botcomponents({t["botcomponentid"]})?$select=name,data', headers=h)
    with urllib.request.urlopen(req, timeout=15) as resp:
        topic = json.loads(resp.read())
    d = topic.get('data', '')
    flags = {
        'END': 'EndDialog' in d,
        'CLR': 'clearTopicQueue' in d,
        'SASC': 'SearchAndSummarizeContent' in d,
        'Q': 'kind: Question' in d,
        'BD': 'BeginDialog' in d,
        'ManualAuth': 'ManualAuthenticationInput' in d,
    }
    print(f"  {t['name'][:50]:50s} | {flags}")
```

### 4. Check Publish Diagnostics
```python
ss = json.loads(bot.get('synchronizationstatus', '{}'))
lop = ss.get('lastFinishedPublishOperation', {})
print(f"Status: {lop.get('status')}")
for d in lop.get('diagnosticDetails', []):
    err = d.get('diagnosticList', [{}])[0]
    print(f"  Comp {d['componentId'][:50]}: {err.get('errorCode','?')}")
```

### 5. Apply Fix (PATCH topic data)
```python
new_data = r"""kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  ...
"""
body = json.dumps({'data': new_data}).encode()
req = urllib.request.Request(f'{BASE}/botcomponents({componentId})',
    data=body, headers={'Authorization': f'Bearer {token}',
    'Accept': 'application/json', 'Content-Type': 'application/json'},
    method='PATCH')
with urllib.request.urlopen(req, timeout=15) as resp:
    assert resp.status == 204  # success
```

### 6. Publish
```bash
pac copilot publish --bot <bot-id> --environment "https://orgbd048f00.crm.dynamics.com"
```

### 7. Verify Publish
Check `publishedon` via Dataverse (not pac CLI, which caches failures):
```python
req = urllib.request.Request(f'{BASE}/bots({BOT})?$select=name,publishedon', headers=h)
bot = json.loads(urllib.request.urlopen(req).read())
print(f"PublishedOn: {bot['publishedon']}")
```

## Critical Pre-Fix: ManualAuthenticationInput Scan

Before flipping `authenticationmode` to `0` (None), scan ALL type-9 topics for `ManualAuthenticationInput` nodes. If any exist, publish will fail:

```python
for t in topics:
    req = urllib.request.Request(f'{BASE}/botcomponents({t["botcomponentid"]})?$select=data', headers=h)
    with urllib.request.urlopen(req, timeout=15) as resp:
        d = json.loads(resp.read()).get('data', '')
    if 'ManualAuthenticationInput' in d:
        print(f"BLOCKER: {t['name']} — cannot flip auth to None")
```

**Verified 2026-07-15:** Flipping auth to None caused `ManualAuthenticationInputNotEnabled` on Clinical Analysis and Multi-Discipline Summary. Reverted to `authenticationmode: 2` (Integrated) with Sign-In topic deactivated (statecode=1) — published clean.

## Case Study: Case History Reviewing Agent (f19e1c40, 2026-07-15)

**Situation:** Agent existed in `pac copilot list` (Published/Active, 17 topics, 18 KBs) but NO local workspace. Baseline SR eval = 31% (28/89).

**Structural scan findings:**
- Fallback: NO SASC — just "I'm sorry" + redirect to OnError. **Every unmatched query guaranteed fails.**
- Conversational boosting: SASC runs but answer never shown — no SendActivity before EndDialog.
- Greeting + ConversationStart: EndDialog but no clearTopicQueue.
- Sign-in: Deactivated (statecode=1), but authmode=2 still causes minor gate.

**Fixes applied (all Dataverse PATCH + publish):**
1. Fallback: replaced apology with SASC + SendActivity + EndDialog(clearTopicQueue:true)
2. Conversational boosting: inserted SendActivity(=Topic.Answer) before EndDialog
3. Greeting + ConversationStart: added `clearTopicQueue: true`
4. Auth: attempted None → reverted to Integrated after ManualAuthenticationInputNotEnabled
5. Publish: Succeeded, eval started same day

## Pitfalls

### $filter requires URL encoding
The f-string `f"{BASE}/botcomponents?$filter=..."` with GUIDs raises `http.client.InvalidURL` in Python's `urllib`. Always use `urllib.parse.urlencode`:
```python
params = urllib.parse.urlencode({
    '$filter': f"_parentbotid_value eq '{BOT}'",
    '$select': 'name,componenttype,statecode'
})
```

### Stale pac CLI publish cache
`pac copilot publish` caches FAILED status permanently. The same error timestamp appears even after fixing the cause. Always verify via Dataverse `publishedon` field.

## Validated 2026-07-15
Used to inventory and fix Case History Reviewing Agent (f19e1c40, Therapy AI Dev). All components queried and PATCHed live.
