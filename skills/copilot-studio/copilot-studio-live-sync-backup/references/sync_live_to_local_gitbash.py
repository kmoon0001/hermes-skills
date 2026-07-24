#!/usr/bin/env python3
"""
sync_live_to_local_gitbash.py
Pull all Copilot Studio TOPIC components (componenttype=9) from a live
Dataverse environment and overwrite local .mcs.yml topic files to match.

Known-good replacement for the inline script in copilot-studio-live-sync-backup
SKILL.md, which used `subprocess -> powershell.exe -> az` and FAILS under
git-bash + WindowsApps Python 3.13 (az is a shell wrapper, not a direct binary,
so subprocess raises FileNotFoundError).

USAGE (git-bash):
  TOKEN=$(az account get-access-token --resource 'https://ORG.crm.dynamics.com' \
          --query accessToken -o tsv)
  python3 sync_live_to_local_gitbash.py "$TOKEN"

Set BOT_ID and BASE below. Run from the agent's repo root; topics land in ./topics.
Connected sub-agents surface as their own botcomponents (e.g. SNF_AI_Dashboard_V2)
and are written, NOT deleted as stale — leave them.
"""
import os, re, sys, json, urllib.request
from urllib.parse import quote

# ---- CONFIGURE THESE ----
BOT_ID = 'ad635500-cf47-f111-bec5-70a8a5b1c3a3'   # Pacific Coast Case Historian
BASE   = 'https://orgbd048f00.crm.dynamics.com/api/data/v9.2'
# LOCAL_DIR defaults to <cwd>/topics; override if needed.
LOCAL_DIR = os.path.normpath(os.path.join(os.getcwd(), 'topics'))
# -------------------------

token = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('DATAVERSE_TOKEN', '')
if not token:
    sys.exit("Pass the az token as argv[1] or set DATAVERSE_TOKEN env var.\n"
             "Get it: az account get-access-token --resource '%s' --query accessToken -o tsv" % BASE)

headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json',
           'OData-MaxVersion': '4.0'}

def fetch(ct):
    filt = f"_parentbotid_value eq '{BOT_ID}' and componenttype eq {ct}"
    url = f"{BASE}/botcomponents?$filter={quote(filt)}&$top=100"
    req = urllib.request.Request(url, headers=headers)
    return json.loads(urllib.request.urlopen(req, timeout=120).read())['value']

def nm(name):
    fn = name.strip().replace('/', ' or ')
    fn = re.sub(r"[()'\"]", '', fn)
    fn = re.sub(r'\s+', '_', fn)
    fn = re.sub(r'_+', '_', fn).strip('_')
    return fn + '.mcs.yml'

os.makedirs(LOCAL_DIR, exist_ok=True)
written = set()
for ct in (9, 15):           # 9=topic, 15=custom gpt (instructions)
    for c in fetch(ct):
        if ct == 15:
            continue          # instructions handled separately
        data = c.get('data', '')
        if not data:
            continue
        fn = nm(c.get('name', 'Unknown'))
        if fn.lower() == 'agent.mcs.yml':
            continue
        open(os.path.join(LOCAL_DIR, fn), 'w', newline='\n').write(data)
        written.add(fn.lower())
        print(f"  WRITE {fn}")

removed = []
for f in os.listdir(LOCAL_DIR):
    if not f.endswith('.mcs.yml') or f.lower() == 'agent.mcs.yml' or f.startswith('.'):
        continue
    if f.lower() not in written:
        os.remove(os.path.join(LOCAL_DIR, f))
        removed.append(f)
        print(f"  REMOVE {f} (stale)")

print(f"\nWritten: {len(written)}, Removed stale: {len(removed)}")
print(f"LOCAL_DIR = {LOCAL_DIR}")
