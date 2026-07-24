---
name: web-scraping-anti-detection
description: "Patterns to bypass bot detection on sites that block Playwright's bundled Chromium. Chrome Canary + --headless=new + --disable-http2 + navigator.webdriver override. Proven on US News health.usnews.com (Akamai/CloudFront CDN)."
category: software-development
---

# Web Scraping Anti-Detection

Patterns for sites that block Playwright's bundled Chromium (navigator.webdriver, HTTP/2 protocol errors, User-Agent fingerprinting). Uses Chrome Canary instead of Playwright's bundled browser.

## The Core Bypass

Always try this first when a headless Playwright script gets blocked:

```js
const browser = await chromium.launch({
  executablePath: 'C:\\Users\\kevin\\AppData\\Local\\Google\\Chrome SxS\\Application\\chrome.exe',
  headless: false,
  args: [
    '--headless=new',
    '--no-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-http2',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'
  ]
});
const page = await browser.newPage();
await page.addInitScript(() => { Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); });
```

## Key Arguments Explained

| Arg | Why |
|-----|-----|
| `executablePath` pointing to Chrome Canary | Uses REAL Chrome, not Playwright's bundled Chromium which has detectable differences |
| `--headless=new` | Chrome's newer headless mode — doesn't expose automation flags like old headless |
| `--disable-http2` | Sites using Akamai/CloudFront CDN intermittently drop HTTP/2 connections (ERR_HTTP2_PROTOCOL_ERROR). HTTP/1.1 is more reliable |
| `--disable-blink-features=AutomationControlled` | Removes the `--enable-automation` flag |
| `navigator.webdriver` override | Hides the `webdriver` property that sites check |

## Retry Strategy

Many CDNs do intermittent rate-limiting. Always wrap requests:

```js
let retries = 0;
while (retries < 3) {
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 25000 });
    await page.waitForTimeout(3000);
    break;
  } catch(err) {
    retries++;
    await page.waitForTimeout(5000 * retries); // 5s, 10s, 15s
  }
}
```

## Warmup

Load the site's homepage first before making search queries. This establishes a session and cookies:

```js
await page.goto('https://example.com', { waitUntil: 'domcontentloaded', timeout: 15000 });
await page.waitForTimeout(2000);
```

## Error Signals

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `ERR_HTTP2_PROTOCOL_ERROR` | CDN dropping HTTP/2 | Add `--disable-http2` |
| `ERR_CONNECTION_RESET` | Rate limiting | Add retry + delay |
| `TimeoutError` | Page not rendering | Increase timeout, check if CDN is blocking |
| `ERR_BLOCKED_BY_RESPONSE` | WAF/security block | Check if headless detection is the issue |

## Rate Limiting Protection

- 2-5s random delay between requests (`Math.random() * 3000 + 2000`)
- Exponential backoff on errors
- Track consecutive errors; if >3, increase delay to 10-15s
- Save state per-item for resume if interrupted

## References

See `references/batch-retry-pattern.md` for the focused re-run pattern when MAX_RETRIES entries remain after a batch scrape.
See `references/not-found-retry-pattern.md` for handling "NOT FOUND / 0 match" failures — a different failure mode where the page loaded cleanly but found no results.

## Known Working Sites

| Site | Detects? | Bypass |
|------|----------|--------|
| health.usnews.com | Yes (HTTP2 + webdriver) | Chrome Canary + headless=new + disable-http2 |
