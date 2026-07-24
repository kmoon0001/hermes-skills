"""Robust eval poller with auto token refresh.
Usage: python3 poll_robust.py

Polls the Makerevaluations list endpoint every 60s.
Refreshes the eval PPAPI token on HTTP 403.
Reports score when run completes.

Edit the ENV/BOT/TENANT/RUN_PREFIX constants for your agent.
"""
import urllib.request, json, time, sys, subprocess

TOKEN_FILE = r'C:\Users\kevin\.copilot-studio-cli\test-agent-token.txt'
REFRESH_DIR = r'C:\Users\kevin\skills-for-copilot-studio\scripts'
GW = 'https://powervamg.us-il107.gateway.prod.island.powerapps.com/api/botmanagement/v2'
ENV = '<env-guid>'          # e.g. a944fdf0-0d2e-e14d-8a73-0f5ffae23315
BOT = '<bot-guid>'           # e.g. f19e1c40-f07e-f111-ab0e-70a8a5b24e56
TENANT = '<tenant-guid>'     # e.g. 03cc92c3-986c-4cf4-ae27-1478cf99d17f
RUN_PREFIX = '<run-prefix>'  # first 8 chars of run ID
MAX_POLLS = 50

def refresh():
    """Refresh the eval PPAPI Bearer token via MSAL cache."""
    subprocess.run(['node', 'refresh_eval_token.cjs'], cwd=REFRESH_DIR,
                   env={'NODE_PATH': './node_modules'}, capture_output=True, timeout=30)

def poll():
    for i in range(MAX_POLLS):
        try:
            token = open(TOKEN_FILE, encoding='utf-8').read().strip()
            h = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json',
                'Origin': 'https://copilotstudio.microsoft.com',
                'X-CCI-ApplicationSource': 'Web',
                'X-CCI-BapEnvironmentId': ENV,
                'X-CCI-BotId': BOT,
                'X-CCI-CdsBotId': BOT,
                'X-CCI-TenantId': TENANT,
            }
            base = f'{GW}/environments/{ENV}/bots/{BOT}/makerevaluations'
            req = urllib.request.Request(base + '?$top=5', headers=h)
            with urllib.request.urlopen(req, timeout=15) as resp:
                runs = json.loads(resp.read())

            for r in runs:
                rid = r.get('id', '')
                if rid.startswith(RUN_PREFIX):
                    state = r.get('state', '?')
                    ag = r.get('aggregatedGraderResults', [])
                    p = f = 0
                    for m in ag:
                        if m.get('name') == 'totalSucceeded': p = m.get('count', 0)
                        if m.get('name') == 'totalFailed': f = m.get('count', 0)
                    total = p + f
                    pct = p * 100 // total if total > 0 else 0
                    ts = time.strftime('%H:%M:%S')
                    sys.stdout.write(f'[{ts}] Poll {i+1}: {state:12s} | {p:3d}/{total:3d} = {pct:3d}%\n')
                    sys.stdout.flush()
                    if state in ('Completed', 'Failed', 'Cancelled'):
                        print(f'\n=== DONE: {pct}% ({p}/{total}) ===')
                        return
                    break

        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                print(f'Token expired (HTTP {e.code}) — refreshing...')
                refresh()
                time.sleep(2)
            else:
                print(f'HTTP {e.code}: {str(e.read()[:200])}')
        except Exception as e:
            print(f'Error: {type(e).__name__}: {e}')
            time.sleep(10)

        time.sleep(60)

    print('Max polls reached without completion')

if __name__ == '__main__':
    poll()
