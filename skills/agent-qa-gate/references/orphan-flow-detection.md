# Orphan Flow Detection — Pre-Publish Gate (G14/G15)

## Why This Matters
Orphaned Power Automate flow references are the #1 cause of silent publish failures.
A topic references a flow that no longer exists → publish fails with unhelpful diagnostics.

## Detection Script
Run this before every `pac copilot publish`:

```python
import json, urllib.request, os, urllib.parse

TOKEN = open('az_token.txt').read().strip()
BASE = 'https://<org>.crm.dynamics.com/api/data/v9.2'

# 1. Get all active topics for this bot
filter_str = "_parentbotid_value eq {botId} and statecode eq 0"
url = f'{BASE}/botcomponents?$filter={urllib.parse.quote(filter_str)}&$select=botcomponentid,data,name'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/json'})
with urllib.request.urlopen(req, timeout=15) as r:
    topics = json.loads(r.read()).get('value', [])

# 2. Search for flow references in each topic
import re
flow_ids = set()
for t in topics:
    data = t.get('data', '')
    # Find flowId patterns
    for m in re.finditer(r'flowId:\s*"?([a-f0-9\-]{36})"?', data):
        flow_ids.add(m.group(1))
    # Find InvokeFlowAction with action: field (WRONG - should be flowId:)
    if re.search(r'kind:\s*InvokeFlowAction', data) and re.search(r'action:', data):
        print(f"WARNING: {t['name']} uses InvokeFlowAction with action: field. Use InvokeConnectedAction.")

# 3. Verify each flow exists
for fid in flow_ids:
    url2 = f'{BASE}/workflows({fid})?$select=workflowid,name,statecode,ismanaged'
    try:
        req2 = urllib.request.Request(url2, headers={'Authorization': f'Bearer {TOKEN}', 'Accept': 'application/json'})
        with urllib.request.urlopen(req2, timeout=10) as r2:
            wf = json.loads(r2.read())
            if wf.get('statecode') != 0:
                print(f"BLOCK: Flow {wf.get('name','?')} ({fid[:12]}) is not active (state={wf.get('statecode')})")
            if wf.get('ismanaged'):
                print(f"MANAGED FLOW: {wf.get('name','?')} ({fid[:12]}) — can't delete via API. Remove from Copilot Studio UI → Flows tab.")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"BLOCK: Flow {fid[:12]} does not exist in workflow table!")
        else:
            print(f"ERROR checking flow {fid[:12]}: {e.code}")
```

## Common Orphan Flow Sources
- **CrossAgentAuditLog** — auto-created when connecting agents. Frequently orphaned.
- **Compliance Audit Flow** — managed solution component. Can't delete via API.
- Any flow whose `ismanaged=True` and `statecode=0` (Draft) still blocks publish.

## Key Insight: Output Binding Errors are Flow-Side Only
When publish diagnostics say "Output binding 'fieldName' is not found, refresh this flow":
- **Do NOT touch topic outputType.properties** — adding them has ZERO effect (proven 2026-07-16: adding 52 properties to Master Patient Context changed nothing)
- The bindings are stored in the Power Automate flow's registered input schema, not in topic YAML
- ONLY fix: delete or update the flow itself
- See `copilot-studio-common-reference` → references/managed-flow-publish-blocker.md for full workflow

## Fix
- For unmanaged flows: Delete via workflow table DELETE
- For managed flows: Remove from Copilot Studio UI → Flows tab → ... → Remove
- ALWAYS re-run this check after removing, before publishing
