# CMS Provider Info — Full Column Reference

Source: `https://data.cms.gov/provider-data/dataset/4pq5-n9py` (Provider Info)
Processing date as of download: 2026-06-01

## 99 Columns (0-indexed CSV)

| Idx | Name | Used for rating? |
|-----|------|-----------------|
| 0 | CMS Certification Number (CCN) | Primary key |
| 1 | **Provider Name** | Name matching target |
| 2 | Provider Address | — |
| 3 | **City/Town** | Geographic filter |
| 4 | **State** | Geographic filter |
| 5 | ZIP Code | — |
| 6 | Telephone Number | — |
| 7-9 | County, Urban | — |
| 10 | Ownership Type | — |
| 11-12 | Certified Beds, Avg Residents/Day | — |
| 14 | Provider Type (Medicare/Medicaid) | — |
| 18 | Chain Name | — |
| 26 | Special Focus Status | Alert flag |
| 27 | Abuse Icon | Alert flag |
| **32** | **Overall Rating** | **Primary CMS rating** |
| **34** | **Health Inspection Rating** | **Sub-rating** |
| **36** | **QM Rating** | **Quality Measures** |
| **38** | **Long-Stay QM Rating** | **Sub-rating** |
| **40** | **Short-Stay QM Rating** | **Sub-rating** |
| **42** | **Staffing Rating** | **Sub-rating** |
| 46-53 | Staffing hours (reported/adjusted) | — |
| 54-59 | Turnover metrics | — |
| 60-71 | Case-mix adjusted data | — |
| 73-88 | Health inspection history | — |
| 90-93 | Penalties/fines | — |
| 94 | Location (lat,lng string) | — |
| 98 | **Processing Date** | **Always check — expect monthly refresh** |

## Star Rating Scale (1-5)
- 1 = Much below average
- 2 = Below average
- 3 = Average
- 4 = Above average
- 5 = Much above average
- Empty = Not enough data

## US News 2026 Methodology Notes

From observing 43 pre-filled (real) US News ratings vs CMS data across 375 ENSG Skilled Nursing facilities:

### What US News weights HEAVILY:
- **Quality Measures (QM)**: Nearly every "High Performing" facility has QM=4 or 5.
- Facilities with CMS Overall=4 but QM=5 often got "High Performing" from US News.
- Facilities with CMS Overall=5 but QM=3 sometimes got downgraded to "As Expected".

### What US News appears to de-emphasize:
- **Staffing Rating**: Several "High Performing" facilities had Staffing=1 or 2 (CMS 5-star Overall with low staffing).
- **Health Inspection Rating**: Similar pattern — High Performing with Health Insp=2 or 3.

### Anomalies observed:
- "Rock Creek of Ottawa" (CMS Overall=2, Health=2, Staffing=1, QM=5) → **High Performing** — US News clearly prioritized the QM rating.
- "Legend Oaks San Antonio" (CMS Overall=2, Health=2, Staffing=3, QM=3) → **High Performing** — unexplained outlier.
- "West Bend Care Center" (CMS Overall=5, QM=4) → **As Expected** — US News disagreed with CMS.

### Conclusion:
US News 2026 is NOT a simple remapping of CMS 5-star. Their proprietary formula weights QM more heavily and applies different thresholds. The CMS proxy fill is directional (good for broad strokes) but individual facility ratings should be verified against the actual US News site if precision matters.
