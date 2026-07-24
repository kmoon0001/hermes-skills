---
name: cms-usnews-nursing-home-data
description: >-
  Workflow for looking up nursing home ratings from CMS Nursing Home Compare
  and US News — data download, fuzzy facility matching, and browser-based
  verification when US News blocks automated access.
---

# CMS / US News Nursing Home Data Lookup

Look up nursing home ratings (Skilled Nursing Facilities only) from CMS and US News sources.

## CMS Data (Primary — Always Accessible)

### Download Provider Data

CMS provides 14,695 nursing home records via their API. Data refreshes monthly.

```python
# CSV format with all 99 fields, 1500 records per page
url = "https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0"
params = "?limit=1500&offset=N&format=csv&results=true&count=false&keys=false"
```

Key rating columns (by index in CSV):
- Col 0: CMS Certification Number (CCN)
- Col 1: Provider Name
- Col 3: City/Town
- Col 4: State
- Col 32: Overall Rating (1-5 stars)
- Col 34: Health Inspection Rating
- Col 36: QM Rating
- Col 38: Long-Stay QM Rating
- Col 40: Short-Stay QM Rating
- Col 42: Staffing Rating

### Fuzzy Facility Name Matching

ENSG facility names (e.g. "Citrus Heights Respiratory and Rehabilitation") often differ from CMS names (e.g. "CITRUS HEIGHTS RESPIRATORY AND REHAB"). Use combined Jaccard + SequenceMatcher:

```python
def match_score(name1, name2):
    n1 = re.sub(r'[^a-z0-9\s]', '', name1.lower()).strip()
    n2 = re.sub(r'[^a-z0-9\s]', '', name2.lower()).strip()
    tokens1 = set(n1.split()) - stop_words
    tokens2 = set(n2.split()) - stop_words
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    jaccard = len(intersection) / len(union)
    text_sim = SequenceMatcher(None, n1, n2).ratio()
    return 0.7 * jaccard + 0.3 * text_sim
# Threshold: >= 0.4 = confident match
```

### CMS → US News Mapping (Approximation)

| CMS Overall | Approx US News |
|-------------|---------------|
| 5 | High Performing |
| 3-4 | As Expected |
| 1-2 | As Expected (proxy) |
| empty | Not rated |

**Caveat:** US News uses its own methodology. Cross-tab validation shows ~20% disagreement — 11 CMS 5-star facilities got "As Expected" from US News, and 2 CMS 2-star facilities got "High Performing".

## US News Data (Direct — Headless Batch Script)

### Bot Detection Bypass

US News blocks vanilla headless browsers. **Chrome Canary** with the right flags bypasses it:

- Chrome Canary at: `C:\Users\kevin\AppData\Local\Google\Chrome SxS\Application\chrome.exe`
- `--headless=new` — new headless mode (avoids detection of old headless)
- `--disable-http2` — force HTTP/1.1 to avoid ERR_HTTP2_PROTOCOL_ERROR (Akamai CDN)
- `--disable-blink-features=AutomationControlled`
- `addInitScript` to override `navigator.webdriver` → `undefined`

### Batch Script (`Desktop\usnews_lookup_batch.js`)

The production workflow uses a Node.js/Playwright batch script:

```bash
cd Desktop && node usnews_lookup_batch.js
```

**Input format** (`need_usnews_lookup.txt`): `row|name|city|state|existing_rating`
**Output** (`usnews_lookup_results.csv`): `row|name|city|state|rating`
**State tracking** (`usnews_state.json`): auto-resume on crash/interrupt

**Search URL Pattern:**
```
https://health.usnews.com/best-nursing-homes/search?name=ENCODED_NAME&location=CITY,+ST
```

**Rating extraction** — reads `document.body.innerText` for keywords:
- `'High Performing'` → High Performing
- `'As Expected'` → As Expected
- `'not rated'` or `'insufficient resident outcomes'` → NOT RATED
- `'0 match'` or `'0 nursing homes'` → NOT FOUND
- `'1 match'` with no explicit rating → MATCH_NO_RATING

### Running the Batch

| Aspect | Detail |
|--------|--------|
| Rate | ~55 facilities / 10 min (~11s per facility) |
| Full 336 run | ~60 min |
| Timeout | 7200s for background runs |
| Resume | Auto via usnews_state.json — survives page crashes |
| Retries | 3 per facility with 5s/10s/15s backoff |
| Adaptive delay | 3-6s base + up to 10s extra on consecutive errors |

**Background pattern:**
```bash
node usnews_lookup_batch.js
# Run with background=true, timeout=7200, notify_on_complete=true
```

### Page Crash Handling

Chrome Canary headless can crash periodically (typically after 10-20 lookups). The state file (`usnews_state.json`) saves `lastIndex` after each facility, so re-running the script resumes seamlessly. Delete the state file only to force a full restart.

### Sign-Up Popup Handling (Legacy)

US News shows a "Sign Up for our 3-Day Guide to Medicare" modal on some manual-browse sessions. For the batch script the search results page doesn't trigger this popup.
