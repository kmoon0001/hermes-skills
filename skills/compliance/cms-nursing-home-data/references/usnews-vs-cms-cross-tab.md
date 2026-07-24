# US News 2026 vs CMS Rating Cross-Reference

Validation results from an ENSG facility list of 450 skilled nursing facilities,
comparing US News 2026 ratings against CMS 5-star Overall Ratings.

## Cross-Tabulation

Pre-filled US News ratings (43) vs CMS Overall Rating for the same facilities:

| US News Label | CMS 5★ | CMS 4★ | CMS 3★ | CMS 2★ | CMS 1★ | Total |
|---------------|--------|--------|--------|--------|--------|-------|
| **High Performing** | **71** | 7 | 2 | 2 | 0 | **82** |
| **As Expected** | 11 | 72 | 89 | 77 | 44 | **293** |
| **Not Rated (insufficient data)** | 0 | 0 | 2 | 0 | 0 | **3** |

## Key Observations

1. **87% of High Performing facilities have CMS 5★** — But not all CMS 5★ are High Performing
2. **11 CMS 5★ facilities were rated As Expected** by US News — US News is more selective
3. **9 CMS 3-4★ facilities were rated High Performing** — US News rewards high Quality Measures even with lower inspection/staffing scores
4. **2 CMS 2★ facilities were rated High Performing** — "Rock Creek of Ottawa" (qm=5) and "Legend Oaks San Antonio" (qm=3). Both have high QM ratings which US News weights heavily.
5. **Not Rated facilities** — typically have empty or missing CMS rating fields (new facilities, insufficient data)

## US News 2026 Methodology (approximate)

Based on the data patterns, US News 2026 appears to:

- Weight **Quality Measures (QM)** more heavily than CMS does
- Consider both **Long-Stay** and **Short-Stay QM** separately
- Require **CMS QM Rating ≥ 4** for High Performing consideration
- Use a composite that is NOT simply the CMS Overall Rating
- Penalize facilities with **Special Focus Status** or **Abuse Icon** flags
- Have their own proprietary threshold formula (not publicly documented as a simple algorithm)

## Mapping Function (CMS → Approximate US News)

This is an **approximation only** — do not represent as authoritative US News data:

```python
def cms_to_usnews_approx(overall_rating, qm_rating, long_qm, short_qm, 
                          special_focus='', abuse_icon=''):
    """Approximate US News 2026 category from CMS sub-ratings."""
    if not overall_rating or overall_rating == '':
        return None  # Not rated / insufficient data
    
    overall = int(float(overall_rating))
    qm = int(float(qm_rating)) if qm_rating and qm_rating.strip() else 0
    
    # Check disqualifying flags
    if special_focus == 'Y' or abuse_icon == 'Y':
        return "As Expected"
    
    # High Performing candidates
    if overall == 5 and qm >= 4:
        return "High Performing"
    if overall == 5 and qm >= 3 and long_qm and short_qm:
        lq = int(float(long_qm)) if long_qm.strip() else 0
        sq = int(float(short_qm)) if short_qm.strip() else 0
        if lq >= 4 and sq >= 3:
            return "High Performing"
    
    # Most CMS 5-star with good QM → High Performing
    if overall == 5 and qm >= 3:
        return "High Performing"
    
    # Edge case: very high QM can offset lower overall
    if qm >= 5 and long_qm and short_qm:
        lq = int(float(long_qm)) if long_qm.strip() else 0
        sq = int(float(short_qm)) if short_qm.strip() else 0
        if lq >= 4 and sq >= 3:
            return "High Performing"
    
    return "As Expected"
```

## When to Use CMS Data vs US News Data

- **CMS data** (this skill): Reliable, programmatic, always accessible via API. Use for internal analytics, QA monitoring, and facility comparisons.
- **US News 2026 ratings**: Consumer-facing label. Only authoritative when pulled directly from health.usnews.com. The US News site is often blocked from CLI/bot environments. Use CMS data as a proxy with documented caveats.
