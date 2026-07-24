# Executive Defense Data Sources

## Use Case
Defend against accusations of:
1. Running buildings with unlicensed administrators
2. Low staffing / non-compliance on staffing requirements

## Data Sources

### CMS Provider Data (FREE, no auth)
- **Provider Info:** `data.cms.gov/provider-data/dataset/4pq5-n9py`
  - 14,651 facilities nationwide
  - Updated monthly
  - Fields: star ratings, staffing hours, turnover, penalties, bed count, ownership
- **Penalties:** `data.cms.gov/provider-data/dataset/g6vv-u9sr`
  - 16,572 penalty records
  - Fields: penalty date, type, fine amount, payment denial dates

### State Open Data APIs (FREE, no CAPTCHA)
- **Colorado CIM:** `data.colorado.gov/resource/7s5z-vewr.json`
  - License type, status, expiration, disciplinary actions, case numbers
- **Washington Open Data:** `data.wa.gov/resource/qxh8-f4bd.json`
  - 2.42M rows, daily updates, includes expiration dates

## Key CMS Columns for Defense

### Staffing Defense
| Column | What It Proves |
|--------|---------------|
| `Reported RN Staffing Hours per Resident per Day` | Actual RN staffing level |
| `Reported Total Nurse Staffing Hours per Resident per Day` | Total nurse staffing |
| `Staffing Rating` (1-5) | CMS's staffing assessment |
| `Total nursing staff turnover` | Staffing stability |
| `Registered Nurse turnover` | RN-specific turnover |
| `Number of administrators who have left` | Admin turnover |

### Compliance Defense
| Column | What It Proves |
|--------|---------------|
| `Overall Rating` (1-5) | CMS overall quality score |
| `Health Inspection Rating` (1-5) | Inspection compliance |
| `Number of Fines` | CMS enforcement history |
| `Total Amount of Fines in Dollars` | Financial penalties |
| `Number of Payment Denials` | CMS payment enforcement |
| `Total Number of Penalties` | Total enforcement actions |
| `Rating Cycle 1 Number of Complaint Health Deficiencies` | Complaint history |
| `Abuse Icon` | Abuse investigation flag |

### License Defense
| Source | What It Proves |
|--------|---------------|
| State scraper result | Active/Expired/Revoked status |
| Expiration date | License is current |
| License number | Verifiable credential |
| Disciplinary action | Clean license history |

## CMS Star Rating Thresholds
- 5 stars = Top 10% nationally
- 4 stars = Above average
- 3 stars = Average
- 2 stars = Below average
- 1 star = Bottom 10% nationally

**For defense:** A facility with 3+ stars overall and 3+ stars staffing is above the national median. Below 3 stars on staffing is a risk indicator.

## Fuzzy Matching for CMS Data
CMS uses different facility names than the ENSG Excel. Matching strategy:
1. Normalize both names (lowercase, strip LLC/Inc/punctuation, collapse spaces)
2. Try exact match on normalized name + state
3. Fall back to substring containment (one name contains the other)
4. Score by word overlap (intersection of word sets)
5. Threshold: 2+ matching words = credible match
