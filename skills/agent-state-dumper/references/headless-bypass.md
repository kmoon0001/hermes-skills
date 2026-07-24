# Headless Browser Bypass Techniques

Techniques for sites that block headless Playwright (DataDome, Akamai, Cloudflare, etc.).

## Primary: Chrome Canary + `--headless=new`

Launch Playwright with Chrome Canary (not Playwright's bundled Chromium):

```js
const browser = await chromium.launch({
  executablePath: 'C:\\Users\\kevin\\AppData\\Local\\Google\\Chrome SxS\\Application\\chrome.exe',
  headless: false,
  args: [
    '--headless=new',
    '--no-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
  ]
});
const page = await browser.newPage();
await page.addInitScript(() => {
  Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
});
```

Why it works:
- `--headless=new` uses Chrome's newer headless mode (no visible automation flags)
- Real Chrome Canary binary, not Playwright's bundled `chrome-win` (different build)
- `navigator.webdriver` explicitly hidden via `addInitScript` (runs before page JS)
- Real user agent string matching actual Chrome version

## Fallback: `playwright-cli --headed`

```bash
npx playwright-cli --session usnews open <url> --headed
```

Requires interactive session — can't run in cron.

## Cooked: Batch US News Script

Located at `C:\Users\kevin\Desktop\usnews_lookup_batch.js`

Features:
- Resume capability via state file
- State abbreviation map (full state name → abbr)
- Random delays (2-5s) between requests
- Per-facility error handling
- Pipe-delimited input/output

Usage:
```bash
node usnews_lookup_batch.js [facilities_file.txt]
```

Input format: `row|name|city|state|old_rating`
Output: `usnews_lookup_results.csv`
