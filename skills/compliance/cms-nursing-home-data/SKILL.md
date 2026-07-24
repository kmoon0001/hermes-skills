---
name: cms-nursing-home-data
description: Download, query, and match facilities against CMS Nursing Home Compare provider data. Enrich spreadsheets with CMS overall ratings, health inspection scores, and staffing data. Fuzzy name matching across 14,695 US nursing homes.
category: compliance
tags:
  - cms
  - nursing-home-compare
  - medicare
  - provider-data
  - excel-enrichment
  - fuzzy-matching
---

# CMS Nursing Home Compare Data

Download and match facilities against the [CMS Nursing Home Compare](https://data.cms.gov/provider-data/dataset/4pq5-n9py) provider dataset (14,695 records covering all US states/territories).

**Related:** When investigating short-seller reports, activist investor attacks, or regulatory accusations against SNF operators, see `references/short-seller-backgrounding.md` — a guide for backgrounding the accuser, triangulating claims against CMS data, structuring counter-narratives, and identifying credibility flags.

## API Access

**Endpoint:** `https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0`

**Format:** Use `format=csv` for named columns, `format=json` for positional arrays.

**Pagination:** Max 1,500 records per page. 10 pages for the full dataset (~14,695 records).

**Rate limit:** ~500ms between calls (empirically safe).

**CSV column index for Overall Rating: 32** (0-indexed).

## Direct CSV Download (Preferred for Bulk Work)

**This is the fastest approach for any task involving 3+ facilities.** The full dataset is ~9 MB as a single CSV. One download, one pass — no pagination, no rate limiting.

**URL:** `https://data.cms.gov/provider-data/sites/default/files/resources/bc7015f6a981fa7e209809e021f8f0cc_1781194538/NH_ProviderInfo_Jun2026.csv`

The URL changes monthly (when CMS releases new data). To get the current URL:
1. Visit https://data.cms.gov/provider-data/dataset/4pq5-n9py
2. Click the "Download full dataset (CSV)" button
3. Copy its link

### Example — download and parse with DictReader (recommended)

CSV headers are human-readable column names (e.g. `"CMS Certification Number (CCN)"`, `"Overall Rating"`, `"Staffing Rating"`). Use `csv.DictReader` for named access:

```python
import csv, urllib.request

url = ("https://data.cms.gov/provider-data/sites/default/files/resources/"
       "bc7015f6a981fa7e209809e021f8f0cc_1781194538/NH_ProviderInfo_Jun2026.csv")

with urllib.request.urlopen(url, timeout=60) as resp:
    reader = csv.DictReader(r.decode('utf-8') for r in resp)

    for row in reader:
        ccn = row.get("CMS Certification Number (CCN)", "")
        if ccn == target_ccn:
            overall = row.get("Overall Rating", "")
            staffing = row.get("Staffing Rating", "")
            health_insp = row.get("Health Inspection Rating", "")
            qm = row.get("QM Rating", "")
            cna = row.get("Reported Nurse Aide Staffing Hours per Resident per Day", "")
            rn = row.get("Reported RN Staffing Hours per Resident per Day", "")
            fines = row.get("Number of Fines", "")
            fine_amt = row.get("Total Amount of Fines in Dollars", "")
            turnover = row.get("Total nursing staff turnover", "")
```

**Key column names for DictReader** (stable across releases):
- `"CMS Certification Number (CCN)"` — unique identifier
- `"Overall Rating"`, `"Health Inspection Rating"`, `"Staffing Rating"`, `"QM Rating"`
- `"Reported Nurse Aide Staffing Hours per Resident per Day"`
- `"Reported RN Staffing Hours per Resident per Day"`
- `"Reported Total Nurse Staffing Hours per Resident per Day"`
- `"Total nursing staff turnover"`, `"Registered Nurse turnover"`
- `"Number of Fines"`, `"Total Amount of Fines in Dollars"`
- `"Number of Payment Denials"`, `"Total Number of Penalties"`
- `"Number of Certified Beds"`, `"Average Number of Residents per Day"`
- `"Ownership Type"`, `"Chain Name"`
- `"Processing Date"` — confirms data vintage (e.g. `2026-06-01`)

### Example — paginated API (fallback, for queries under 3 facilities)

Use only when you cannot or should not download the full CSV (CDN blocked, bandwidth constrained, need just 1-2 records). Max 1,500 per page.

```python
import csv, urllib.request, json, time

page_size = 1500
total = 14695
num_pages = (total + page_size - 1) // page_size
all_rows = []

for page in range(num_pages):
    offset = page * page_size
    url = (f"https://data.cms.gov/provider-data/api/1/datastore/query/4pq5-n9py/0"
           f"?limit={page_size}&offset={offset}&format=csv&results=true&count=false&keys=false")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "text/csv"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read().decode('utf-8')
        reader = csv.reader(content.strip().split('\n'))
        page_rows = list(reader)
        if page == 0:
            headers = page_rows[0]
            all_rows.extend(page_rows[1:])
        else:
            all_rows.extend(page_rows[1:])
    time.sleep(0.5)
```

**Pitfall:** The API's `filter` parameter does NOT work via GET query string or POST body for CCN filtering — it ignores the condition and returns the first result regardless. Always download the file and search locally.

## Fuzzy Name Matching

ENSG facility names in Excel spreadsheets often differ from CMS provider names. Use this algorithm:

1. **Normalize**: lowercase, strip punctuation, collapse whitespace
2. **Tokenize**: split on whitespace, remove stop words (`the`, `and`, `of`, `at`, `for`, `a`, `an`, `in`, `to`, `llc`, `inc`, `lp`, `&`)
3. **Score**: weighted blend of Jaccard token similarity (70%) and SequenceMatcher text ratio (30%)
4. **Threshold**: ≥ 0.4 for auto-match, ≥ 0.3 for low-confidence with note

```python
from difflib import SequenceMatcher
import re

def match_score(name1, name2):
    n1 = re.sub(r'[^a-z0-9\s]', '', name1.lower().strip())
    n2 = re.sub(r'[^a-z0-9\s]', '', name2.lower().strip())
    n1 = re.sub(r'\s+', ' ', n1)
    n2 = re.sub(r'\s+', ' ', n2)
    t1 = set(n1.split()) - {'the','and','of','at','for','a','an','in','to','llc','inc','lp','&'}
    t2 = set(n2.split()) - {'the','and','of','at','for','a','an','in','to','llc','inc','lp','&'}
    inter = t1 & t2
    union = t1 | t2
    if not union:
        return 0.0
    jaccard = len(inter) / len(union)
    text = SequenceMatcher(None, n1, n2).ratio()
    return 0.7 * jaccard + 0.3 * text
```

### Match Strategy (by priority)

0. **CCN lookup (exact)** — If the spreadsheet has a "CMS CCN" column, match directly by `CMS Certification Number (CCN)`. This is 100% accurate and avoids all fuzzy matching. Simply create a dict keyed by CCN from the CSV and look up each row. Write `CMS Match Score = 1` for exact CCN matches.

1. **State + exact city match** — group CMS providers by `{State}|{city_lower}`, then fuzzy-score within group
2. **State-only fallback** — when city names differ (e.g. "Mt Pleasant" vs "Mount Pleasant", "Shoreline" vs "Seattle"), search all providers in the same state
3. **Flag low confidence** — write the CMS match name + score to a NOTES column when score < 0.5

## State Name → Abbreviation Conversion

US News data uses full state names (`"Utah"`, `"Arizona"`) while CMS uses 2-letter codes (`"UT"`, `"AZ"`). Always convert before matching:

```python
STATE_ABBR = {
    'alabama':'AL','alaska':'AK','arizona':'AZ','arkansas':'AR','california':'CA',
    'colorado':'CO','connecticut':'CT','delaware':'DE','florida':'FL','georgia':'GA',
    'hawaii':'HI','idaho':'ID','illinois':'IL','indiana':'IN','iowa':'IA',
    'kansas':'KS','kentucky':'KY','louisiana':'LA','maine':'ME','maryland':'MD',
    'massachusetts':'MA','michigan':'MI','minnesota':'MN','mississippi':'MS',
    'missouri':'MO','montana':'MT','nebraska':'NE','nevada':'NV','new hampshire':'NH',
    'new jersey':'NJ','new mexico':'NM','new york':'NY','north carolina':'NC',
    'north dakota':'ND','ohio':'OH','oklahoma':'OK','oregon':'OR','pennsylvania':'PA',
    'rhode island':'RI','south carolina':'SC','south dakota':'SD','tennessee':'TN',
    'texas':'TX','utah':'UT','vermont':'VT','virginia':'VA','washington':'WA',
    'west virginia':'WV','wisconsin':'WI','wyoming':'WY','district of columbia':'DC',
}
def to_state_abbr(s):
    s = s.strip().lower()
    if len(s) == 2: return s.upper()
    return STATE_ABBR.get(s, s[:2].upper())
```

## Full-Download + JSON Cache Pattern

For enrichment workflows (staffing hours, turnover, fines), download ALL 99 columns once and cache as JSON. This avoids re-downloading the 14K-record dataset on every run. See `references/field-index-map.md` for the complete column map with all 36 commonly-used fields.

## CMS National Averages for Benchmarking

When comparing a portfolio against national benchmarks, use these 2025-2026 reference values:

| Metric | National Avg |
|--------|-------------|
| CNA Hours/Res/Day | 2.3 |
| RN Hours/Res/Day | 0.7 |
| Total Nurse Hours/Res/Day | 3.8 |
| Total Nursing Staff Turnover | 46.5% |
| RN Turnover | 45.8% |

## Portfolio Analysis (Defensive/Quality Evidence)

Use the enriched spreadsheet to prove quality of care and refute exploitation claims:

1. **Staffing vs national averages** — compare your portfolio's CNA/RN/total hours against CMS benchmarks. Green = above avg, red = below.
2. **Turnover analysis** — identify facilities with below-national-average turnover as retention success stories.
3. **Rating × Staffing correlation** — prove that High Performing facilities have higher staffing ratings (avg ~3.5 stars vs ~2.8 for As Expected).
4. **Action items sheet** — rank facilities by severity (combined flags: 1-star staffing, abuse icon, SFS, fines >$50K, payment denials).

## Rating Mapping

CMS Overall Rating (1-5 stars) → approximate US News 2026 category:

| CMS Stars | US News Label |
|-----------|---------------|
| 5 | High Performing |
| 3-4 | As Expected |
| 1-2 | As Expected (proxy) |
| empty/NA | This home was not rated due to insufficient resident outcomes data. |

**Important caveat:** US News 2026 uses its own proprietary methodology combining CMS data with additional criteria. The CMS-to-US-News mapping above is an approximation. Validation against pre-existing US News ratings shows ~20% disagreement — do not represent as authoritative US News data.

## Writing Back to Spreadsheet

Use `openpyxl` to write values and flag low-confidence matches:

```python
ws.cell(row=row, column=1).value = usnews_label
if score < 0.5:
    note = f"Low confidence match: CMS '{cms_name}'; Score: {score:.2f}"
    ws.cell(row=row, column=2).value = note
```

## Interactive Dashboard Visualization

After enrichment, you can generate a self-contained HTML portfolio intelligence dashboard (works from `file://`, no server needed):

- Charts: rating distribution, state comparison, HP×staffing scatter, ownership breakdown
- Regional analysis: West/Midwest/South/Northeast KPI cards, state table, city trends
- **Knowledge graph**: D3.js force-directed network — each cluster = facilities sharing same state, similar staffing (±1★), similar turnover (±15%), same ownership, same US News tier
- Full facility table with search/sort/filter
- Action items ranked by severity

### Workflow

1. Download + match facilities to CMS (see above)
2. Enrich each facility with all CMS fields
3. Compute state/region/ownership aggregate stats
4. Run tier comparisons (HP vs AE across staffing, turnover, CNA, RN, health scores)
5. Cluster facilities by shared-pattern similarity (5-dimension matching)
6. Serialize everything to JSON and embed into the HTML
7. Open in browser

### Template

`templates/portfolio-dashboard.html` — complete working implementation (336 facilities, 6 tabs, embedded data). Adaptation guide inside.

## Reference Files

This skill ships with references, templates, and scripts:

- **`references/field-index-map.md`** — Complete CSV column index map for all 99 fields, plus a compact-download script.
- **`references/usnews-vs-cms-cross-tab.md`** — Cross-tabulation of US News 2026 ratings vs CMS Overall Rating.
- **`references/hunterbrook-short-seller-defense.md`** — Evidence-backed rebuttal to Hunterbrook Capital's Ensign Group short report: methodology flaws, OIG PBJ error data, external source validation, CMS data defense, court-ready evidence chain.
- **`references/short-seller-backgrounding.md`** — Guide for investigating the accuser and claims when a short-seller or activist attacks a SNF operator (Hunterbrook, Hindenburg, etc.). Covers backgrounding playbook, common narratives, counter-data patterns, credibility flags, and key research sources.
- **`templates/portfolio-dashboard.html`** — Interactive HTML dashboard template (see above).
- **`scripts/verify-ccns.py`** — Standalone verification script: pass a spreadsheet or inline CCN list; downloads live CMS CSV, compares every field, outputs a side-by-side report. Usage: `python3 scripts/verify-ccns.py --ccn-list 065404 055894 055744` or `python3 scripts/verify-ccns.py input.xlsx --sheet "Facility Ratings" --ccn-col "CMS CCN"`.

Load with `skill_view(name='cms-nursing-home-data', file_path='references/field-index-map.md')`.

## Raters: Loading This Skill

When you load this skill, immediately check `references/field-index-map.md` for the current column indices — they are stable across CMS data releases but always good to verify.

## Pitfalls

- **City name differences** — CMS may use "Mt Pleasant" where spreadsheet has "Mount Pleasant", or "Seattle" where the facility is in "Shoreline". Always fall back to state-only search when state+city returns no match above threshold.
- **Name word-order differences** — "Care and Rehabilitation Center" vs "Rehabilitation and Care Center" have low Jaccard overlap. The SequenceMatcher component helps bridge these.
- **Non-SNF types have no ratings** — CMS only rates Medicare/Medicaid-certified skilled nursing facilities. Assisted Living, Independent Living, Outpatient Therapy, Service Centers, etc. should be left blank.
- **JSON format returns positional arrays** — use CSV format for named columns (header row included). `rowIds=true` does NOT add dict keys as expected — stick with CSV.
- **Properties filter causes HTTP 400** — do NOT use the `properties` query parameter; download the full row and extract needed columns by index.
- **openpyxl Font(family=) expects a number** — use `name='Consolas'` not `family='Consolas'`. The `family` parameter requires a numeric font family code (e.g. 1=serif, 2=serif, 3=monospace), not a font name string.
- **Excel file lock** — if the target `.xlsx` is open in Excel, `openpyxl` raises `PermissionError: [Errno 13]`. Close Excel first (`taskkill /F /IM EXCEL.EXE`) or save to a temp path and swap.
