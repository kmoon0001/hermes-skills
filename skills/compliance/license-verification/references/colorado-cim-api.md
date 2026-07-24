# Colorado CIM Open Data API

## Overview
Colorado publishes all professional license data via the Colorado Information Marketplace (CIM) — a Socrata open data portal. Free REST API, no CAPTCHA, includes expiration dates.

## API Endpoint
```
https://data.colorado.gov/resource/7s5z-vewr.json
```

## NHA License Types
- `NHA` — Nursing Home Administrator
- `MSNHA` — Master of Science NHA
- `NHATPE` — NHA Temporary Practice Endorsement
- `TNHAP` — Temporary NHA Permit

## Query Pattern
```python
import urllib.parse, urllib.request, json

type_clause = " OR ".join(f"licensetype='{t}'" for t in ("NHA", "MSNHA"))
where = f"({type_clause}) AND upper(lastname)='{last_name.upper()}'"
params = urllib.parse.urlencode({"$where": where, "$limit": "20"})
url = f"https://data.colorado.gov/resource/7s5z-vewr.json?{params}"

req = urllib.request.Request(url, headers={"Accept": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    data = json.loads(resp.read().decode())
```

## Key Fields
- `licenseexpirationdate` — ISO format `2027-02-28T00:00:00.000` (slice `[:10]`)
- `licensestatusdescription` — Active, Expired, Revoked, Suspended
- `licensenumber`, `lastname`, `firstname`, `city`, `state`

## Gotchas
- Do NOT use `IN()` clause — Socrata doesn't support it. Use `OR`.
- All active NHAs expire on the same date (2027-02-28 in current data).
- Total NHA records: ~3,114 (including expired/revoked).

## Lesson for Other States
When a state portal has CAPTCHA, check for open data portals:
- Search: `site:data.<state>.gov license` or `<state> open data professional license`
- Common platforms: Socrata, CKAN, OpenDataSoft
