# 2captcha Integration for License Verification

## Setup
1. Sign up at https://2captcha.com/auth/register
2. Add funds (minimum $1, enough for 300+ CAPTCHAs)
3. Get API key from dashboard → Settings → API Key
4. Run: `python setup_2captcha.py` (prompts for key securely via getpass)
5. Key saved to .env as `TWOCAPTCHA_API_KEY`

## What Works (PROVEN)
- **reCAPTCHA v2** — ✅ **South Carolina**: Reliable. Module: `states/south_carolina.py`. Verified: Lacey Smith ACTIVE #124419.
- **reCAPTCHA v3** — ⚠️ Intermittent. Tokens obtained but form submission sometimes fails (~30-50%).
- **hCaptcha** — Supported but untested on our portals
- **Image CAPTCHAs** — Simple text only (NOT BotDetect)

## What Does NOT Work
- **BotDetect CAPTCHAs** (Tennessee) — 0% accuracy. Workers cannot read distorted text.
- **DataDome** (Alaska) — Claims support but untested.
- **AWS WAF** (Iowa) — JavaScript challenge, not standard CAPTCHA.

## API Usage

### reCAPTCHA v2 (South Carolina pattern)
```python
import urllib.request, urllib.parse, json, time

def solve_recaptcha_v2(site_key, page_url, api_key):
    data = urllib.parse.urlencode({
        "key": api_key, "method": "userrecaptcha",
        "googlekey": site_key, "pageurl": page_url, "json": 1
    }).encode()
    req = urllib.request.Request("http://2captcha.com/in.php", data=data)
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    
    captcha_id = result["request"]
    for i in range(60):
        time.sleep(5)
        url = f"http://2captcha.com/res.php?key={api_key}&action=get&id={captcha_id}&json=1"
        with urllib.request.urlopen(url, timeout=10) as resp:
            result = json.loads(resp.read())
        if result.get("status") == 1:
            return result["request"]
    return "TIMEOUT"

# Then set token and submit:
# page.evaluate(f"document.getElementById('g-recaptcha-response').value = '{token}'")
# page.evaluate("document.querySelector('button[type=submit]').click()")
```

### reCAPTCHA v3 (Utah pattern)
```python
def solve_recaptcha_v3(site_key, page_url, action, api_key):
    data = urllib.parse.urlencode({
        "key": api_key, "method": "userrecaptcha",
        "googlekey": site_key, "pageurl": page_url,
        "version": "v3", "action": action, "min_score": 0.3, "json": 1
    }).encode()
    # ... same polling pattern as reCAPTCHA v2
```

## Cost Estimate
- $0.003 per CAPTCHA solve
- 9 South Carolina searches = $0.03 ✅
- 34 Utah reCAPTCHA v3 solves = $0.10 (intermittent)
- 11 Tennessee searches = $0.03 ❌ (fails on BotDetect)

## Key Learnings
- BotDetect CAPTCHAs resist ALL automated solving (OCR, vision models, human CAPTCHA farms)
- reCAPTCHA v2 is reliably solvable by 2captcha workers (SC proven)
- reCAPTCHA v3 is solvable but form submission can fail even with valid token
- Always test the specific CAPTCHA type before committing to a paid service
- Use `getpass` for API key input, never paste keys in chat
