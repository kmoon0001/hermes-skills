---
name: copilot-studio-live-sync-backup
description: Pull all topic YAMLs from a live Copilot Studio agent via Dataverse REST API and sync local files to match. Live UI = source of truth; local = backup.
tags: [copilot-studio, dataverse, backup, sync, live]
---

# Copilot Studio Live Sync Backup

Make local YAML topic files match the live Copilot Studio agent. The live UI is the source of truth; this script overwrites local with live data.

## Prerequisites

- `az` CLI authenticated to the target tenant
- Bot ID (GUID from Copilot Studio URL or pac copilot list)
- Environment org URL (e.g. `https://orgxxx.crm.dynamics.com`)
- Local workspace path with topic `.mcs.yml` files

## Script

Save the following as `sync_live_to_local.py` and run with `python`:

```python
#!/usr/bin/env python3
import subprocess, json, urllib.request, sys, os, re
from urllib.parse import quote

# CONFIGURE THESE
BOT_ID = 'YOUR_BOT_GUID'
BASE   = 'https://YOUR_ORG.crm.dynamics.com/api/data/v9.2'
LOCAL_DIR = r'D:\path\to\topics'

# Auth — DO NOT call az via subprocess/powershell.exe. Under git-bash +
# the WindowsApps Python 3.13 build, `az` is a shell wrapper and subprocess
# cannot launch it (FileNotFoundError). Get the token in bash, then pass it:
#   TOKEN=$(az account get-access-token --resource '<org_url>' --query accessToken -o tsv)
#   python sync_live_to_local.py "$TOKEN"
import sys
token = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DATAVERSE_TOKEN', '')
if not token:
    sys.exit("Pass the az token as argv[1] (or set DATAVERSE_TOKEN). "
             "Get it: az account get-access-token --resource '<org_url>' --query accessToken -o tsv")

headers = {
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json',
    'OData-MaxVersion': '4.0',
}

# Fetch all botcomponents (componenttype=9 = topic)
filt = f"_parentbotid_value eq '{BOT_ID}' and componenttype eq 9"
url = f"{BASE}/botcomponents?$filter={quote(filt)}&$top=100"
req = urllib.request.Request(url, headers=headers)
data = json.loads(urllib.request.urlopen(req, timeout=60).read())
components = data['value']
print(f"Fetched {len(components)} live components")

def name_to_filename(name):
    import re
    fn = name.strip()
    fn = fn.replace('/', ' or ')
    fn = re.sub(r"[()'\"]", '', fn)
    fn = re.sub(r'\s+', '_', fn)
    fn = re.sub(r'_+', '_', fn).strip('_')
    return fn + '.mcs.yml'

os.makedirs(LOCAL_DIR, exist_ok=True)
written = set()
for c in components:
    name = c.get('name', 'Unknown')
    data_field = c.get('data', '')
    if not data_field:
        continue
    filename = name_to_filename(name)
    fpath = os.path.join(LOCAL_DIR, filename)
    with open(fpath, 'w', newline='\n') as f:
        f.write(data_field)
    written.add(filename.lower())
    print(f"  WRITE {filename}")

# Remove stale files
removed = []
for fname in os.listdir(LOCAL_DIR):
    if not fname.endswith('.mcs.yml'):
        continue
    if fname.lower() == 'agent.mcs.yml' or fname.startswith('.'):
        continue
    if fname.lower() not in written:
        os.remove(os.path.join(LOCAL_DIR, fname))
        removed.append(fname)
        print(f"  REMOVE {fname} (stale)")

print(f"\nWritten: {len(written)}, Removed: {len(removed)}")
```

## Clean Re-Clone (stale local -> delete + re-pull)
When the local workspace has drifted from live (e.g. the live agent was restructured and local
topic filenames no longer match), a plain sync can leave stale files or miss renamed
topics. Do a clean re-clone instead:
1. `rm -rf` the agent's local directory — it is only a backup mirror; live UI is the source of truth.
2. Recreate the dirs: `<Agent>/topics`, `<Agent>/scripts`.
3. Re-run the sync, pulling BOTH `componenttype=9` (topics) AND `componenttype=15`
   (Custom GPT instructions -> save as `agent.instructions.mcs.yml`). The base sync script
   skips `ct=15`, so add a fetch for it or the instructions clone is incomplete.
4. (Optional) pull bot metadata from `bots(<botId>)?$select=botid,name` -> `agent.metadata.json`.
Never push local -> live. Local is a read-only backup; all edits go to live via Dataverse
PATCH and re-sync afterward.

## Also Sync GPT Instructions

Per Microsoft Learn, agent GPT instructions are stored in `botcomponents` with `componenttype=15` (Custom GPT). To extract:

```python
filt = f"_parentbotid_value eq '{BOT_ID}' and componenttype eq 15"
url = f"{BASE}/botcomponents?$filter={quote(filt)}&$select=botcomponentid,name,data"
```

Parse the `data` field YAML — extract the `instructions:` block (indented under `instructions: |-`).

## PPAPI Eval Token (for draft evals without publishing)
After syncing local from live, run evals on the DRAFT (no publish needed). CRITICAL: the direct host `https://api.powerplatform.com/copilotstudio/.../api/makerevaluation` REJECTS all tokens in this tenant (401 InvalidAudience). Use the **Gateway** instead: `https://powervamg.us-il107.gateway.prod.island.powerapps.com/api/botmanagement/v2` with X-CCI routing headers. Mint the token via MSAL cache (`api://96ff4394-9197-43aa-b393-6a41652e21f8/.default` scope) — see `copilot-studio-run-eval` skill for the full Gateway + harness recipe (`scripts/eval_harness.py`).

## Known Pitfalls

- The `bots` entity's instruction fields (`overwriteinstructions`, `instructionstext`) may require different query syntax — test with `$select=botid,name&$top=5` first
- The Copilot Studio URL bot GUID IS the Dataverse bot ID for this environment — no translation needed
- **Auth**: never call `az` through `subprocess`/`powershell.exe` — it fails with `FileNotFoundError` on git-bash + WindowsApps Python (az is a shell wrapper, not a direct binary). Fetch the token in bash and pass it as `argv[1]` or the `DATAVERSE_TOKEN` env var. A known-good, re-runnable version lives in `references/sync_live_to_local_gitbash.py` — copy it and set `BOT_ID`/`BASE` at the top.
- **Snapshot BEFORE sync**: if the live agent was restructured since the local copy was last touched, the "remove stale files" step can delete a LARGE number of local files (e.g. 33 removed when Pacific Coast Case Historian moved to acute-record-extraction topics + an intent router + connected sub-agents). `git commit` or `git stash` the local tree FIRST so you keep history; `git status` only AFTER is too late to recover.
- **Connected sub-agents**: they surface as their own `botcomponents` (e.g. `SNF_AI_Dashboard_V2`, `TheraDoc_Workbench`) and get written as topics — do NOT treat them as stale and delete them.
- **`botcomponent.data` is RAW YAML, not JSON** — `json.loads()` on it throws `Expecting value: line 1 column 1 (char 0)`. Local `.mcs.yml` files written straight from `data` ARE the faithful live content (any defect you see locally is the real live defect, not a sync artifact). To inspect a topic's structure, parse with `yaml.safe_load(data)` or match strings with regex.
- **TOPICS are `componenttype eq 9`** (NOT 6). `6` returns only 2 components and misses every topic. Use `_parentbotid_value eq '<BOT_GUID>' and componenttype eq 9`.
- **OData `$select` rejects `displayname`** for `botcomponents` (400 Bad Request). Use `name` instead. Also ALWAYS `urllib.parse.urlencode` the whole query string (`$filter`, `$select`, `$top`) — a bare f-string like `?$filter=... and _parentbotid_value eq '{GUID}'` throws `InvalidURL: URL can't contain control characters` (the space). `$top` alone works; pair it with `$filter` + `$select=data` for reliable pulls.
- **`subprocess` cannot launch `az`** even in normal terminal python on this host: `subprocess.check_output(['az',...])` → `FileNotFoundError: The system cannot find the file specified` (az is a shim, not a direct binary). Get the token in **bash** and pass it into python via `python3 - "$TOKEN" <<'PY' ... PY`. Same trap for any `az`/`pac` subprocess call.
- **Verify pac auth first** with `pac auth list` (lists active env + user). Note: `pac version` is NOT a valid command — it errors out; use `pac auth list` or `pac copilot list` to confirm you're on the right environment.
- Commit the backup state to git for traceability after a verified sync.
