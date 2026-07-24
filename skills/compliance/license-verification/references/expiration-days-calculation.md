# Expiration Days Calculation Pattern

## Problem

Several state scrapers parsed expiration strings but returned `days_until_expiry: None`. This caused expiration alerts to silently skip those states.

## Affected States

| State | Expiration Format(s) | Source |
|-------|---------------------|--------|
| Alabama | `10/31/2026` (Renewal Date), `January 01, 2023` (Licensure) | ASP.NET WebForms |
| Idaho | `10-Feb-2028` | edopl.idaho.gov |
| Wisconsin | `2025-01-22` (Granted date) | DSPS License Lookup |

## Fix

Add this block to any scraper that returns a non-empty `expiration` string:

```python
from datetime import datetime

days_until = None
if expiration:
    for fmt in ["%m/%d/%Y", "%B %d, %Y", "%Y-%m-%d", "%d-%b-%Y", "%m-%d-%Y"]:
        try:
            exp_date = datetime.strptime(expiration.strip(), fmt)
            days_until = (exp_date - datetime.now()).days
            break
        except ValueError:
            continue
```

## Alert Thresholds (in verify_all.py)

```python
if days_until is not None and days_until >= 0 and days_until <= 60:
    alert = f"EXPIRES IN {days_until} DAYS"
elif days_until is not None and days_until < 0:
    alert = "EXPIRED"
```

## Notes

- `days_until is not None` guards against skipping states that still return `None`.
- Negative values mean the license has expired.
- Only Alabama, Idaho, and Wisconsin needed this fix; Arizona, Oregon, and Texas already compute days.
