---
name: cms-usnews-nursing-home-data
description: >-
  Workflow for looking up nursing home ratings from CMS Nursing Home Compare
  and US News — data download, fuzzy facility matching, browser scrape,
  accuracy documentation, and discrepancy analysis.
---

# CMS / US News Nursing Home Data Lookup

Look up nursing home ratings (Skilled Nursing Facilities only) from CMS and US News sources. Covers full pipeline: data download → fuzzy matching → US News scraping → retry → merge → spreadsheet assembly → accuracy documentation.

## CMS Data (Primary — Always Accessible)

### Download Provider Data

CMS provides 14,695 nursing home records via their API. Data refreshes monthly.

```python
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

### CMS Matching Priority

**Primary rule:** if the source workbook already contains a CMS Certification Number (CCN), use that CCN as the primary key and rebuild all CMS-derived columns by exact CCN lookup. Do **not** trust fuzzy name matching over a source CCN. Normalize CCNs to 6 digits before lookup.

Only use fuzzy facility-name matching when the source record has no CCN. ENSG facility names differ from CMS names, and repeated brand patterns (`Legend Oaks`, `Healthcare Resort`, `Trucare`, renamed facilities) can produce plausible but wrong fuzzy matches.

```python
def norm_ccn(x):
    s = str(x or '').strip()
    if s.endswith('.0'):
        s = s[:-2]
    s = ''.join(ch for ch in s if ch.isdigit())
    return s.zfill(6) if s else ''
```

Fallback fuzzy matching: use combined Jaccard + SequenceMatcher with threshold >= 0.4, but flag those rows as approximate and put them in an audit sheet.

```python
def match_score(name1, name2):
    # strip punctuation, lowercase, tokenize, remove stop words
    # 0.7 * jaccard + 0.3 * SequenceMatcher ratio
```

See `references/ensg-usnews-ccn-rebuild-2026-07.md` for the Ensign workbook lesson where exact CCN rebuild corrected 21 fuzzy-matched CCNs.

See `references/ensg-authoritative-evidence-package-2026-07.md` for the evidence-only response-package pattern: primary-source dossier, printable brief, talking points, dependency-free SVG charts, separate lawful patient/staff justice guide, and the off-record quarantine pattern for rumors/personal-life dirt/unverified fraud wording.

### CMS → US News Mapping (Approximation)

| CMS Overall | Approx US News |
|-------------|---------------|
| 5 | High Performing |
| 3-4 | As Expected |
| 1-2 | As Expected (proxy) |
| empty | Not rated |

**Caveat:** ~20% disagreement — this is expected. US News uses its own methodology.

## US News Data (Direct — Headless Batch Script)

### Bot Detection Bypass

Chrome Canary at `C:\Users\kevin\AppData\Local\Google\Chrome SxS\Application\chrome.exe` with flags: `--headless=new`, `--disable-http2`, `--disable-blink-features=AutomationControlled`, and `navigator.webdriver` override.

### Batch Script (`Desktop\usnews_lookup_batch.js`)

Input: `row|name|city|state[|existing_rating]`, Output: `row|name|city|state|rating`, State tracking via `usnews_state.json`.

Search URL: `https://health.usnews.com/best-nursing-homes/search?name=NAME&location=CITY,+ST`

Rating extraction from `document.body.innerText`: High Performing, As Expected, NOT FOUND, NOT RATED, MATCH_NO_RATING.

### Running the Batch

Run in foreground chunks (background kills Chrome on Windows). Resume automatically via state file.

```bash
cd Desktop && timeout 600 node usnews_lookup_batch.js
```

### Targeted Retry for NOT FOUND

When batch finishes with NOT FOUND entries, create a focused retry that tries BOTH the spreadsheet name and the CMS provider name:
- 5 retries per name, 30s page timeout, 4s page wait
- CMS provider name is column 9 in the ENSG source spreadsheet
- If alt name resolves it → scraper miss, update rating
- If both return 0 matches and CCN is valid → genuinely NOT RATED by US News

Expected recovery: ~2 of every 16 NOT FOUND recover with the CMS provider name.

## Post-Scrape: Accuracy & Discrepancy Analysis

### CMS Data Verification

After scrape, verify CMS data against the live CMS API. Download current `4pq5-n9py` CSV and rebuild by exact source CCN whenever possible.

**Best practice learned Jul 2026:** For Ensign-style source files with a CMS CCN column, do a full CCN rebuild rather than a spot-check:
- Normalize source CCN to 6 digits.
- Pull the full CMS Provider Data dataset.
- Rebuild every CMS-derived field from the live CMS row for that CCN.
- Add a `CMS Verification Audit` sheet with original/source CCN, old workbook CCN, rebuilt CCN, CMS provider name/city/state, status, changed-field count, and notes.
- Set `Data Confidence` to `✅ Verified by CMS CCN` only when exact CCN lookup succeeds.

**Known Ensign workbook result** (verified Jul 2026): exact CCN rebuild verified 336/336 facilities, corrected 21 old fuzzy-matched CCNs, and refreshed/corrected/normalized 1,318 CMS cells. See `references/ensg-usnews-ccn-rebuild-2026-07.md`.

### Per-Column Reliability Guide

| Reliability | Columns | Reason |
|-------------|---------|--------|
| ✅ Reliable | US News Rating, Row, Facility Name, City, State, Ownership, Special Focus, Abuse Flag, CMS CCN, CMS ratings/fields rebuilt by exact source CCN | Direct scrape or exact CMS CCN lookup |
| ⚠️ Source caveat | Staffing hours, turnover, fines, penalties | The workbook can match CMS perfectly, but PBJ staffing/turnover is self-reported and fines/penalties can lag or be appealed |
| ⚠️ Approximate | Rows without source CCN that required fuzzy name matching | Wrong facility may be linked; put these rows in an audit sheet and verify manually |
| ❌ Verify | Empty staffing cells, missing CCN, source CCN absent from current CMS API | No PBJ submission, not Medicare/Medicaid certified, or source/refresh mismatch |

### Discrepancy Categorization

After batch completes, compare CSV against original `need_usnews_lookup.txt`. Two categories:

**1. Methodology difference** (yellow-flag): Original said "As Expected" but US News says "High Performing" (or vice versa). US News uses its own methodology — CMS 3★ with strong QM may get High Performing. ~20% of facilities. Normal.

**2. Facility not listed** (red-flag): Any original rating → NOT FOUND. Valid CCN, real SNF, but US News doesn't rank it (insufficient outcomes data or not in sample). Can't be recovered via retry. ~4% of facilities.

## Spreadsheet Structure (Final Output)

The assembled XLSX at `Desktop\US News Nursing Home Ratings 2026.xlsx` should have 6 sheets:

1. **Summary** — Clean dashboard: verification counts, US News counts, CMS overall counts, risk/counter-argument flags, state breakdown
2. **Facility Ratings** — 336 facilities, 37 columns, color-coded with Data Confidence column
3. **Discrepancies** — 45 mismatch entries with category + explanation (8 columns)
4. **CMS Verification Audit** — Row-level transparency for exact CCN rebuild: source CCN, old workbook CCN, rebuilt CCN, CMS provider name, status, changed fields
5. **Action Items** — Priority compliance/operational flags regenerated from corrected CMS data
6. **Data Sources & More** — Full per-column methodology, transparency docs, source caveats, short-seller context

### Data Confidence column logic

Prefer exact source CCN rebuild:
- Source CCN exists and current CMS API contains it → **✅ Verified by CMS CCN** (green). This is the target state.
- Source CCN missing or not found in current CMS API → **⚠️ Verify manually** (yellow/red depending on severity). Use Medicare Care Compare / CMS Provider Data search.
- Fuzzy name match used because no source CCN exists → **⚠️ Approximate** (yellow). Put the row in `CMS Verification Audit` and verify manually before using in disputes.

If the workbook already has a historical `CMS Match Score` from fuzzy matching, treat it as legacy metadata only after exact CCN rebuild. Set it to 1.0 for rows rebuilt by exact CCN.

## Desktop Cleanup After Batch Completion

When the user can see and confirm the final current workbook, keep an obvious visible copy on Desktop:

- `OPEN THIS - US News Nursing Home Ratings 2026.xlsx`

Archive old work artifacts instead of permanently deleting them. Use a dated folder such as:

- `Documents/Hermes Desktop Cleanup Archive/<date>-usnews-and-work-artifacts/`

Move old copies/backups/scripts/test files there and write `cleanup_manifest.json`. Include hashes for the kept current workbook and moved files where practical. Do not delete the Excel lock file `~$OPEN THIS...xlsx` while the workbook is open; it disappears when Excel closes.

Typical archive candidates:
- old workbook names/backups: `US News Nursing Home Ratings 2026.xlsx`, `*.backup-before-*.xlsx`
- source/intermediate files after final workbook is delivered: `need_usnews_lookup.txt`, `usnews_lookup_final.csv`, retry result CSVs/logs
- scraper/test scripts: `usnews_lookup_batch.js`, `usnews_retry_*`, `test_usnews*`, `test_az*`
- temp rebuild scripts: `add_documentation_to_xlsx.py`, `rebuild_spreadsheet.py`, `rebuild_cms_by_ccn.py`, `regenerate_summary_action_items.py`, `fix_methodology_text.py`
- scraper dependencies in Desktop root: `node_modules`, `package.json`, `package-lock.json`, `.playwright-cli`

Only archive broad unrelated project folders when the user explicitly asks to clean old artifacts from other work and the folder is clearly a backup/output folder. Keep active/current project folders.
