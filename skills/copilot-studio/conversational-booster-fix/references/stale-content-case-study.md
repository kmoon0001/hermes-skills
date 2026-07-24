# Stale Content Field Case Study — Ensign Default (Jul 4 2026)

## The Symptom

PT_Specialist scored 0-5% conversational on Ensign Default, while SLP_Specialist (same topic pattern) scored 85%. OT and TDA also showed low conversational scores.

## The Proposed (Wrong) Theory

A session proposed that PT's Conversational Boosting was "DELETED + recreated" with a new component GUID, and that "the platform caches the component GUID internally" — a new GUID wouldn't register with the orchestrator.

## The Actual Investigation

### Step 1: Check component IDs
Queried `botcomponents` for all OnUnknownIntent topics. All three agents had the SAME component IDs as recorded in `botcomponent-ids.csv` — no deletion/recreation had happened. The GUID theory was false.

### Step 2: Check YAML structure
The `data` field was correct on all three agents: `SearchAndSummarizeContent`, `ConditionGroup`, `Topic.Answer`, `System.Activity.Text`, `EndDialog` with `clearTopicQueue: true`. No structural issues.

### Step 3: Check content field (THE SMOKING GUN)
```python
# Query BOTH data and content fields
url = f"{ORG_URL}api/data/v9.2/botcomponents({cid})?$select=data,content"

data_sasc = "SearchAndSummarizeContent" in data_yaml
content_sasc = "SearchAndSummarizeContent" in content_yaml
content_fbc = "FallbackCount" in content_yaml  # OLD broken pattern
```

Results:
- PT-Fallback: `data` SASC=True, `content` SASC=False, FallbackCount=True — **STALE**
- OT-Fallback: same stale pattern
- TDA-Fallback: same stale pattern
- SLP-Search: `data` SASC=True, `content` SASC=True — **COMPILED** (explains 85%)

### Root Cause

The `data` field was patched with correct YAML via Dataverse API. But **publish was never run** after the patch. The `content` field (compiled YAML, what the agent actually executes at eval time) still contained the old broken pattern with `System.FallbackCount < 3` and no `SearchAndSummarizeContent`.

### Failed Fix Attempts

1. **`pac copilot publish`** — returned "Published successfully" but did NOT regenerate `content` for system/OnUnknownIntent topics
2. **PvaPublish API** — returned HTTP 200 with empty `PublishedBotContentId` (silent failure)
3. **Deactivate + Reactivate + Publish** — `content` still not regenerated
4. **Direct `content` PATCH** — blocked by Dataverse validator: "Unexpected character encountered while parsing value: k" (platform rejects writes to `content` for complex YAML)

### The Only Working Fix

Opening the Fallback topic in the **Copilot Studio UI code editor** and saving. The UI save triggers content compilation — it regenerates `content` from `data`. This is the ONLY path when `pac publish` and `PvaPublish` both fail to recompile system topics.

### Verification Code (Use After Every Fix)

```python
import subprocess, json, urllib.request, urllib.parse

ORG_URL = "https://org3353a370.crm.dynamics.com/"
r = subprocess.run(["az.cmd", "account", "get-access-token",
    "--resource", "https://org3353a370.crm.dynamics.com/",
    "--query", "accessToken", "-o", "tsv"],
    capture_output=True, text=True, shell=True)
token = r.stdout.strip()

# Check ALL OnUnknownIntent topics for the agent
CHECKS = {
    "PT-Fallback": "959540fc-bce6-4a04-a152-bc955567f849",
    "PT-Search": "388ca5fa-2077-f111-ab0f-000d3a37eba2",
}

for label, cid in CHECKS.items():
    url = f"{ORG_URL}api/data/v9.2/botcomponents({cid})?$select=data,content"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    req.add_header("OData-MaxVersion", "4.0")
    
    resp = urllib.request.urlopen(req, timeout=30)
    comp = json.loads(resp.read())
    
    data_sasc = "SearchAndSummarizeContent" in (comp.get("data") or "")
    content_sasc = "SearchAndSummarizeContent" in (comp.get("content") or "")
    content_fbc = "FallbackCount" in (comp.get("content") or "")
    
    ok = data_sasc and content_sasc and not content_fbc
    print(f"{label}: data_SASC={data_sasc} content_SASC={content_sasc} FBC={content_fbc} → {'✓' if ok else '✗ STALE'}")

print(f"All compiled: {all_ok}")
```

## Key Takeaways

1. **Always verify `content` after publish** — correct `data` + stale `content` = 0-5% scores that look like a different root cause
2. **`pac copilot publish` is not 100% reliable** for system/OnUnknownIntent topic compilation — the Copilot Studio UI code editor save is the ground truth
3. **The GUID-caching theory is a red herring** — always check `data` vs `content` before theorizing about platform internals
4. **Check the working agent for comparison** — SLP's compiled `content` was the key to understanding why it scored 85% while PT/OT/TDA scored 0-5%
