# Data-Sparse Leaf Patch Pattern — Therapy Report Prep V2

## Problem

Global anti-abstention instructions on GPT metadata, Conversational boosting,
and Fallback are OVERRIDDEN by leaf-level SASC `additionalInstructions` when a
generative orchestrator routes directly to the leaf. A leaf that says only
"Extract from user-provided text when present" will cause abstention/incompleteness
on data-sparse queries even when the global instructions say "never refuse."

## Fix: Three-mode leaf instructions

Replace the `additionalInstructions:` block in each leaf's SASC with three explicit
mode sections. The leaf topics to patch are `report_prep_v2.topic.*` (new-experience)
found in the Dataverse botcomponents collection filtered by `_parentbotid_value`.

### Leaf topic IDs (Therapy Report Prep V2)

| Topic | Component ID | Type-specific snippet |
|-------|-------------|----------------------|
| ProgressAnalysis | `83343002-744f-f111-bec5-7ced8d700cae` | Progress report prep: measurable change, goal progression, skilled intervention rationale, next-certification-period evidence fields, PDPM context. |
| RecertAnalysis | `85343002-744f-f111-bec5-7ced8d700cae` | Recertification medical necessity / continued skilled need: condition complexity over 30 days, why continued clinician skill is required, POC/certification fields, Jimmo maintenance review, payer denial risk flags. |
| DischargeAnalysis | `7d343002-744f-f111-bec5-7ced8d700cae` | Discharge summary prep: status at discharge, goal disposition, continuity-of-care / follow-up risks, unresolved-risk checklist, episode closure rationale. |
| EvalAnalysis | `7f343002-744f-f111-bec5-7ced8d700cae` | Evaluation analysis: baseline functional status, skilled service medical necessity, POC/goal quality, Section GG alignment, documentation completeness gaps. |
| ManualIntakeFallback | `81343002-744f-f111-bec5-7ced8d700cae` | General documentation intake: infer report type (progress/recert/discharge/eval) from text or request. Produce full structured package when enough text present; otherwise deliver missing-elements checklist. |

### Template `additionalInstructions` block

```yaml
      additionalInstructions: |-
        Provide a structured {TYPE} review for SNF rehab.

        ## DATA RICH — When the user provides full clinical text or notes
        Extract and analyze only from what was provided. Do NOT invent findings, scores,
        diagnoses, patient facts, or facility metrics.

        ## DATA SPARSE — When the user gives only record IDs, date, discipline, or a
        partial request WITHOUT clinical text
        Do NOT say "No notes found", "no documentation provided", or "the notes are not
        included". The agent does NOT have EHR retrieval — do not claim records were searched
        or unavailable. Instead, deliver a complete {TYPE_SHORT} pre-review package:
        - Full CMS compliance checklist for this report type
        - Required evidence and documentation elements
        - Placeholder language for missing clinical fields
        - Missing-fields table with "To complete from your facility data"
        - Do NOT ask "what document type" — use the topic context to infer the report type.

        ## PARTIAL DATA — When the user supplies metrics, counts, or one period but asks
        for comparison
        Format and analyze the provided values. Create blank comparator columns for missing
        periods. Mark missing values as "To complete from your facility data", not as
        unavailable. Do NOT claim any data was searched for or not found.

        ## REPORT TYPE SPECIFIC
        {TYPE_SPECIFIC}
        End with CLINICAL REVIEW REQUIRED.
```

Replace `{TYPE}` with the short name (e.g. "progress report review"),
`{TYPE_SHORT}` with the plain name (e.g. "progress report"), and
`{TYPE_SPECIFIC}` with the leaf-specific content from the table above.

### Patch procedure (Python via urllib + az)

```python
import json, urllib.request, urllib.parse, subprocess, re

ORG = 'https://orgbd048f00.crm.dynamics.com'
AZ = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'

def get_token():
    return json.loads(subprocess.run([AZ,'account','get-access-token',
        '--resource',ORG+'/','--tenant','03cc92c3-986c-4cf4-ae27-1478cf99d17f',
        '-o','json'], capture_output=True,text=True).stdout)['accessToken']

def dv_get(url_str):
    tok = get_token()
    h = {'Authorization': f'Bearer {tok}', 'Accept': 'application/json',
         'OData-MaxVersion': '4.0', 'OData-Version': '4.0'}
    p = urllib.parse.urlparse(url_str)
    ep = urllib.parse.quote(p.path, safe='/@:$&?=%,')
    s = p._replace(path=ep).geturl()
    req = urllib.request.Request(s, headers=h)
    req.selector = ep; req.full_url = s
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)

def dv_patch(cid, body_dict):
    tok = get_token()
    h = {'Authorization': f'Bearer {tok}', 'Content-Type': 'application/json',
         'If-Match': '*', 'OData-MaxVersion': '4.0', 'OData-Version': '4.0'}
    url = f'{ORG}/api/data/v9.2/botcomponents({cid})'
    data = json.dumps(body_dict).encode('utf-8')
    req = urllib.request.Request(url, data=data, method='PATCH', headers=h)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code

# 1. GET current data
c = dv_get(f"{ORG}/api/data/v9.2/botcomponents({CID})?$select=data")
d = c.get('data', '')

# 2. Replace additionalInstructions
old_start = d.find('additionalInstructions: |-')
# Find the end — next top-level key at same or lower indent
# ... (see execute_code in session transcript for full algorithm)

# 3. PATCH
d_new = d[:old_start] + new_instructions_block + d[rest_start:]
d_crlf = d_new.replace('\r\n','\n').replace('\r','\n').replace('\n','\r\n')
dv_patch(CID, {'data': d_crlf})

# 4. VERIFY
cv = dv_get(f"{ORG}/api/data/v9.2/botcomponents({CID})?$select=data")
assert 'DATA SPARSE' in cv.get('data','')
assert 'Extract only from user-provided text when present' not in cv.get('data','')
```

### Publish after patching

After all leaf patches are applied (204 OK each), publish via the gateway API:

```python
GATEWAY = 'https://powervamg.us-il106.gateway.prod.island.powerapps.com'
tok = json.loads(subprocess.run([AZ,'account','get-access-token',
    '--resource','96ff4394-9197-43aa-b393-6a41652e21f8','-o','json'],
    capture_output=True,text=True).stdout)['accessToken']

GH = {
    'Authorization': f'Bearer {tok}',
    'X-CCI-ApplicationSource': 'Web',
    'X-CCI-BapEnvironmentId': ENV_ID,
    'X-CCI-BotId': BOT,
    'X-CCI-CdsBotId': BOT,
    'X-CCI-TenantId': '03cc92c3-986c-4cf4-ae27-1478cf99d17f',
    'X-CCI-OrganizationId': ENV_ID,
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}
url = f'{GATEWAY}/api/botmanagement/v1/environments/{ENV_ID}/bots/{BOT}/publishv2-operations'
req = urllib.request.Request(url, data=b'{}', method='POST', headers=GH)
# Poll GET same URL until isInFinalState=true and state=Finished
# Verify via Dataverse: GET bots({BOT})?$select=publishedon,synchronizationstatus
```

Publish takes ~60-90s. Two separate publishes (leaf patches + new topic) both needed.

## IDT Therapy Agenda topic

Create a separate Pattern-L leaf for explicit IDT requests. 10 trigger phrases,
explicit "never ask what document type" in instructions.

**POST-create details (validated 2026-07-17):**
- Schema prefix: match target agent's existing topics (e.g. `report_prep_v2.topic.X`)
- Headers: DO NOT include `If-Match` — 400s on POST
- Include `statecode: 0, statuscode: 1`
- `parentbotid@odata.bind: "/bots({BOT_ID})"` — NOT `_parentbotid_value`
- Response is 204 (empty body) — ID in `OData-EntityId` header
- Verify with `$filter=schemaname eq '<name>'` + check `_parentbotid_value`
- Publish in separate operation after creation

## Verified results (Therapy Report Prep V2, 2026-07-17)

- Conv #1 (pre-fix, started before publish): 9/20 = 45.0%
- Conv #2 (post-fix): 11/20 = 55.0% (+10 points)
- SR #1 (post-fix): 68/100 = 68.0%
- SR #2 (post-fix, different test set): 86/100 = 86.0%
- Post-fix averages: Conv 55.0% (+7.5pts), SR 77.0% (+3.0pts)

Remaining 9 Conv failures: NOT refusals — agent delivers substantive CMS policy
content but grader expects facility-specific data that tests didn't supply. This
is an **eval-setup issue** (Pattern E5: reword facility-export tests to ask about
CMS standards rather than facility-specific numbers).
