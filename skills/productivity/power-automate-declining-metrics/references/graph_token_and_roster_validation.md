# Graph token refresh + DOR roster validation

Use this when the saved token at `C:\Users\kevin\Documents\graph_token.txt` is expired and the Pacific Coast DOR Roster needs to be verified before/after Power Automate changes.

## Refresh a Graph token without asking for credentials in chat

1. Open Graph Explorer in the already-authenticated browser session:
   `https://developer.microsoft.com/en-us/graph/graph-explorer`
2. Click **Sign in** and select `123713644@ensignservices.net` if prompted. The user can complete MFA/password directly in the browser if needed.
3. In Graph Explorer, open the **Access token** tab.
4. Click **Copy**. The visible token text and `jwt.ms` link may be masked/truncated with `...`; do not scrape those display values.
5. Save the Windows clipboard content to `C:\Users\kevin\Documents\graph_token.txt` and verify it looks like a JWT:
   - starts with `eyJ`
   - has 3 dot-separated parts
   - does not contain `...`

PowerShell one-liner from git-bash after clicking Copy:

```bash
powershell.exe -NoProfile -Command '$t = Get-Clipboard -Raw; $u = $t.Trim(); [IO.File]::WriteAllText("C:\Users\kevin\Documents\graph_token.txt", $u); Write-Output ("chars=" + $u.Length + " parts=" + ($u.Split(".").Count) + " starts=" + $u.StartsWith("eyJ") + " hasEllipsis=" + $u.Contains("..."))'
```

Expected good summary: `parts=3 starts=True hasEllipsis=False`.

## Validate the Pacific Coast DOR Roster

Use Microsoft Graph with:

- Site ID: `ensignservices.sharepoint.com,d03d707d-1a83-4851-aa74-dc1560d1d0c4,a66a3bed-1db7-49f6-b9f8-7708fd56a868`
- List ID: `99359330-0b9a-4abc-98c4-8579da49910d`
- Columns to validate: `Facility`, `DORName`, `DOREmail`, `Active`

Validation checks:

- token works against `/me`
- SharePoint site is accessible
- list items can be read
- every active row has Facility, DORName, and DOREmail
- DOREmail has email format and should generally end in `@ensignservices.net`

Python probe:

```python
import requests, re
from pathlib import Path

token = Path(r'C:\Users\kevin\Documents\graph_token.txt').read_text(encoding='utf-8').strip()
h = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}

for name, url in [
    ('me', 'https://graph.microsoft.com/v1.0/me?$select=displayName,userPrincipalName'),
    ('site', 'https://graph.microsoft.com/v1.0/sites/ensignservices.sharepoint.com:/sites/PacificCoast_SLP'),
]:
    r = requests.get(url, headers=h, timeout=30)
    print(name, r.status_code, r.text[:500] if r.status_code >= 400 else r.json())

site_id = 'ensignservices.sharepoint.com,d03d707d-1a83-4851-aa74-dc1560d1d0c4,a66a3bed-1db7-49f6-b9f8-7708fd56a868'
list_id = '99359330-0b9a-4abc-98c4-8579da49910d'
url = f'https://graph.microsoft.com/v1.0/sites/{site_id}/lists/{list_id}/items?$expand=fields&$top=200'
r = requests.get(url, headers=h, timeout=30)
r.raise_for_status()
items = r.json().get('value', [])

email_re = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
issues = []
active = []
for it in items:
    f = it.get('fields', {})
    facility = (f.get('Facility') or '').strip()
    dor = (f.get('DORName') or '').strip()
    email = (f.get('DOREmail') or '').strip()
    is_active = f.get('Active') is True or str(f.get('Active')).lower() in ('true', '1', 'yes')
    if is_active:
        active.append((facility, dor, email))
    if not facility:
        issues.append(f"Item {it.get('id')}: missing Facility")
    if is_active and not dor:
        issues.append(f"{facility}: active but missing DORName")
    if is_active and not email:
        issues.append(f"{facility}: active but missing DOREmail")
    if email and not email_re.match(email):
        issues.append(f"{facility}: invalid email {email}")
    if is_active and email and not email.lower().endswith('@ensignservices.net'):
        issues.append(f"{facility}: non-Ensign email {email}")

print('total_items', len(items), 'active', len(active), 'issues', len(issues))
for facility, dor, email in active:
    print(f'- {facility} | {dor} | {email}')
if issues:
    print('ISSUES:')
    for issue in issues:
        print('-', issue)
else:
    print('No roster integrity issues found.')
```

## Known-good June 2026 roster result

The validation returned 12 total rows, 12 active rows, 0 issues. Active facilities were:

- Alamitos West
- Beachside
- Coventry Court
- Mainplace Post Acute
- New Orange Hills
- Pacific Haven Subacute
- Palm Terrace
- Sea Cliff Healthcare
- St. Catherine
- St. Elizabeth
- The Hills Post Acute
- Victoria Healthcare
