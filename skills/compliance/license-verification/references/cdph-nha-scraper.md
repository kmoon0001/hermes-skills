# CDPH NHA Scraper — Proven Pattern (Jun 23, 2026)

## Site
https://cvl.cdph.ca.gov/SearchPage.aspx

## Search Strategy (Updated Jun 23, 2026)

**Primary:** Use `rdoLastStart` (Last Name Starting With) — more reliable than exact name search.

```python
page.check('#ContentPlaceHolderMiddleColumn_rdoLastStart')
page.fill('#ContentPlaceHolderMiddleColumn_txtLastNameStart', last_name)
page.click('#ContentPlaceHolderMiddleColumn_btnSearch2')
page.wait_for_load_state('networkidle', timeout=15000)
page.wait_for_timeout(2000)
```

**Fallback:** If no results, try `rdoLastFirst`:
```python
page.check('#ContentPlaceHolderMiddleColumn_rdoLastFirst')
page.fill('#ContentPlaceHolderMiddleColumn_txtLastName', last_name)
page.fill('#ContentPlaceHolderMiddleColumn_txtFirstName', first_name)
page.click('#ContentPlaceHolderMiddleColumn_btnSearch2')
```

## Result Extraction (JavaScript)

Use `page.evaluate` to extract all table rows and `DetailPage.aspx` links:

```python
data = page.evaluate('''() => {
    const rows = [];
    const links = {};
    document.querySelectorAll('tr').forEach(tr => {
        const cells = Array.from(tr.querySelectorAll('td'));
        if (cells.length >= 4) {
            const text = cells.map(c => c.innerText.trim()).join('\t');
            rows.push(text);
        }
    });
    document.querySelectorAll('a[href*="DetailPage.aspx"]').forEach(a => {
        const m = a.href.match(/cert_holder_id=(\\d+)/);
        if (m && a.innerText.trim()) links[a.innerText.trim()] = m[1];
    });
    return {rows, links};
}''')
```

Rows are tab-delimited: `NAME \t TYPE \t NUMBER \t STATUS`.

## Expiration Date — Detail Page Required

**Critical change (Jun 23, 2026):** The results page does NOT show expiration. Open each result's detail page to get it.

```python
detail_url = f"https://cvl.cdph.ca.gov/DetailPage.aspx?cert_holder_id={cert_holder_id}"
page.goto(detail_url, timeout=30000)
text = page.inner_text("body")
exp_match = re.search(r"Expiration Date:\\s*([^\\n]+)", text, re.IGNORECASE)
if exp_match:
    expiration = exp_match.group(1).strip()
```

Detail page also shows:
- `Effective Date:` — use for notes
- `Status:` — maps to `Active`, `Denied Not Employable`, etc.

## Status Mapping

| Detail Page Status | Mapped To |
|--------------------|-----------|
| `ACTIVE, EMPLOYABLE` | `Active` |
| `DENIED, NOT EMPLOYABLE` | `Denied` |
| `INACTIVE` | `Inactive` |
| `EXPIRED` | `Expired` |
| `REVOKED` | `Revoked` |
| `SUSPENDED` | `Suspended` |

## Name Matching

CDPH result names use `LASTNAME, FIRSTNAME M.` format. `matches_name_score` uses `rapidfuzz.token_sort_ratio` with +10 bonuses for last/first name substring matches. Threshold 60.

## Tested Names (Jun 23, 2026)

| Name | Result | License # | Expiration |
|------|--------|-----------|------------|
| SMITH, ADRAIN B | Active | 00007647 | 2027-01-21 |
| COLE, CALENE | Denied Not Employable | 00084446 | 2000-06-12 |
