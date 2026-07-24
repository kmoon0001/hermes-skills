"""
Background eval poller with token refresh. Run via:
  terminal(background=true, command='python3 background-poll.py <run-id>', notify_on_complete=true)

Refreshes the MSAL eval token every ~5 min so polling survives the 15-min token expiry.
Polls the aggregrated list endpoint for live progress, only hits /details at completion.
"""
import json, urllib.request, os, time, sys

ENV = os.environ.get("EVAL_ENV", "a944fdf0-0d2e-e14d-8a73-0f5ffae23315")
BOT = os.environ.get("EVAL_BOT", "")
RUN_ID = sys.argv[1] if len(sys.argv) > 1 else ""
GW = f"https://powervamg.us-il106.gateway.prod.island.powerapps.com/api/botmanagement/v2/environments/{ENV}/bots/{BOT}"
TOKEN_FILE = os.path.expanduser("~/.copilot-studio-cli/test-agent-token.txt")
REFRESH_CMD = f'cd {os.path.expanduser("~/skills-for-copilot-studio/scripts").replace(chr(92), chr(92)*2)} && node refresh_eval_token.cjs 2>NUL'

def get_headers():
    token = open(TOKEN_FILE, encoding="utf-8").read().strip()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-CCI-ApplicationSource": "Web",
        "X-CCI-BapEnvironmentId": ENV,
        "X-CCI-BotId": BOT,
        "X-CCI-CdsBotId": BOT,
        "X-CCI-TenantId": "03cc92c3-986c-4cf4-ae27-1478cf99d17f",
        "X-CCI-OrganizationId": ENV,
    }

def refresh():
    os.system(REFRESH_CMD)

def poll(run_id):
    # List endpoint: live scores during InProgress
    url = f"{GW}/makerevaluations?$top=6"
    req = urllib.request.Request(url, headers=get_headers())
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            arr = json.loads(r.read())
    except Exception:
        refresh()
        return False

    for run in arr:
        if not run.get("id", "").startswith(run_id[:8]):
            continue
        state = run.get("state", "?")
        ag = run.get("aggregatedGraderResults") or []
        s = next((m["count"] for m in ag if m["name"] == "totalSucceeded"), 0)
        f = next((m["count"] for m in ag if m["name"] == "totalFailed"), 0)
        t = s + f
        pct = f"{round(s/t*100)}%" if t else "?"
        print(f"  {run_id[:8]} {state} {pct} ({s}/{t})", flush=True)

        if state in ("Completed",):
            print(f"DONE {s}/{t} = {pct}", flush=True)
            return True
        if state in ("Failed", "Cancelled"):
            print(f"TERMINAL {state}", flush=True)
            return True
        break
    return False


if __name__ == "__main__":
    if not RUN_ID:
        # Auto-discover the most recent InProgress run
        url = f"{GW}/makerevaluations?$top=3"
        req = urllib.request.Request(url, headers=get_headers())
        with urllib.request.urlopen(req, timeout=15) as r:
            for run in json.loads(r.read()):
                if run.get("state") in ("InProgress", "Queued"):
                    RUN_ID = run["id"]
                    print(f"Auto-found: {RUN_ID[:12]}")
                    break
        if not RUN_ID:
            print("No active run found")
            sys.exit(1)

    refresh()
    for i in range(120):
        time.sleep(30)
        if poll(RUN_ID):
            sys.exit(0)
        if i > 0 and i % 10 == 0:
            refresh()
    print("Timed out after 60 min")
