# Utah DOPL Data Request / Roster Order Workflow

Use this when Kevin asks to get as far as possible on the Utah website for the Health Facility Administrator roster.

## Target site

- License lookup: `https://secure.utah.gov/llv/search/index.html`
- Data request: `https://secure.utah.gov/datarequest/professionals/index.html`

## Known-good website path

1. Open the data request page.
2. Select `without address/phone/email` unless Kevin explicitly needs contact data.
3. On the profession list, uncheck all profession types.
4. Check only `Health Facility Administrator`.
   - In the observed page DOM this was checkbox id `i231`, name `professionTypes`, value `_231p`.
   - Do not rely solely on the id forever; if it changes, locate by label text containing `Health Facility Administrator`.
5. Click/review the `without address/phone/email` request button.
6. On summary page, confirm the order is limited to HFA only.
7. Select delivery format:
   - Excel is acceptable for the observed HFA count because it is under 65,535 rows.
   - Text/CSV is safer if the count grows above Excel's old-row limit warning.
8. Fill known fields only:
   - Name: `Kevin Moon`
   - Email: `kevinmoon7@gmail.com`
   - Leave Phone for Kevin to enter unless he has supplied a current phone number in the same turn.
9. Stop before clicking final Continue/payment. Kevin should complete phone/payment/checkout himself.

## Observed 2026-06-28 result

For Health Facility Administrator without address/phone/email:

- Records: 1,691
- Fee: $49.73
- Delivery email configured: `kevinmoon7@gmail.com`

Do not treat the fee/count as durable facts; re-check on the live page each time.

## Browser handoff pattern

When Kevin asks to take over, open a real Edge window and leave it alive. A browser automation session that exits may close the window, so launch Edge independently with a temporary profile and CDP, then connect to it only long enough to fill the page.

Pattern:

```python
import subprocess, time, urllib.request
from playwright.sync_api import sync_playwright

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
PROFILE = r'C:\Users\kevin\AppData\Local\Temp\utah-roster-edge-profile'
PORT = 9224
URL = 'https://secure.utah.gov/datarequest/professionals/index.html'

subprocess.Popen([
    EDGE,
    f'--remote-debugging-port={PORT}',
    f'--user-data-dir={PROFILE}',
    '--no-first-run',
    '--no-default-browser-check',
    URL,
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for _ in range(60):
    try:
        urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/version', timeout=1).read()
        break
    except Exception:
        time.sleep(0.5)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(f'http://127.0.0.1:{PORT}')
    page = browser.contexts[0].pages[0]
    page.goto(URL, wait_until='domcontentloaded')
    # fill/select only non-payment steps
    browser.close()  # disconnects CDP; independently launched Edge remains open
```

After launch/fill, verify the handoff with a CDP liveness check:

```python
urllib.request.urlopen('http://127.0.0.1:9224/json/version', timeout=2)
```

If Kevin says Edge is not open, retry the independent Edge launch rather than only using the built-in browser session.

## After Kevin completes checkout

- If Utah emails the roster to Gmail, run:

```bash
cd D:/license-verification
python data_request_automation.py --poll-email --email-days 30 --max-emails 50 --build-supplements --build-final --open-final
```

- If Utah downloads a file to Downloads, run:

```bash
D:/license-verification/import_data_request_downloads.cmd
```

or:

```bash
cd D:/license-verification
python data_request_automation.py --scan-downloads --hours 72 --build-supplements --build-final --open-final
```
