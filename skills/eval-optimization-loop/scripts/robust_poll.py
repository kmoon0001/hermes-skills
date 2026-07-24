"""
Robust eval poller for long-running Copilot Studio evals.
Handles connection resets and token expiry gracefully.
Usage: python scripts/robust_poll.py <run-id>
"""
import json, urllib.request, os, time, sys

TOKEN = open(os.path.expanduser('~/.copilot-studio-cli/test-agent-token.txt')).read().strip()
ENV = 'a944fdf0-0d2e-e14d-8a73-0f5ffae23315'
BOT = 'ea52ad9c-8233-f111-88b3-6045bd09a824'
GW = f'https://powervamg.us-il106.gateway.prod.island.powerapps.com/api/botmanagement/v2/environments/{ENV}/bots/{BOT}'

def make_headers():
    tok = open(os.path.expanduser('~/.copilot-studio-cli/test-agent-token.txt')).read().strip()
    return {
        'Authorization': f'Bearer {tok}',
        'Accept': 'application/json',
        'X-CCI-ApplicationSource': 'Web',
        'X-CCI-BapEnvironmentId': ENV,
        'X-CCI-BotId': BOT,
        'X-CCI-CdsBotId': BOT,
        'X-CCI-TenantId': '03cc92c3-986c-4cf4-ae27-1478cf99d17f',
    }

RUN_ID = sys.argv[1] if len(sys.argv) > 1 else None
if not RUN_ID:
    print('Usage: python robust_poll.py <run-id>')
    sys.exit(1)

for i in range(120):
    time.sleep(30)
    try:
        H = make_headers()
        req = urllib.request.Request(f'{GW}/makerevaluations?$top=20', headers=H)
        runs = json.loads(urllib.request.urlopen(req, timeout=30).read())
        for r in runs:
            if r['id'] == RUN_ID:
                ag = r.get('aggregatedGraderResults') or []
                s = next((m['count'] for m in ag if m['name']=='totalSucceeded'), 0)
                f = next((m['count'] for m in ag if m['name']=='totalFailed'), 0)
                print(f'[{i*30}s] {r.get("state")} | S={s} F={f}')
                sys.stdout.flush()
                if r.get('state') in ('Completed', 'Failed', 'Cancelled'):
                    score = round(s/(s+f)*100) if (s+f) > 0 else 0
                    print(f'FINAL: Score = {score}% ({s}/{s+f})')
                    sys.exit(0)
                break
    except Exception as e:
        print(f'[{i*30}s] Connection issue: {e}')
        sys.stdout.flush()
        time.sleep(10)

print('TIMEOUT after 120 polls')
