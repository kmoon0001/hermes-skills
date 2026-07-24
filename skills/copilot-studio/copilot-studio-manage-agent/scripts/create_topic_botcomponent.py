#!/usr/bin/env python3
"""Create a NEW topic (botcomponent, componenttype 9) under a Copilot Studio bot via the
Dataverse Web API. ADDITIVE: never modifies existing topics.

Validated 2026-07-12 on Pacific Coast Case Historian (bot ad635500...). Two gotchas baked in:

  1. Parent link MUST use the navigation-property bind `parentbotid@odata.bind: "/bots(<GUID>)"`.
     Passing `_parentbotid_value: "<GUID>"` (lookup string) 400s with
     "CRM do not support direct update of Entity Reference properties".

  2. `schemaname` MUST start with a valid customization prefix (e.g. `auto_agent_XRF5I.`).
     A bare name 400s with "Export key attribute schemaname ... must start with a valid
     customization prefix". Grab the prefix from any existing sibling topic's schemaname
     (the PCCH topics use `auto_agent_XRF5I.`).

Dataverse CRM token is read from a file (the ~2930-char az token truncates in the terminal
if captured into a shell variable). Default token file: ~/.copilot-studio-cli/<org>-dv-token.txt.
Override with env DV_TOKEN_FILE. If no file, fetches live via full-path az.cmd.

Usage:
  python create_topic_botcomponent.py <local_yaml_path> [--dry]

Env overrides (optional):
  PCCH_ORG    Dataverse org short name   (default orgbd048f00)
  PCCH_BOT    Target bot GUID            (default ad635500-cf47-f111-bec5-70a8a5b1c3a3)
  PCCH_PREFIX Customization prefix       (default auto_agent_XRF5I)
  DV_TOKEN_FILE  Path to a saved CRM token (avoids az call / truncation)
"""
import sys, os, json, urllib.request, urllib.error, re, subprocess

ORG = os.environ.get('PCCH_ORG', 'orgbd048f00')
BOT = os.environ.get('PCCH_BOT', 'ad635500-cf47-f111-bec5-70a8a5b1c3a3')
PREFIX = os.environ.get('PCCH_PREFIX', 'auto_agent_XRF5I')
AZ = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
AZP = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'


def token():
    tf = os.environ.get('DV_TOKEN_FILE')
    if tf and os.path.exists(tf):
        return open(tf, encoding='utf-8').read().strip()
    env = dict(os.environ)
    env['PATH'] = AZP + ';' + env.get('PATH', '')
    return subprocess.run(
        [AZ, 'account', 'get-access-token', '--resource',
         f'https://{ORG}.crm.dynamics.com', '--query', 'accessToken', '-o', 'tsv'],
        capture_output=True, text=True, env=env).stdout.strip()


def main():
    if len(sys.argv) < 2:
        print('Usage: python create_topic_botcomponent.py <local_yaml_path> [--dry]')
        sys.exit(2)
    path = sys.argv[1]
    dry = '--dry' in sys.argv
    data = open(path, encoding='utf-8').read()
    m = re.search(r"displayName:\s*(.+)", data)
    disp = m.group(1).strip().strip('"') if m else os.path.splitext(os.path.basename(path))[0]
    sch = f"{PREFIX}.{re.sub(r'[^A-Za-z0-9]', '', disp)}"
    body = {
        'name': disp,
        'schemaname': sch,
        'componenttype': 9,
        'parentbotid@odata.bind': f"/bots({BOT})",
        'data': data,
    }
    tok = token()
    print(f"Creating topic '{disp}' (schemaname={sch}) under bot {BOT}")
    if dry:
        print('DRY RUN — no write.'); return
    req = urllib.request.Request(
        f"https://{ORG}.crm.dynamics.com/api/data/v9.2/botcomponents",
        data=json.dumps(body).encode(), method='POST')
    for h, v in {
        'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json',
        'OData-MaxVersion': '4.0', 'OData-Version': '4.0', 'Accept': 'application/json',
    }.items():
        req.add_header(h, v)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        print('status', resp.status, 'entityId', resp.getheader('OData-EntityId'))
        print('TOPIC CREATED OK.')
    except urllib.error.HTTPError as e:
        print('HTTP', e.code, '—', e.read().decode()[:600])
        sys.exit(1)


if __name__ == '__main__':
    main()
