# Gemini Vision CAPTCHA Solving (Experimental)

## Overview
Use Google Gemini 2.0 Flash (free tier) to read BotDetect/CAPTCHA images via Playwright CDP screenshots.

## Setup
1. Get free API key: https://aistudio.google.com/apikey
2. Run: `python C:/Users/kevin/Desktop/setup_gemini_key.py` (secure prompt, hidden input)
3. Key saved to: `~/.hermes/profiles/coding-profile/.env` as `GEMINI_API_KEY`

## CDP CAPTCHA Capture Pattern
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent="Mozilla/5.0 ...")
    page = context.new_page()
    page.goto("https://internet.health.tn.gov/Licensure/", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # Screenshot the CAPTCHA image element
    captcha_img = page.query_selector("img.BDC_CaptchaImage")
    if captcha_img:
        captcha_img.screenshot(path="captcha.png")
```

## Gemini API Call
```python
import urllib.request, json, base64

def read_captcha(image_path, api_key):
    with open(image_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    body = json.dumps({
        "contents": [{"parts": [
            {"text": "Read the CAPTCHA text in this image. Reply with ONLY the characters, nothing else."},
            {"inline_data": {"mime_type": "image/png", "data": img_data}}
        ]}]
    }).encode()
    
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
```

## Limitations
- BotDetect CAPTCHAs are designed to resist ML vision (distortion, noise, overlapping)
- Success rate varies by CAPTCHA difficulty
- May need retry logic (3-5 attempts)
- Audio CAPTCHA endpoint may be disabled (returns 400)

## Best Free Vision Models
| Model | Speed | Vision Quality | Free Tier |
|-------|-------|---------------|-----------|
| Gemini 2.0 Flash | Fast | Excellent | 15 req/min |
| Ollama + LLaVA | Slow | Good | Unlimited (local) |
| OpenRouter free | Varies | Varies | Limited |

## Recommendation
For reliable coverage, use semi_auto.py (user solves CAPTCHA once). The vision approach is experimental and best for states with simple CAPTCHAs or as a fallback.
