# Dataverse Test Case Query Extraction

When the Gateway API `/makerevaluations/{runId}/details` returns HTTP 404 (regional PPAPI limitation), per-case grader data is unavailable. However, the raw test case query text is stored in Dataverse as **componenttype 19** botcomponents.

## Extraction Recipe

```python
import urllib.request, json, urllib.parse
AZ = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd'
import subprocess, os
AZP = r'C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin'
env = dict(os.environ); env['PATH'] = AZP + ';' + env.get('PATH', '')
r = subprocess.run([AZ, 'account', 'get-access-token', '--resource', 'https://orgbd048f00.crm.dynamics.com/'],
                   capture_output=True, text=True, env=env)
token = json.loads(r.stdout)['accessToken']
h = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
params = urllib.parse.urlencode({
    '$filter': f"_parentbotid_value eq '{BOT}' and componenttype eq 19",
    '$select': 'name,data',
    '$top': 100
})
req = urllib.request.Request(f'https://orgbd048f00.crm.dynamics.com/api/data/v9.2/botcomponents?{params}', headers=h)
comps = json.loads(urllib.request.urlopen(req, timeout=30).read())['value']
```

## Classify by Domain

```python
categories = {}
for tc in comps:
    # Type-19 data may be JSON or plain text
    data = tc.get('data', '')
    try: d = json.loads(data) if isinstance(data, str) else data
    except: d = {}
    query = ''
    for key in ['prompt', 'query', 'userMessage', 'text', 'utterance', 'description', 'name']:
        if key in d and isinstance(d[key], str): query = d[key]; break
    if not query: query = tc.get('name', '?')
    
    ql = query.lower()
    if any(w in ql for w in ['upload', 'file', 'pdf']): cat = 'file_upload'
    elif any(w in ql for w in ['prior level', 'plof', 'prior function']): cat = 'plof_extraction'
    elif any(w in ql for w in ['sbar', 'handoff']): cat = 'sbar'
    elif any(w in ql for w in ['mds', 'crosswalk', 'pdpm']): cat = 'mds_pdpm'
    elif any(w in ql for w in ['discharge', 'transition']): cat = 'discharge'
    elif any(w in ql for w in ['medication', 'lab', 'imaging', 'vital']): cat = 'meds_labs_imaging'
    elif any(w in ql for w in ['summary', 'synthesize', 'longitudinal', 'case history']): cat = 'synthesis'
    elif any(w in ql for w in ['gap', 'audit', 'compliance', 'review', 'denial']): cat = 'audit_compliance'
    elif any(w in ql for w in ['fall risk', 'precaution', 'safety', 'cognitive', 'swallow']): cat = 'clinical_safety'
    elif any(w in ql for w in ['progress', 'recert']): cat = 'progress_recert'
    elif any(w in ql for w in ['hospital course', 'stay', 'admission']): cat = 'hospital_course'
    else: cat = 'other'
    
    categories.setdefault(cat, []); categories[cat].append(query)

for cat, qs in sorted(categories.items(), key=lambda x: -len(x[1])):
    print(f"{cat}: {len(qs)} cases — e.g. \"{qs[0][:60]}\"")
```

## Cross-Reference with Topic Trigger Phrases

After getting categories, compare against each active topic's `triggerQueries`. Categories with no matching trigger phrases explain ~category_count% of failures — they all fall through to Fallback/generative answering.

Common coverage gaps for acute-to-SNF agents:
- **meds_labs_imaging**: Topics rarely cover pharmacology, lab reference ranges, or imaging interpretation
- **clinical_safety**: Fall risk, swallowing, precautions often not in any topic's trigger phrases
- **hospital_course**: "Summarize the patient's hospital stay" — generic wording that misses narrow trigger phrases
