"""
Eval runner for Copilot Studio agents via the PowerVA Gateway API.
Supports: list, start, poll actions.

Usage:
  python scripts/eval_runner.py list                       # list recent runs
  python scripts/eval_runner.py start <testset-id> [name]  # start new eval
  python scripts/eval_runner.py poll <run-id>              # poll once

Environment config (edit ENV/BOT/GW for your org):
  ENV = Therapy AI Dev environment ID
  BOT = target agent GUID
  GW  = gateway host
"""
import json, urllib.request, os, sys

TOKEN = open(os.path.expanduser('~/.copilot-studio-cli/test-agent-token.txt')).read().strip()
ENV = 'a944fdf0-0d2e-e14d-8a73-0f5ffae23315'   # Therapy AI Dev
BOT = 'ea52ad9c-8233-f111-88b3-6045bd09a824'    # CHANGE ME
GW = f'https://powervamg.us-il106.gateway.prod.island.powerapps.com/api/botmanagement/v2/environments/{ENV}/bots/{BOT}'

H = {
    'Authorization': f'Bearer {TOKEN}',
    'Accept': 'application/json',
    'X-CCI-ApplicationSource': 'Web',
    'X-CCI-BapEnvironmentId': ENV,
    'X-CCI-BotId': BOT,
    'X-CCI-CdsBotId': BOT,
    'X-CCI-TenantId': '03cc92c3-986c-4cf4-ae27-1478cf99d17f',
}

action = sys.argv[1] if len(sys.argv) > 1 else 'list'

if action == 'list':
    req = urllib.request.Request(f'{GW}/makerevaluations?$top=10', headers=H)
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    print(f'Found {len(resp)} recent runs')
    for r in resp:
        ag = r.get('aggregatedGraderResults') or []
        s = next((m['count'] for m in ag if m['name']=='totalSucceeded'), 0)
        f = next((m['count'] for m in ag if m['name']=='totalFailed'), 0)
        name = r.get('clientRequestedEvaluationRunName') or r.get('testSetName','') or ''
        print(f"  {r['id'][:12]} | {r.get('state','?'):12s} | {s}/{s+f} | {name[:60]}")

elif action == 'start':
    test_id = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else f'Eval {test_id[:8]}'
    body = json.dumps({'testSetId': test_id, 'clientRequestedEvaluationRunName': name}).encode()
    req = urllib.request.Request(f'{GW}/makerevaluations', data=body, headers=H)
    req.add_header('Content-Type', 'application/json')
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    run_id = resp.get('runId') or resp.get('id', '?')
    print(f'Started: {run_id} | State: {resp.get("state")}')

elif action == 'poll':
    run_id = sys.argv[2]
    req = urllib.request.Request(f'{GW}/makerevaluations?$top=20', headers=H)
    runs = json.loads(urllib.request.urlopen(req, timeout=30).read())
    for r in runs:
        if r['id'] == run_id:
            ag = r.get('aggregatedGraderResults') or []
            s = next((m['count'] for m in ag if m['name']=='totalSucceeded'), 0)
            f = next((m['count'] for m in ag if m['name']=='totalFailed'), 0)
            e = next((m['count'] for m in ag if m['name']=='totalErrors'), 0)
            print(f'State: {r.get("state")} | S={s} F={f} E={e}')
            if r.get('state') == 'Completed':
                score = round(s/(s+f)*100) if (s+f) > 0 else 0
                print(f'Score: {score}% ({s}/{s+f})')
            break
