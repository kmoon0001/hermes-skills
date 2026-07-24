# Tennessee BotDetect CAPTCHA — Reverse Engineering Analysis

**Date:** 2026-06-27
**Portal:** https://internet.health.tn.gov/Licensure/

## Form Structure

ASP.NET WebForms with BotDetect CAPTCHA. Form action: `default.aspx` (POST).

### Required POST Fields

| Field | Value | Notes |
|-------|-------|-------|
| `__VIEWSTATE` | ~4500 char base64 | Extracted from page HTML |
| `__VIEWSTATEGENERATOR` | `BAEED252` | Fixed across sessions |
| `__EVENTVALIDATION` | ~1200 char base64 | Changes per session |
| `__EVENTTARGET` | (empty) | For button submit |
| `__EVENTARGUMENT` | (empty) | For button submit |
| `ctl00$PageContent$txtFirstName` | user input | Optional |
| `ctl00$PageContent$txtMiddleName` | user input | Optional |
| `ctl00$PageContent$txtLastName` | user input | Required for search |
| `ctl00$PageContent$txtCity` | user input | Optional filter |
| `ctl00$PageContent$drpStates` | state code | Optional filter (AL, AK, etc.) |
| `ctl00$PageContent$drpProfessions` | `2514` | NHA = 2514, ALL = 9999 |
| `ctl00$PageContent$txtLicense` | user input | Optional |
| `ctl00$PageContent$btnSubmit` | `Submit` | Button text |
| `c_default_ctl00_pagecontent_captchacode` | CAPTCHA text | BotDetect field |

### Profession Values (partial)

- `2514` — Nursing Home Administrator
- `564` — Res./Inst. Home Administrator
- `9999` — ALL
- `1702` — Advanced Practice Registered Nurse
- `1703` — Registered Nurse
- `1704` — Licensed Practical Nurse
- `501` — Nurse Aide

## CAPTCHA Analysis

### BotDetect Image CAPTCHA
- Format: JPEG, 250x40 pixels, ~3.5KB
- Characters: alphanumeric (case-sensitive)
- Length: typically 4-6 characters
- OCR resistance: HIGH — pytesseract gives garbage even with preprocessing

### Audio CAPTCHA (DISABLED)
- URL pattern: `BotDetectCaptcha.ashx?get=sound&c=...&t=...&s=...`
- Returns: 400 Bad Request (11 bytes: "Bad Request")
- The `s=` parameter appears to be a session/proof token
- Even with correct session cookies, audio endpoint returns 400
- Likely disabled by site administrator

### Whisper Transcription (works on OTHER BotDetect sites)
- faster-whisper `base` model can transcribe BotDetect audio CAPTCHAs
- BotDetect spells out each character: "T-A-R-W-J-3"
- Clean with: `re.sub(r'[^a-zA-Z0-9]', '', raw_text)`
- Works when audio endpoint is available (not on TN)

### What Doesn't Work
1. **pytesseract OCR** — BotDetect is specifically designed to resist OCR
2. **Image preprocessing + OCR** — contrast enhancement, scaling, median filter all fail
3. **Audio CAPTCHA + Whisper** — audio endpoint disabled (400)
4. **Headless browser** — gets 403 (IP blocking from datacenter IPs)
5. **Form without CAPTCHA** — redirects to SearchError.aspx
6. **playwright-stealth** — doesn't help (BotDetect checks IP reputation, not just browser fingerprint)

### What Could Work
1. **semi_auto.py** — real Chrome, user solves CAPTCHA once, auto-searches rest
2. **2captcha API** — ~$0.003/solve, reliable for image CAPTCHAs
3. **LicensureReports bulk export** — bypass individual search CAPTCHA entirely (not yet implemented)

## Session/Request Flow

```
GET /Licensure/
  → Set-Cookie: ASP.NET_SessionId=...
  → Response contains: __VIEWSTATE, __EVENTVALIDATION, CAPTCHA image URL
  
GET /Licensure/BotDetectCaptcha.ashx?get=image&c=...&t=...
  → Returns JPEG CAPTCHA image
  
POST /Licensure/default.aspx
  → All form fields + CAPTCHA text + session cookie
  → Success: results page with license data
  → Failure: redirect to SearchError.aspx
```

## Python Implementation Notes

```python
import requests, re

session = requests.Session()
resp = session.get("https://internet.health.tn.gov/Licensure/", 
    headers={"User-Agent": "Mozilla/5.0 ..."})
html = resp.text

# Extract ASP.NET fields
vs = re.search(r'__VIEWSTATE.*?value="([^"]*)"', html).group(1)
ev = re.search(r'__EVENTVALIDATION.*?value="([^"]*)"', html).group(1)

# Get CAPTCHA image
captcha_url = re.search(r'(BotDetectCaptcha\.ashx\?get=image[^"]*)', html)
img = session.get(f"https://internet.health.tn.gov/Licensure/{captcha_url.group(1).replace('&amp;', '&')}")

# After solving CAPTCHA (manually or via service):
data = {
    "__VIEWSTATE": vs,
    "__VIEWSTATEGENERATOR": "BAEED252",
    "__EVENTVALIDATION": ev,
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    "ctl00$PageContent$txtLastName": "Smith",
    "ctl00$PageContent$drpProfessions": "2514",
    "ctl00$PageContent$btnSubmit": "Submit",
    "c_default_ctl00_pagecontent_captchacode": solved_captcha_text,
}
result = session.post("https://internet.health.tn.gov/Licensure/default.aspx", data=data)
```
