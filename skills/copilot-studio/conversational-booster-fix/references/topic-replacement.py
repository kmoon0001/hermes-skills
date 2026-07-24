"""
Fleet-wide conversational booster topic fix via Dataverse API.

Usage:
    python topic-replacement.py            # dry-run mode
    python topic-replacement.py --apply    # actual PATCH

Requirements:
    - az CLI with Dataverse org access
    - pac CLI for publish step
"""

import subprocess, json, urllib.request, urllib.parse, sys

DRY_RUN = "--apply" not in sys.argv

# ---- CONFIG ----
ORG_URL = "https://org3353a370.crm.dynamics.com/"
AGENTS = {
    "OT": {
        "bot": "73b45e98-af7a-443a-aa12-6d8a05118530",
        "fallback": "ae395715-cf8c-4ee6-ba0a-7f767d9e2a3c",
        "clinical": "ba8940b8-9dc0-4170-9866-bb7f5fb93fa9",
    },
    "PT": {
        "bot": "593407f3-539b-490f-84ac-d74e13216c81",
        "fallback": "959540fc-bce6-4a04-a152-bc955567f849",
        "clinical": "dac45f2e-ea96-4813-9a20-332ba0f97392",
    },
    "SLP": {
        "bot": "6e437a77-a5dc-4984-90eb-4924eab10006",
        "fallback": "1cce87b6-3419-46bb-9950-d115d20a9cf5",
        "clinical": "d4509e45-ea7e-4e53-8f09-e93add0ef8ef",
    },
    "TDA": {
        "bot": "4d0ed0d3-30f6-f011-8406-000d3a37eba2",
        "fallback": "19972666-7de9-45f3-98da-58726f7a06ad",
        "clinical": "ac3b0308-da75-f111-ab0f-000d3a37eba2",
    },
}

# YAML templates per discipline - see SKILL.md or conversational-booster-fix skill
YAML_TEMPLATES = {
    "OT": """kind: AdaptiveDialog\nbeginDialog:\n  kind: OnUnknownIntent\n  id: main\n  actions:\n    - kind: SearchAndSummarizeContent\n      id: search-cb\n      latencyMessageSettings:\n        allowLatencyMessage: false\n      variable: Topic.Answer\n      userInput: =System.Activity.Text\n      additionalInstructions: |-\n        - Answer the user's OT clinical or compliance question using CMS Ch. 15, AOTA standards, and all available knowledge sources.\n        - First sentence must directly answer the question. Be a helpful OT clinical and compliance chatbot.\n        - Cite regulations inline by natural name. Plain text only -- no JSON or citation tokens.\n        - Keep response under 800 characters total. End with: Clinical review required. Non-Device CDS only.\n      applyModelKnowledgeSetting: true\n    - kind: ConditionGroup\n      id: has-answer-check\n      conditions:\n        - id: has-answer\n          condition: =!IsBlank(Topic.Answer)\n          actions:\n            - kind: SendActivity\n              id: send-answer\n              activity: =Topic.Answer\n            - kind: EndDialog\n              id: end-with-answer\n              clearTopicQueue: true\n      elseActions:\n        - kind: SendActivity\n          id: send-fallback\n          activity: I don't have specific information on that in my OT knowledge sources. Could you rephrase your question about OT documentation compliance, Medicare guidelines, or clinical standards?\n        - kind: EndDialog\n          id: end-fallback\n          clearTopicQueue: true\ninputType: {}\noutputType: {}""",
    # PT, SLP, TDA templates follow same pattern with discipline-specific text
}


def get_token():
    r = subprocess.run(
        ["C:\\Program Files\\Microsoft SDKs\\Azure\\CLI2\\wbin\\az.cmd",
         "account", "get-access-token",
         "--resource", ORG_URL,
         "--query", "accessToken", "-o", "tsv"],
        capture_output=True, text=True
    )
    return r.stdout.strip()


def patch_component(token, component_id, data_yaml, label):
    url = f"{ORG_URL}api/data/v9.2/botcomponents({component_id})"
    body = json.dumps({"data": data_yaml})
    req = urllib.request.Request(url, data=body.encode(), method="PATCH")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("OData-MaxVersion", "4.0")
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return resp.status == 204
    except urllib.error.HTTPError as e:
        print(f"  ERROR {e.code} [{label}]: {e.read().decode(errors='replace')[:200]}")
        return False


# ---- MAIN ----
token = get_token()
for name, cfg in AGENTS.items():
    print(f"{name}: Patching fallback...")
    if not DRY_RUN:
        ok = patch_component(token, cfg["fallback"], YAML_TEMPLATES.get(name, YAML_TEMPLATES["OT"]), f"{name} Fallback")
        print(f"  {'OK' if ok else 'FAIL'}")
    else:
        print(f"  [DRY RUN - would patch {cfg['fallback'][:8]}...]")

    print(f"{name}: Deactivating clinical inquiry ({cfg['clinical'][:8]}...)...")
    if not DRY_RUN:
        url = f"{ORG_URL}api/data/v9.2/botcomponents({cfg['clinical']})"
        body = json.dumps({"componentstate": 2, "statecode": 1})
        req = urllib.request.Request(url, data=body.encode(), method="PATCH")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")
        req.add_header("OData-MaxVersion", "4.0")
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            print(f"  {'OK' if resp.status == 204 else f'HTTP {resp.status}'}")
        except urllib.error.HTTPError as e:
            print(f"  ERROR {e.code}: {e.read().decode(errors='replace')[:200]}")
    else:
        print(f"  [DRY RUN]")

print("\nDone. Publish each agent and run evals.")
