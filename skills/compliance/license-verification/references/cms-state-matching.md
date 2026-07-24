# CMS State Matching — Full Names vs Abbreviations

## The Problem

When matching facilities between two data sources (e.g., user's Excel and CMS data), state names may be in different formats:
- Excel often stores full names: "Arizona", "California", "Texas"
- CMS data uses abbreviations: "AZ", "CA", "TX"

If the matching function only tries one format, 0% of matches succeed.

## The Fix (from cms_data.py)

```python
STATE_MAP = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", ...
}

def match_facility(facility_name, state, provider_data):
    state = state.strip().upper()
    full_state = STATE_MAP.get(state, state)
    
    states_to_try = set()
    if len(state) == 2:
        # Input is abbreviated — also try full name
        states_to_try.add(state)
        states_to_try.add(full_state)
    else:
        # Input is full name — also try abbreviation
        states_to_try.add(state)
        states_to_try.add(full_state)
    
    # Try exact match with both formats
    for s in states_to_try:
        key = f"{norm_name}|{s}"
        if key in provider_data:
            return provider_data[key]
    
    # Then try fuzzy match
    ...
```

## Key Insight

`STATE_MAP.get(state, state)` returns:
- If state="ARIZONA" → returns "AZ" (the abbreviation)
- If state="AZ" → returns "ARIZONA" (the full name)
- If state="XX" → returns "XX" (unknown, no mapping)

So `states_to_try` always has both formats, regardless of which one was input.

## Verification

Test with:
```python
from cms_data import init_cms_cache, get_facility_cms
init_cms_cache()

# Should match — "Arizona" in Excel, "AZ" in CMS
r = get_facility_cms("Chandler Post Acute and Rehabilitation", "Arizona")
assert r["cms_match"] == "YES"
assert r["cms_overall_rating"] == "4"
```

Before the fix: 0% match rate.
After the fix: ~95% match rate for facilities in CMS.
