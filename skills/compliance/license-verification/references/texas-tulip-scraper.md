# Texas TULIP Scraper Details

## Site
https://tulip.hhs.texas.gov/TULIP/s/public-search

## Status
FULLY FUNCTIONAL — verified 2026-06-24

## Verified Results
- Robert Smith: Active, License #NFA007578, expires 2027-06-14
- Melinda Smith: Active, License #NFA012374, expires 2027-05-19
- Gabriel Barraza: Active, License #NFA012571, expires 2027-01-26
- Heather Hicks: Active, License #NFA009801, expires 2026-12-29
- Gregory Bustamante: Active, License #NFA012826, expires 2026-12-09

## Architecture
The TULIP site uses a custom Lightning Web Component `c-rs_-public-search-l-w-c` with nested shadow DOM containing:
- 8 `lightning-select` elements (Program Type, match types for First/Last Name, SSN, License #, State, Zip, City)
- 7 `lightning-input` elements (text fields for each search criterion)
- 2 buttons (Reset, Submit) inside shadow DOM

## Form Fields (in order)
| Index | Select Name | Purpose |
|-------|-------------|---------|
| 0 | (no name) | Program Type — must be "Nursing Facility Administrator" |
| 1 | firstNameOptn | First Name match type (Equals/Begins With/Ends With/Contains) |
| 2 | lstNameOptn | Last Name match type |
| 3 | ssnOptn | SSN match type |
| 4 | facNameOptn | Facility Name match type |
| 5 | facAddrOptn | Address match type |
| 6 | facZipOptn | Zip match type |
| 7 | facCityOptn | City match type |

## Key Technique: Native Select Piercing
Playwright's `page.locator("select").all()` pierces shadow DOM and returns the native `<select>` elements inside the Lightning components. This bypasses all the shadow DOM complexity.

```python
selects = page.locator("select").all()  # Returns 8 selects
selects[0].select_option(label="Nursing Facility Administrator")
```

## Critical Pitfalls
1. After selecting Program Type, the LWC re-renders. Must re-query `selects` list.
2. Submit button inside shadow DOM does NOT respond to standard `.click()`. Must use `page.get_by_text("Submit", exact=True).first.click(force=True)`.
3. Intermittent race conditions — add retry logic (2 attempts, 1s sleep).
4. **asyncio loop crash:** If called from Streamlit or Jupyter, `sync_playwright` fails with "Playwright Sync API inside asyncio loop." Fix: detect `asyncio.get_running_loop()` and run sync Playwright in a `ThreadPoolExecutor`. All 110 TX facilities showed identical "NEEDS MANUAL REVIEW" errors from this bug. (Fixed 2026-06-24.)
