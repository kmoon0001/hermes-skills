---
name: cms-data-matching
description: "Match ENSG/healthcare facility names against CMS Nursing Home Compare data. Download provider records with star ratings, match via fuzzy name tokens, and map CMS ratings to US News categories. Covers the CMS API provider info dataset (14,695 records), pagination, and the CMS-to-USNews 2026 cross-tab."
---

# CMS Nursing Home Compare Data Matching

Look up CMS 5-star ratings (Overall, Health Inspection, Staffing, Quality Measures) for any US skilled nursing facility and optionally map to approximate US News 2026 rating labels.

## CMS API Endpoint

Base: `https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0`

Key params:
- `limit` (max 1500), `offset` — paginate through all ~14,695 records
- `format=csv` — returns clean CSV with headers; `format=json` with `rowIds=true` returns dicts
- `count=false` / `results=true` / `schema=false` / `keys=false`

Rating field columns (0-indexed CSV):
| Index | Field |
|-------|-------|
| 0 | CMS Certification Number (CCN) |
| 1 | Provider Name |
| 3 | City/Town |
| 4 | State |
| 32 | Overall Rating (1-5) |
| 34 | Health Inspection Rating |
| 36 | QM Rating |
| 38 | Long-Stay QM Rating |
| 40 | Short-Stay QM Rating |
| 42 | Staffing Rating |

Processing date field is at index 98 — always verify data is current (expect ~monthly refresh).

## Download Pattern (Python)

```python
import urllib.request, csv, time

total = 14695
page_size = 1500
for page in range((total + page_size - 1) // page_size):
    url = (f"https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0"
           f"?limit={page_size}&offset={page * page_size}&format=csv"
           f"&results=true&count=false&keys=false")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8')
        # parse CSV rows, skip header on page 0, keep data rows from all pages
    time.sleep(0.5)  # rate limiting
```

## Name Matching

Facility names in spreadsheets may differ from CMS names. Use state-level matching (not city-level) because CMS may list different cities for the same facility.

### Fuzzy matching algorithm:
1. Normalize: strip punctuation, lowercase, collapse whitespace
2. Tokenize into word sets, remove stop words (`the`, `and`, `of`, `at`, `for`, `a`, `an`, `in`, `to`, `llc`, `inc`, `lp`, `&`)
3. Score = 0.7 × Jaccard(token_sets) + 0.3 × SequenceMatcher(full_text)
4. Threshold: >= 0.5 high confidence, 0.35-0.5 low confidence (flag in NOTES column), < 0.35 no match

```python
from difflib import SequenceMatcher

def match_score(name1, name2):
    # Returns 0.0-1.0 score between two facility names
    n1 = re.sub(r'[^a-z0-9\s]', '', name1.lower()).strip()
    n2 = re.sub(r'[^a-z0-9\s]', '', name2.lower()).strip()
    n1 = re.sub(r'\s+', ' ', n1)
    n2 = re.sub(r'\s+', ' ', n2)
    t1 = set(n1.split()) - stop_words
    t2 = set(n2.split()) - stop_words
    if not t1 or not t2:
        return 0.0
    jaccard = len(t1 & t2) / len(t1 | t2)
    text = SequenceMatcher(None, n1, n2).ratio()
    return 0.7 * jaccard + 0.3 * text
```

## CMS → US News 2026 Mapping

This is an **approximation only** — US News uses its own proprietary methodology.

| CMS Overall | US News 2026 label |
|-------------|-------------------|
| 5 | "High Performing" (87% match rate in observed data) |
| 4 | Usually "As Expected" (some "High Performing" with high QM) |
| 3 | "As Expected" |
| 2 | "As Expected" (rarely "High Performing" if QM=5) |
| 1 | "As Expected" |
| empty | "This home was not rated due to insufficient resident outcomes data."|

### Cross-tab from 375 ENSG skilled nursing facilities:

| US News | CMS 5★ | CMS 4★ | CMS 3★ | CMS 2★ | CMS 1★ |
|---------|--------|--------|--------|--------|--------|
| High Performing | 71 | 7 | 2 | 2 | 0 |
| As Expected | 11 | 72 | 89 | 77 | 44 |

**Key finding:** ~20% of facilities have different CMS vs US News ratings. If precise US News data is needed, prefer direct site access (see Pitfalls and references/usnews-via-cua-driver.md). For headless batch scraping, see the `nursing-home-data-lookup` skill (same category) and `web-scraping-anti-detection` skill (bypass technique + retry patterns for MAX_RETRIES and NOT FOUND).

## Pitfalls

- **US News site blocks automated tools** — health.usnews.com rejects Playwright browsers and curl with infinite SSL renegotiation. It does load from a real Chrome Canary browser with a residential IP (Cox). To use the user's Chrome, cua-driver can navigate it, but CDP (`--remote-debugging-port`) is needed for execute_javascript. Without CDP, only screenshot-based reading works.
- **City name differences** — CMS may list a facility in "Mt Pleasant" when the spreadsheet says "Mount Pleasant", or "Seattle" vs "Shoreline". Always match by state + fuzzy name, not city.
- **Empty CMS rating** — If Overall Rating is empty or "Not Available", the facility has insufficient resident outcomes data. Mark as "not rated" in the spreadsheet.
- **Non-SNF facilities** — CMS data only covers Medicare/Medicaid-certified skilled nursing facilities. Assisted Living, Independent Living, Outpatient Therapy, and Service Center rows will not match.
- **API properties filter causes 400 error** — Don't use the `properties` query parameter; download full records and extract only needed columns after parsing.
- **NOT FOUND ≠ scraper failure** — When a US News batch scrape returns NOT FOUND for a facility with a valid CMS CCN, the facility is often genuinely not listed by US News (not a scraper miss). US News only rates ~14,500 of 15,500+ Medicare-certified SNFs. Before concluding it's a missed entry, retry with the CMS provider name as an alternative search — the operational name in the spreadsheet may differ from US News's indexed name. See `scripts/not-found-retry-with-alt-names.cjs` under the `cms-usnews-nursing-home-data` skill for the retry pattern.
