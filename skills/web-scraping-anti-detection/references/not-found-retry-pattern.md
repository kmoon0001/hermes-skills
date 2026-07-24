# NOT FOUND Retry Pattern — "0 match" / clean-page failures

When a batch scrape returns `NOT FOUND` (the page loaded cleanly with "0 match") rather than `ERROR:MAX_RETRIES` (connection timed out), it's a different failure mode. The search found nothing on the target site, but the facility may still be listed under a different name.

## Diagnosis

Before retrying, check which NOT FOUND entries are genuine misses:

| Test | Meaning |
|------|---------|
| Facility has a valid CMS CCN | It's a real Medicare/Medicaid SNF — should exist on the rating site |
| Facility has CMS overall rating of 4-5 and good staffing | Likely a scraper miss, not a genuine absence |
| Facility is in a state/region with few US News listings (TN, ID, NV small facilities) | Genuine — US News may not rate them |
| Facility was rated in the original ENSG spreadsheet | Original data predates the scrape — retry with different names |

## Retry with Alternative Names

The batch script usually searches by the **operational/location name** from the input file. The **CMS Provider Name** (from CMS provider data, column I in the ENSG spreadsheet) often differs. Try these in order:

1. Original operational name (what was already searched)
2. CMS Provider Name (the legal/Medicare name)
3. Shortened variations (e.g. "The Oaks at Lakewood" → "Oaks at Lakewood")
4. Drop suffixes ("Rehabilitation and Healthcare Center" → try "Rehab", "Center", or just the base name)

### Script pattern for alternative-name retry

```js
const searchNames = [
  originalName,
  cmsProviderName,
  ...shortVariants
];

for (const searchName of searchNames) {
  const url = `https://health.usnews.com/best-nursing-homes/search?name=${encodeURIComponent(searchName)}&location=${encodeURIComponent(city)},+${st}`;
  
  for (let retry = 0; retry < 5; retry++) {
    const text = await page.evaluate(() => document.body.innerText);
    
    if (text.includes('0 match') || text.includes('0 nursing homes')) {
      // This name didn't work — try next alternative
      break;
    } else if (text.includes('High Performing')) {
      rating = 'High Performing';
    } else if (text.includes('As Expected')) {
      rating = 'As Expected';
    } else if (text.includes('match')) {
      // Has results but no rating on search page — click into detail page
      const link = await page.$('a[href*="/best-nursing-homes/"]');
      if (link) {
        await link.click();
        await page.waitForTimeout(5000);
        const detailText = await page.evaluate(() => document.body.innerText);
        if (detailText.includes('High Performing')) rating = 'High Performing';
        else if (detailText.includes('As Expected')) rating = 'As Expected';
      }
    }
  }
}
```

## Expected Recovery

From experience with US News nursing homes:
- **~2 of 16** NOT FOUND facilities recover with alternative name search
- **~0 of 16** recover from "0 match" via retry alone (no connection error to fix)  
- The remaining ~14 are **genuine absences** — US News only rates ~14,500 of 15,500+ Medicare-certified SNFs

## When to accept NOT FOUND as final

A facility is genuinely NOT on the rating site if:
- Multiple name variations all returned "0 match" with 5+ retries
- CMS CCN exists (it's a real SNF) but the site simply doesn't have a profile
- Facilities in clusters from the same operator in the same region ALL return NOT FOUND (suggests the operator hasn't submitted data)
- The facilities are small (<60 beds) with 1-2 star CMS overall ratings — US News tends to exclude low-volume or low-performing facilities

## Post-Retry: Update output

After retrying with alternative names, merge the new results back into the master CSV. Any entries that remain NOT FOUND should stay as `NOT FOUND` in the final output (plus a note explaining "Not listed on US News").
