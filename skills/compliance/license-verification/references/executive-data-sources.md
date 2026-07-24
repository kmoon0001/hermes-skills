# Executive Data Sources for NHA Facility Monitoring

Beyond license verification, these public data sources provide actionable insights for executives.

## CMS Provider Data (Free, All States)

**URL:** https://data.cms.gov/provider-data/topics/nursing-homes
**Update frequency:** Monthly
**Coverage:** All 15,000+ Medicare-certified nursing homes nationwide

### Datasets:

| Dataset | ID | Key Fields | Value |
|---------|-----|-----------|-------|
| Provider Information | 4pq5-n9py | Five-Star ratings, certified beds, staffing, quality measures | Overall facility quality |
| Penalties | g6vv-u9sr | Fines, payment denials, amounts, dates | Compliance risk |
| Ownership | y2hd-n93e | For-profit/non-profit, parent company, chain | Corporate structure |
| Health Inspections | (part of Provider Info) | Deficiency counts, severity, complaint investigations | Inspection risk |
| MDS Quality Measures | djen-97ju | Clinical outcomes, antipsychotic use, falls | Resident care quality |

### Access:
- CSV downloads available directly from each dataset page
- No API key required for basic queries
- Socrata SODA API for programmatic access

### Recommended columns to add to Excel output:
- CMS Overall Star Rating (1-5)
- CMS Health Inspection Rating
- CMS Staffing Rating
- Penalties in Last 3 Years (count + total amount)
- Administrator Disciplinary Action (from state portals)

### Value for executives:
The intersection of "license expiring soon" + "low CMS rating" + "recent penalties" flags facilities needing immediate attention.

## CMS Data Implementation (`cms_data.py`)

**Module:** `D:/license-verification/cms_data.py`
**Cache:** `D:/license-verification/cache/` (refreshes weekly)

### How it works:
1. `init_cms_cache()` — downloads and caches CMS Provider Info (8.7 MB) and Penalties (2.6 MB) CSVs
2. `get_facility_cms(facility_name, state)` — fuzzy matches by name + state, returns dict with 15 fields
3. Matching: normalizes names (removes LLC/Inc/punctuation), tries exact match first, then substring containment with word overlap scoring

### Usage in verify_all.py:
```python
from cms_data import init_cms_cache, get_facility_cms

# At startup:
init_cms_cache()

# For each facility:
cms = get_facility_cms("Chandler Post Acute", "AZ")
# Returns: cms_overall_rating, cms_staffing_rating, cms_rn_hours, cms_total_penalties, etc.
```

### What the 15 CMS columns prove:

**For "unlicensed administrator" defense:**
- CMS Match (YES/NO) — confirms facility exists in federal records
- Abuse Flag — CMS abuse investigation status

**For "low staffing" defense:**
- CMS Overall/Staffing/Health Star Ratings (1-5)
- RN Hours per Resident per Day (actual staffing number)
- Total Nursing Hours per Resident per Day
- Staff Turnover %, RN Turnover %, Admin Turnover

**For "non-compliance" defense:**
- Total Penalties (count)
- Total Fines $ (dollar amount)
- Payment Denials
- Complaint Deficiencies
- Penalty Details (specific penalties last 3 years)

### Key data points from CMS:
- 14,651 facilities in Provider Info
- 16,572 penalty records
- All Medicare-certified nursing homes nationwide
- Updated monthly

## State Open Data Portals

Many states publish license data via Socrata/CKAN APIs. Pattern for discovery:
```
site:data.colorado.gov <state> license
<state> open data professional license
```

### Currently working:
- Colorado CIM: data.colorado.gov/resource/7s5z-vewr.json (includes disciplinary actions, case numbers)
- Washington Open Data: data.wa.gov/resource/qxh8-f4bd.json (includes action taken, issue dates)

### Fields available beyond status/expiration:
- Issue date / original licensure date (tenure indicator)
- Disciplinary actions / program actions
- License type (NHA vs Provisional vs Temporary — indicates experience level)
