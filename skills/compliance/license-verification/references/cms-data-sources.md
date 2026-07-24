# CMS Provider Data Sources

## Provider Info (staffing, ratings, penalties)
- **Dataset:** `4pq5-n9py`
- **URL:** `https://data.cms.gov/provider-data/dataset/4pq5-n9py`
- **CSV:** `https://data.cms.gov/provider-data/sites/default/files/resources/38f631a211bad946a404d39a1c66d599_1778861765/NH_ProviderInfo_May2026.csv`
- **Rows:** 14,651 facilities
- **Key columns:** Overall Rating, Health Inspection Rating, Staffing Rating, QM Rating, RN Hours/Resident/Day, Total Nursing Hours/Resident/Day, Staff Turnover %, RN Turnover %, Admin Turnover, Total Penalties, Total Fines $, Payment Denials, Complaint Deficiencies, Abuse Flag

## Penalties (fines and denials)
- **Dataset:** `g6vv-u9sr`
- **URL:** `https://data.cms.gov/provider-data/dataset/g6vv-u9sr`
- **CSV:** `https://data.cms.gov/provider-data/sites/default/files/resources/c671cdaa1461db5a685367690785fcb3_1778861763/NH_Penalties_May2026.csv`
- **Rows:** 16,572 penalty records
- **Key columns:** CCN, Provider Name, Penalty Date, Penalty Type, Fine Amount, Payment Denial Start Date, Payment Denial Length in Days

## State Open Data APIs
- **Colorado CIM:** `https://data.colorado.gov/resource/7s5z-vewr.json` — licensetype='NHA' (NHA, MSNHA, NHATPE, TNHAP)
- **Washington Socrata:** `https://data.wa.gov/resource/qxh8-f4bd.json` — credentialtype like '%NURSING HOME%'

## Matching Strategy
1. Normalize facility name (strip LLC/Inc/punctuation, lowercase)
2. Try exact match: `{norm_name}|{state_abbrev}` in provider_data
3. Try fuzzy match: substring containment with word overlap scoring
4. Handle both full state names ("Arizona") and abbreviations ("AZ")

## Caching
- Downloads CSVs to `D:/license-verification/cache/`
- Refreshes weekly (7-day cache age)
- One `init_cms_cache()` call at startup loads all data into memory
