# CMS Provider Data — Field Index Map

CSV column indices (0-based) for the CMS Nursing Home Compare dataset (`4pq5-n9py`).
Use these to extract specific fields from the full 99-column CSV without downloading everything.

## Core Identifiers

| Field | CSV Index | Notes |
|-------|-----------|-------|
| CMS Certification Number (CCN) | 0 | Primary CMS facility ID |
| Provider Name | 1 | Official CMS name (all-caps) |
| Provider Address | 2 | Street address |
| City/Town | 3 | |
| State | 4 | 2-letter abbreviation |
| ZIP Code | 5 | |
| County/Parish | 8 | |
| Urban/Rural | 9 | |

## Rating Fields

| Field | CSV Index | Range |
|-------|-----------|-------|
| Overall Rating | 32 | 1-5 stars or empty |
| Health Inspection Rating | 34 | 1-5 |
| Staffing Rating | 42 | 1-5 |
| QM Rating | 36 | 1-5 (composite) |
| Long-Stay QM Rating | 38 | 1-5 |
| Short-Stay QM Rating | 40 | 1-5 |

## Staffing Hours (per resident per day)

| Field | CSV Index | Notes |
|-------|-----------|-------|
| CNA Hours | 46 | Reported Nurse Aide hrs/res/day |
| LPN Hours | 47 | Reported LPN hrs/res/day |
| RN Hours | 48 | Reported RN hrs/res/day |
| Licensed Staff Hours | 49 | LPN + RN combined |
| Total Nurse Hours | 50 | CNA + LPN + RN combined |
| Weekend Total Nurse Hours | 51 | Weekend total hrs/res/day |
| Weekend RN Hours | 52 | Weekend RN hrs/res/day |
| PT Hours | 53 | Physical Therapist hrs/res/day |

## Case-Mix Adjusted Staffing

| Field | CSV Index | Notes |
|-------|-----------|-------|
| Nursing Case-Mix Index | 60 | Acuity index (higher = sicker residents) |
| CMI Ratio | 61 | Case-mix adjustment ratio |
| Adjusted CNA Hours | 67 | Case-mix adjusted CNA hrs/res/day |
| Adjusted LPN Hours | 68 | |
| Adjusted RN Hours | 69 | |
| Adjusted Total Nurse Hours | 70 | **Best metric for staffing comparisons** |
| Adjusted Weekend Total Hours | 71 | |

## Turnover

| Field | CSV Index | Notes |
|-------|-----------|-------|
| Total Nursing Staff Turnover % | 54 | All nursing staff |
| RN Turnover % | 56 | RN-specific turnover |
| Administrators Who Left | 58 | Count of admin departures |

## Health Inspection Scores

| Field | CSV Index | Notes |
|-------|-----------|-------|
| Cycle 1 Total Health Score | 79 | Most recent inspection |
| Cycle 2/3 Total Health Score | 87 | Prior inspection |
| Total Weighted Health Survey Score | 88 | **Composite score across cycles** |

## Fines & Penalties

| Field | CSV Index | Notes |
|-------|-----------|-------|
| Number of Fines | 90 | |
| Total Amount of Fines ($) | 91 | |
| Number of Payment Denials | 92 | |
| Total Number of Penalties | 93 | Fines + denials combined |

## Flags & Metadata

| Field | CSV Index | Values |
|-------|-----------|--------|
| Special Focus Status | 26 | Y/N/empty |
| Abuse Icon | 27 | Y/N |
| Provider Changed Ownership (12mo) | 29 | Y/N |
| With Resident and Family Council | 30 | Y/N |
| Automatic Sprinkler Systems | 31 | Y/N |
| Chain Name | 18 | |
| Chain ID | 19 | |
| Chain Size (# facilities) | 20 | |
| Chain Avg Overall Rating | 21 | Chain-level 5-star average |
| Ownership Type | 10 | For profit - Corporation, etc. |
| Number of Certified Beds | 11 | |
| Average Residents per Day | 12 | |
| Provider Type | 14 | Medicare, Medicaid, Both |
| Continuing Care Retirement Community | 25 | Y/N |
| Most Recent Health Inspection >2y ago | 28 | Y/N |
| Location | 94 | POINT (lon lat) |

## Quick Download (compact — rating + staffing fields)

```python
import csv, urllib.request, json, time

output_path = r'cms_providers_cache.json'
fields = {
    'ccn': 0, 'name': 1, 'address': 2, 'city': 3, 'state': 4, 'zip': 5,
    'ownership': 10, 'beds': 11, 'avg_residents': 12, 'provider_type': 14,
    'chain': 18, 'sfs': 26, 'abuse': 27,
    'overall_rating': 32, 'health_rating': 34,
    'qm_rating': 36, 'long_qm': 38, 'short_qm': 40,
    'staffing_rating': 42,
    'cna_hours': 46, 'lpn_hours': 47, 'rn_hours': 48,
    'total_staff_hours': 50, 'weekend_hours': 51, 'rn_weekend_hours': 52, 'pt_hours': 53,
    'nurse_turnover': 54, 'rn_turnover': 56, 'admin_turnover': 58,
    'cmi': 60, 'adjusted_total': 70,
    'health_score': 88,
    'fine_count': 90, 'fine_total': 91, 'pay_denials': 92, 'penalties': 93,
    'location': 94
}

all_rows, headers = [], None
for offset in range(0, 14695, 1500):
    url = (f"https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0"
           f"?limit=1500&offset={offset}&format=csv&results=true&count=false&keys=false")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/csv"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        reader = csv.reader(resp.read().decode('utf-8').strip().split('\n'))
        page = list(reader)
        if headers is None:
            headers = page[0]
            all_rows.extend(page[1:])
        else:
            all_rows.extend(page[1:])
    time.sleep(0.5)

data = []
for row in all_rows:
    d = {}
    for key, col_idx in fields.items():
        d[key] = row[col_idx].strip() if col_idx < len(row) else ''
    data.append(d)

with open(output_path, 'w') as f:
    json.dump(data, f)
print(f"Cached {len(data)} CMS providers")
```
