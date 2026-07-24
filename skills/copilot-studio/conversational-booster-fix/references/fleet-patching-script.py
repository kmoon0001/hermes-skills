#!/usr/bin/env python3
"""
Fleet-wide Conversational Booster Fix — apply via Dataverse API.

PATCHes Fallback topics with new YAML and deactivates overlapping Clinical Inquiry
topics across all 4 therapy agents (OT, PT, SLP, TDA).

Usage:
    python fleet-patching-script.py          # dry-run (print only)
    python fleet-patching-script.py --apply  # apply changes
    python fleet-patching-script.py --publish  # apply + publish all agents
"""

import subprocess, json, urllib.request, urllib.parse, sys

ORG_URL = "https://org3353a370.crm.dynamics.com/"
AZ_PATH = "C:\\Program Files\\Microsoft SDKs\\Azure\\CLI2\\wbin\\az.cmd"

BOTS = {
    "OT": {
        "bot": "73b45e98-af7a-443a-aa12-6d8a05118530",
        "fallback": "ae395715-cf8c-4ee6-ba0a-7f767d9e2a3c",
        "clinical": "ba8940b8-9dc0-4170-9866-bb7f5fb93fa9",
        "yaml": """kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: SearchAndSummarizeContent
      id: search-cb
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Answer the user's OT clinical or compliance question using CMS Ch. 15, AOTA standards, and all available knowledge sources.
        - First sentence must directly answer the question. Be a helpful OT clinical and compliance chatbot.
        - Cite regulations inline by natural name. Plain text only -- no JSON or citation tokens.
        - Keep response under 800 characters total. End with: Clinical review required. Non-Device CDS only.
      applyModelKnowledgeSetting: true
    - kind: ConditionGroup
      id: has-answer-check
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: SendActivity
              id: send-answer
              activity: =Topic.Answer
            - kind: EndDialog
              id: end-with-answer
              clearTopicQueue: true
      elseActions:
        - kind: SendActivity
          id: send-fallback
          activity: I don't have specific information on that in my OT knowledge sources. Could you rephrase your question about OT documentation compliance, Medicare guidelines, or clinical standards?
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
inputType: {}
outputType: {}"""
    },
    "PT": {
        "bot": "593407f3-539b-490f-84ac-d74e13216c81",
        "fallback": "959540fc-bce6-4a04-a152-bc955567f849",
        "clinical": "dac45f2e-ea96-4813-9a20-332ba0f97392",
        "yaml": """kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: SearchAndSummarizeContent
      id: search-cb
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Answer the user's PT clinical or compliance question using CMS Ch. 15, APTA standards, and all available knowledge sources.
        - First sentence must directly answer the question. Be a helpful PT clinical and compliance chatbot.
        - Cite regulations inline by natural name. Plain text only -- no JSON or citation tokens.
        - Keep response under 800 characters total. End with: Clinical review required. Non-Device CDS only.
      applyModelKnowledgeSetting: true
    - kind: ConditionGroup
      id: has-answer-check
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: SendActivity
              id: send-answer
              activity: =Topic.Answer
            - kind: EndDialog
              id: end-with-answer
              clearTopicQueue: true
      elseActions:
        - kind: SendActivity
          id: send-fallback
          activity: I don't have specific information on that in my PT knowledge sources. Could you rephrase your question about PT documentation compliance, Medicare guidelines, or clinical standards?
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
inputType: {}
outputType: {}"""
    },
    "SLP": {
        "bot": "6e437a77-a5dc-4984-90eb-4924eab10006",
        "fallback": "1cce87b6-3419-46bb-9950-d115d20a9cf5",
        "clinical": "d4509e45-ea7e-4e53-8f09-e93add0ef8ef",
        "yaml": """kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: SearchAndSummarizeContent
      id: search-cb
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Answer the user's SLP clinical or compliance question using CMS Ch. 15, ASHA guidelines, and all available knowledge sources.
        - First sentence must directly answer the question. Be a helpful SLP clinical and compliance chatbot.
        - Cite regulations inline by natural name. Plain text only -- no JSON or citation tokens.
        - Keep response under 800 characters total. End with: Clinical review required. Non-Device CDS only.
      applyModelKnowledgeSetting: true
    - kind: ConditionGroup
      id: has-answer-check
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: SendActivity
              id: send-answer
              activity: =Topic.Answer
            - kind: EndDialog
              id: end-with-answer
              clearTopicQueue: true
      elseActions:
        - kind: SendActivity
          id: send-fallback
          activity: I don't have specific information on that in my SLP knowledge sources. Could you rephrase your question about SLP documentation compliance, Medicare guidelines, or clinical standards?
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
inputType: {}
outputType: {}"""
    },
    "TDA": {
        "bot": "4d0ed0d3-30f6-f011-8406-000d3a37eba2",
        "fallback": "19972666-7de9-45f3-98da-58726f7a06ad",
        "clinical": "ac3b0308-da75-f111-ab0f-000d3a37eba2",
        "yaml": """kind: AdaptiveDialog
beginDialog:
  kind: OnUnknownIntent
  id: main
  actions:
    - kind: SearchAndSummarizeContent
      id: search-cb
      latencyMessageSettings:
        allowLatencyMessage: false
      variable: Topic.Answer
      userInput: =System.Activity.Text
      additionalInstructions: |-
        - Answer the user's therapy documentation audit question using CMS Ch. 15, APTA, AOTA, ASHA standards, and all available knowledge sources.
        - First sentence must directly answer the question. Be a helpful therapy compliance chatbot.
        - Cite regulations inline by natural name. Plain text only -- no JSON or citation tokens.
        - Keep response under 800 characters total. End with: Clinical review required. Non-Device CDS only.
      applyModelKnowledgeSetting: true
    - kind: ConditionGroup
      id: has-answer-check
      conditions:
        - id: has-answer
          condition: =!IsBlank(Topic.Answer)
          actions:
            - kind: SendActivity
              id: send-answer
              activity: =Topic.Answer
            - kind: EndDialog
              id: end-with-answer
              clearTopicQueue: true
      elseActions:
        - kind: SendActivity
          id: send-fallback
          activity: I don't have specific information on that in my therapy documentation knowledge sources. Could you rephrase your question about compliance, Medicare guidelines, or clinical documentation standards?
        - kind: EndDialog
          id: end-fallback
          clearTopicQueue: true
inputType: {}
outputType: {}"""
    }
}

def get_token():
    r = subprocess.run([AZ_PATH, "account", "get-access-token",
                        "--resource", ORG_URL.rstrip("/") + "/",
                        "--query", "accessToken", "-o", "tsv"],
                       capture_output=True, text=True)
    return r.stdout.strip()

def patch_component(token, cid, data_yaml, label):
    url = f"{ORG_URL}api/data/v9.2/botcomponents({cid})"
    body = json.dumps({"data": data_yaml})
    req = urllib.request.Request(url, data=body.encode(), method="PATCH")
    for h, v in [("Authorization", f"Bearer {token}"),
                 ("Content-Type", "application/json"),
                 ("Accept", "application/json"),
                 ("OData-MaxVersion", "4.0")]:
        req.add_header(h, v)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        print(f"  OK {label} (HTTP {resp.status})")
        return True
    except urllib.error.HTTPError as e:
        print(f"  FAIL {label} (HTTP {e.code})")
        return False

def deactivate_component(token, cid, label):
    url = f"{ORG_URL}api/data/v9.2/botcomponents({cid})"
    body = json.dumps({"componentstate": 2, "statecode": 1})
    req = urllib.request.Request(url, data=body.encode(), method="PATCH")
    for h, v in [("Authorization", f"Bearer {token}"),
                 ("Content-Type", "application/json"),
                 ("Accept", "application/json"),
                 ("OData-MaxVersion", "4.0")]:
        req.add_header(h, v)
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        print(f"  Deactivated {label} (HTTP {resp.status})")
        return True
    except urllib.error.HTTPError as e:
        print(f"  FAIL deactivate {label} (HTTP {e.code})")
        return False

def publish_bot(token, bot_id, name):
    url = f"{ORG_URL}api/data/v9.2/bots({bot_id})/Microsoft.Dynamics.CRM.PvaPublish"
    body = json.dumps({})
    req = urllib.request.Request(url, data=body.encode(), method="POST")
    for h, v in [("Authorization", f"Bearer {token}"),
                 ("Content-Type", "application/json"),
                 ("Accept", "application/json"),
                 ("OData-MaxVersion", "4.0")]:
        req.add_header(h, v)
    try:
        resp = urllib.request.urlopen(req, timeout=120)
        print(f"  Published {name} (HTTP {resp.status})")
        return True
    except urllib.error.HTTPError as e:
        print(f"  PUBLISH FAIL {name} (HTTP {e.code})")
        return False

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    also_publish = "--publish" in sys.argv

    if not apply:
        print("=== DRY RUN (pass --apply to execute) ===")

    token = get_token() if apply else None
    if apply and not token:
        print("ERROR: Could not get auth token")
        sys.exit(1)

    for name, cfg in BOTS.items():
        print(f"\n--- {name} ---")

        # Patch fallback
        if apply:
            patch_component(token, cfg["fallback"], cfg["yaml"], f"{name} Fallback")
        else:
            print(f"  Would PATCH Fallback ({cfg['fallback'][:8]}...) with new YAML")

        # Deactivate clinical
        if apply:
            deactivate_component(token, cfg["clinical"], f"{name} ClinicalInquiry")
        else:
            print(f"  Would DEACTIVATE ClinicalInquiry ({cfg['clinical'][:8]}...)")

    if apply and also_publish:
        print("\n=== Publishing ===")
        for name, cfg in BOTS.items():
            publish_bot(token, cfg["bot"], name)

    if not apply:
        print(f"\nTo execute: python {__file__} --apply")
        print("To execute and publish: python {__file__} --publish")
