# Webwright + Vision Model for CAPTCHA Solving

## Concept
Webwright (Microsoft Research) drives a browser using an LLM that writes
Playwright scripts each step. If the LLM has vision capabilities, it can
see CAPTCHA images in screenshots and type the answer.

## Best Free Vision Models for This

| Model | Provider | Free Tier | Vision Quality | Speed |
|-------|----------|-----------|----------------|-------|
| Gemini 2.0 Flash | Google | 15 req/min | Excellent | Fast |
| Gemini 1.5 Flash | Google | 15 req/min | Good | Fast |
| LLaVA 1.6 | Ollama | Unlimited (local) | Decent | Slow |
| Qwen-VL-Plus | Alibaba | Limited | Good | Medium |

**Recommendation:** Google Gemini 2.0 Flash — best free vision model.
Get API key at: https://aistudio.google.com/apikey

## How It Works
1. Webwright loads the page
2. Takes a screenshot
3. Sends screenshot to vision LLM
4. LLM sees CAPTCHA, reads the text
5. LLM writes code to type the CAPTCHA answer
6. Submits the form

## Webwright Config for Gemini
```yaml
model:
  model_class: openrouter
  model_name: google/gemini-2.0-flash-001
  provider_require_parameters: false
```

Or for direct Google API:
```yaml
model:
  model_class: google
  model_name: gemini-2.0-flash
  api_key: YOUR_GEMINI_API_KEY
```

## Limitations
- CAPTCHAs designed to resist ML vision (distorted text, background noise)
- BotDetect CAPTCHAs are specifically OCR-resistant
- reCAPTCHA v3 is invisible (no image to read) — this approach doesn't help
- Best for: image CAPTCHAs with readable text (BotDetect when not too distorted)
- Not helpful for: reCAPTCHA v2/v3, hCaptcha, DataDome, AWS WAF

## States Where This Might Help
- **Tennessee (BotDetect)**: Image CAPTCHA with readable text. Vision model
  could potentially read it. Audio endpoint is disabled (400).
- **Alaska (DataDome)**: No — DataDome uses behavioral analysis, not image CAPTCHA.
- **Iowa (AWS WAF)**: No — AWS WAF is JavaScript challenge, not image CAPTCHA.
- **South Carolina (reCAPTCHA)**: No — reCAPTCHA v2 checkbox, not image.
- **Utah (reCAPTCHA v3)**: No — invisible scoring, no image to read.

## Alternative: CDP Screenshot + External Vision API
Instead of Webwright, use Playwright CDP to capture the CAPTCHA image,
then send it to a vision API (Gemini, GPT-4V) for transcription:

```python
# Capture CAPTCHA via CDP
captcha_img = page.query_selector("img.BDC_CaptchaImage")
captcha_img.screenshot(path="captcha.png")

# Send to Gemini Vision API
import base64
with open("captcha.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Use Gemini API to read the text
# ... (API call with image_data)
```

This is more reliable than Webwright because you control the CAPTCHA
capture and can retry with different prompts.
