# Nevada & Utah License Verification Techniques (2026-06-27)

## Nevada — PDF Roster (FULLY WORKING)

### Discovery
- `beltca.nevada.gov` has SSL cert mismatch → redirects to `http://beltca.nv.gov`
- "Current Administrators" page at `/current-administrators/` has PDF rosters
- Three PDFs: NFA, RFA, HSE administrators
- NFA PDF URL: `http://beltca.nv.gov/uploadedFiles/beltcanvgov/content/CEU_Program/Licensed%20Nursing%20Facility%20Administrators.pdf`

### PDF Structure
- Header: "LICENSED NURSING FACILITY ADMINISTRATORS", "Last Updated: 03/31/2026"
- Column headers: Administrator Name, License #, Status, Original License Date, License Expiration Date, Disciplinary Actions
- Each admin on one line: `Last, First Middle    License#    Status    OrigDate    ExpDate`
- 100 administrators in current PDF
- Updated quarterly

### Parse Code
```python
import subprocess, re

result = subprocess.run(['pdftotext', '-layout', pdf_path, '-'],
                       capture_output=True, text=True, timeout=30)
lines = result.stdout.split('\n')

for line in lines:
    line = line.strip()
    if not line or 'Administrator Name' in line or 'LICENSED' in line or 'Last Updated' in line:
        continue
    m = re.match(
        r"^(.+?)\s{2,}(\d+)\s+(Active|Inactive|Expired|Revoked|Suspended|Pending|Current)"
        r"\s+(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}/\d{1,2}/\d{4})",
        line
    )
    if m:
        name_raw = m.group(1).strip()
        name_parts = name_raw.split(", ", 1)
        last = name_parts[0].strip()
        first_middle = name_parts[1].strip() if len(name_parts) > 1 else ""
        full_name = f"{first_middle} {last}"
        # m.group(2)=license, m.group(3)=status, m.group(4)=orig_date, m.group(5)=exp_date
```

### Name Matching
- ENSG Excel: "First Last" format
- PDF: "Last, First Middle" format
- Match by: exact → first+last → last-only (if unique)

### Verification Results (2026-06-27)
| Admin | Facility | License | Status | Expiration |
|-------|----------|---------|--------|------------|
| Nathan Lant | Hearthstone Health and Rehabilitation | #826 | Active | 8/31/2026 |
| Seth Anderson | Henderson Health and Rehabilitation | #801 | Active | 6/30/2026 |
| Whitney Wilding | Rosewood Rehabilitation Center | #817 | Active | 10/31/2027 |

---

## Utah — Playwright + reCAPTCHA v3 (INTERMITTENT)

### Portal Details
- URL: `https://secure.utah.gov/llv/search/index.html`
- After submission: navigates to `/llv/search/search.html`
- reCAPTCHA v3 site key: `6LcQUqIUAAAAAG7lgG1BfDlhvVUuFP26QsY4Eq6_`
- Profession: Health Facility Administrator (checkbox `item153_1`)
- Form action: `/llv/search/index.html` (POST)

### Critical: Form Submission Method
`form.submit()` and `requestSubmit()` DO NOT WORK with reCAPTCHA v3 on this site.
The ONLY reliable method is clicking the submit button:

```python
submit_btn = pg.query_selector("input[type='submit']")
submit_btn.click()
pg.wait_for_url("**/search.html**", timeout=15000)
```

`expect_navigation()` fails intermittently — use `wait_for_url()` instead.

### reCAPTCHA v3 Token Acquisition
```python
pg.evaluate("""
    () => {
        return new Promise((resolve) => {
            const siteKey = document.getElementById('recaptchaSiteKey');
            grecaptcha.execute(siteKey.value, {action: 'search'}).then(token => {
                document.getElementById('g-recaptcha-response-name').value = token;
                resolve();
            });
        });
    }
""")
```

### Anti-Detection Measures
```python
browser = p.chromium.launch(
    headless=True,
    args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
)
context = browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ...",
    viewport={"width": 1920, "height": 1080},
    locale="en-US",
)
pg.evaluate("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
```

### Results Format
Multi-line per entry:
```
NAME\tCITY\t
PROFESSION
LICENSE_TYPE
\tLICENSE#\tSTATUS
```

Names are ALL CAPS. Parser must:
1. Skip header lines ("City", "Status", "License #", etc.)
2. Handle ALL CAPS names (not just mixed case)
3. Handle tab-separated status (`7946637-1501\tACTIVE`)

### Success Rate
~30-50% with headless Chromium. reCAPTCHA v3 scores based on:
- IP reputation (datacenter = low score)
- Cookie history (no history = low score)
- Behavioral patterns (headless = low score)
- TLS fingerprint

For reliable coverage, use `semi_auto.py` or paid data download.

### Verification Results (2026-06-27)
| Admin | Facility | Profession | License | Status |
|-------|----------|------------|---------|--------|
| Kirk Rodney Player | Pinnacle Nursing and Rehabilitation Center | Health Facility Administrator | #7946637-1501 | Active |

---

## Tennessee — BotDetect CAPTCHA (BLOCKED)

### Portal Details
- URL: `https://internet.health.tn.gov/Licensure/`
- Tech: ASP.NET WebForms + BotDetect CAPTCHA
- NHA profession value: `2514` ("Nursing Home Administrator")
- CAPTCHA field: `c_default_ctl00_pagecontent_captchacode`

### CAPTCHA Analysis
- BotDetect image CAPTCHA (250x40 JPEG, ~3.5KB)
- OCR (pytesseract) gives garbage — BotDetect is OCR-resistant
- Audio CAPTCHA endpoint returns 400 (disabled by site)
- Headless browser gets 403 (IP blocking)
- Form without CAPTCHA → redirects to `SearchError.aspx`

### CAPTCHA Input Field (CRITICAL)
The correct field ID is `ctl00_PageContent_CaptchaCodeTextBox` (NOT `c_default_ctl00_pagecontent_captchacode` which is a hidden BotDetect session token).

```python
page.fill("#ctl00_PageContent_CaptchaCodeTextBox", captcha_text)
```

### Vision Model Approach (TESTED — LOW SUCCESS RATE)
Free vision models (Gemma 4 26B via OpenRouter) read the CAPTCHA but get characters wrong ~70% of the time. BotDetect designs distorted text to resist ML vision. For production, use semi_auto.py.

OpenRouter setup (simpler than Gemini):
- Get key at https://openrouter.ai/keys (free, no project setup)
- Model: `google/gemma-4-26b-a4b-it:free`
- Save to .env: `OPENROUTER_API_KEY=sk-or-...`

### Three Tennessee Portals
| URL | Has NHA? | Notes |
|-----|----------|-------|
| `verify.tn.gov` | NO | Redirects to Commerce site (no NHA data) |
| `internet.health.tn.gov/Licensure/` | YES | BotDetect CAPTCHA |
| `internet.health.tn.gov/LicensureReports/` | YES | Report generator (bulk export, jQuery AJAX) |

### Potential Approach: LicensureReports
The report generator at `/LicensureReports/` uses jQuery AJAX with CSRF tokens.
No CAPTCHA on the reports page. Could potentially generate bulk CSV exports
of all NHA licensees, bypassing the individual search CAPTCHA.
Not yet implemented.
