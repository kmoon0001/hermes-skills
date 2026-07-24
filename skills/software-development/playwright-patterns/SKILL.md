---
name: playwright-patterns
description: >-
  Reusable Playwright Python patterns for browser automation, CAPTCHA handling,
  bulk scraping, and Excel-style output on Windows. Captures field-tested
  techniques for semi-automated workflows, retry logic, and structured result
  formatting.
platforms: [windows]
---

# Playwright Patterns

## Scope
This skill covers raw Playwright Python API patterns for Windows automation scrapers
and semi-automated workflows. It does NOT cover the Webwright framework; for that
use `webwright-automation`.

## Semi-Automated CAPTCHA Workflow
When a site uses reCAPTCHA/v3/hCaptcha that blocks headless automation:

1. Use `launch_persistent_context(user_data_dir=..., headless=False)`
2. Browser reuses cookies + fingerprint between runs
3. User solves ONE CAPTCHA per state per session
4. Script waits for user signal (`input(">>> Press ENTER...")`) before bulk-searching

### Why this works
reCAPTCHA v3 re-evaluates on every page load using IP + browser fingerprint + behavior.
Stealth libraries hide automation flags but don't solve the challenge. A real user
session in a persistent profile raises the trust score enough that many sites stop
challenging after the first solve.

### Pitfall
If the site aggressively flags Playwright's `navigator.webdriver` flag or WebGL vendor,
stealth tools (`playwright_stealth`, `pydoll`) may be needed. Test with a simple
`page.evaluate("navigator.webdriver")` check first.

## Pre-Submit Hooks
Some forms require selecting a dropdown before searching (e.g., "Nursing Home
Administrators" program type). Configure each state with an optional `pre_submit`
field:

```python
STATE_CONFIGS = {
    "ALASKA": {
        "url": "https://...",
        "selector_program": "select[name='Program']",
        "pre_submit": "_select_program",
        # ...
    },
}

def _select_program(page, config):
    try:
        page.select_option(config["selector_program"], "Nursing Home Administrators", timeout=5000)
        time.sleep(1)
    except Exception as e:
        print(f"WARNING: could not select program: {e}")
```

## Retry Pattern for Transient Errors
Network flakiness, CloudFront blocks, and timeouts happen. Wrap verifiers with a
retry that sleeps between attempts:

```python
MAX_RETRIES = 2

def verify_with_retry(verifier, admin, page=None, max_retries=MAX_RETRIES):
    last_result = None
    for attempt in range(1, max_retries + 1):
        try:
            result = verifier(admin, page=page)
            status = result.get("status", "")
            if status and any(word in status.upper()
                              for word in ["TIMEOUT", "CONNECTION", "NETWORK", "ERR_"]):
                raise RuntimeError(f"Transient error: {status}")
            return result
        except Exception as e:
            last_result = e
            if attempt < max_retries:
                time.sleep(1)
    if isinstance(last_result, Exception):
        return {"status": "ERROR", "expiration": "", "url": "",
                "note": str(last_result), "days_until_expiry": None}
    return last_result
```

## Bulk Scraping Performance
Spawning a new browser per admin is the safest approach (no session bleed) but slow:
- Each lookup: 5-20s depending on site responsiveness
- 426 facilities across 8 states: ~30-60 minutes total

Optimization options:
- Persistent context across lookups in same state (reuses cookies, faster)
- Reduce `wait_after` delays (default 3000ms → 1000-1500ms if site is snappy)
- Parallel state runs (separate processes, not threads)

## Excel Output Pattern
Write results to a color-coded Excel file with openpyxl:

```python
# PASS=green, FAIL=red, NEEDS MANUAL REVIEW=yellow
for row in results:
    ws.append([state, facility, admin, raw_status, overall, alert, expiration, days, url, note])
    result_cell = ws.cell(row=ws.max_row, column=5)
    if overall == "PASS":
        result_cell.fill = PatternFill(start_color="C6EFCE", fill_type="solid")
    elif overall == "FAIL":
        result_cell.fill = PatternFill(start_color="FFC7CE", fill_type="solid")
    else:
        result_cell.fill = PatternFill(start_color="FFEB9C", fill_type="solid")
```

## Status Classification

| Bucket | Values |
|--------|--------|
| PASS | Active, Found, Actively Licensed, Current |
| FAIL | Not Found, Inactive, Expired, Revoked, Suspended, Denied, Lapsed |
| NEEDS MANUAL REVIEW | Blocked, Needs Manual, Error, empty/unknown |

## Graph Explorer Access Token Extraction

When automating Microsoft Graph Explorer with Playwright, the **Access token** appears in a tab named "Access token". After clicking the tab, the UI shows the token string and a **Copy** button. The token can be retrieved programmatically by:

1. Click the "Access token" tab:
   ```js
   await page.locator('text=Access token').first().click();
   ```
2. Optionally click the **Copy** button:
   ```js
   await page.locator('button:has-text("Copy")').click();
   ```
3. Read the token text directly from the element:
   ```js
   const token = await page.locator('div:has-text("eyJ")').innerText();
   console.log('Token:', token);
   ```

**Pitfalls**:
- The token element may be truncated in snapshots; use `innerText()` on the actual DOM element rather than relying on snapshot output.
- Multiple elements with the text "Access token" can exist; use `.first()` or a more specific selector (e.g., `[ref="e536"]`).
- The Copy button may be hidden behind a dropdown; ensure the button is visible before clicking.

**Example Playwright snippet**:
```js
await page.locator('text=Access token').first().click();
await page.locator('button:has-text("Copy")[visible=true]').click();
const token = await page.locator('div:has-text("eyJ")').innerText();
console.log('Token:', token);
```
Map raw state site statuses to three buckets:

| Bucket | Values |
|--------|--------|
| PASS | Active, Found, Actively Licensed, Current |
| FAIL | Not Found, Inactive, Expired, Revoked, Suspended, Denied, Lapsed |
| NEEDS MANUAL REVIEW | Blocked, Needs Manual, Error, empty/unknown |

## Expiration Alerting
Flag licenses expiring within 60 days:

```python
if days_until is not None and 0 <= days_until <= 60:
    alert = f"EXPIRES IN {days_until} DAYS"
elif days_until is not None and days_until < 0:
    alert = "EXPIRED"
```

## Error Handling for Excel Input
- Empty admin fields: skip, don't crash
- Empty state fields: skip, don't crash
- State not in verifier map: track as "NO ADMIN" in output summary
- Never let one bad lookup stop the whole run; wrap each admin in try/except or retry

## Verifier Function Signature: Optional `page=None` Parameter
To support shared browser contexts, design verifiers to optionally accept a `page` parameter:

```python
def verify_alabama(admin_name, page=None):
    url = "http://..."
    parts = admin_name.strip().split()
    first, last = parts[0], parts[-1]

    if page is None:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent="...")
            page = context.new_page()
            try:
                # ... full scraping logic ...
                return result
            except Exception as e:
                return {"status": "ERROR", ...}
            finally:
                browser.close()
    else:
        try:
            # ... same scraping logic, reusing provided page ...
            return result
        except Exception as e:
            return {"status": "ERROR", ...}
```

**Key rule**: The `else` branch must wrap logic in `try/except`. Do NOT copy the `except` block from the `if` branch outside the `else` — that breaks Python parsing.

**Pitfall: helper functions must also accept `page`.** If `verify_<state>()` calls a helper like `_try_search()`, the helper must accept `page=None` as a parameter. Do NOT rely on closure or assume `page` is in scope. Call the helper with explicit `page=None`: `_try_search(name, page=None)`. Without this, `UnboundLocalError` crashes all verifications. (TX scraper had this bug.)

## Sync Playwright Inside asyncio Loop (Streamlit, Jupyter)

`sync_playwright` crashes when called from within an running asyncio event loop:
"Playwright Sync API inside asyncio loop. Please use the Async API instead."

**Detection:**
```python
import asyncio

def _is_asyncio_running():
    try:
        loop = asyncio.get_running_loop()
        return loop is not None
    except RuntimeError:
        return False
```

**Fix — run sync Playwright in a thread:**
```python
if _is_asyncio_running():
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_run_sync_search, admin_name)
        return future.result(timeout=60)
else:
    with sync_playwright() as p:
        # normal sync flow
```

The thread runs without an event loop, so `sync_playwright` works normally. This is the simplest fix — converting to async Playwright requires rewriting the entire scraper.

**When this happens:** Streamlit runs an asyncio loop. If a Streamlit callback imports and calls a scraper directly (not via subprocess), every lookup fails with the same error. The `app.py` subprocess approach (`subprocess.Popen([sys.executable, "verify_all.py"])`) is safe because the subprocess has its own process with no event loop. The danger is direct imports in Streamlit forms.

## Shared Browser Context Per State (Performance Optimization)
Spawning a new browser per admin is safe but slow (~5-20s per admin due to startup). For bulk runs:

1. Create one Playwright instance, browser, and context for the entire state run
2. For each admin, create a fresh `page = context.new_page()`
3. Pass the page to the verifier: `result = verifier(admin, page=page)`
4. Close the page after each lookup: `page.close()`
5. After the state finishes, close context/browser/playwright

```python
# In run_verification():
for state in sorted(by_state.keys()):
    if state in playwright_states:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 ...")
    
    for fac in state_facilities:
        page = context.new_page() if browser else None
        result = verify_with_retry(verifier, admin, page=page)
        if browser:
            page.close()
    
    if browser:
        context.close()
        browser.close()
        playwright.stop()
```

**Performance gain**: 426 facilities across 7 states drops from ~30-60 min to ~10-20 min.

## Email Alert Integration
Attach email sending to the nightly run. Reads SMTP config from `config.json` or `SMTP_USER`/`SMTP_PASSWORD` env vars.

**Always load `.env` first:**
```python
from dotenv import load_dotenv
load_dotenv()
```
This accepts `project_root/.env` and makes `os.environ` populate before reading credentials.

```python
def send_email_alert(email_config, report_path, results):
    smtp_server = email_config.get("smtp_server", "smtp.office365.com")
    smtp_port = email_config.get("smtp_port", 587)
    use_tls = email_config.get("use_tls", True)
    smtp_user = os.environ.get("SMTP_USER") or email_config.get("smtp_user", "")
    smtp_password = os.environ.get("SMTP_PASSWORD") or email_config.get("smtp_pass", "")
    
    if not email_config.get("to") or not smtp_user or not smtp_password:
        print("No email configured, skipping")
        return
    
    msg = MIMEMultipart()
    msg["From"] = email_config.get("from", smtp_user)
    msg["To"] = email_config["to"]
    msg["Subject"] = f"License Verification Report - {datetime.now().strftime('%B %d, %Y')}"
    # Attach HTML body with summary table + flagged items
    # Attach Excel report as MIMEApplication
    # Send via smtplib.SMTP() with STARTTLS
```

**Pitfall**: Never hardcode credentials. Use env vars with config.json fallback. If credentials are missing, skip silently rather than crash — this keeps nightly runs from failing due to missing email setup.

## Chrome Profile Locking with `launch_persistent_context`

`launch_persistent_context` locks the Chrome profile directory. If Chrome was previously running (even from a killed process), the next launch fails with "Opening in existing browser session."

**Fix before running:**
```bash
taskkill //F //IM chrome.exe          # Kill all Chrome processes
rm -f profile_dir/SingletonLock       # Remove lock files
rm -f profile_dir/SingletonSocket
rm -f profile_dir/SingletonCookie
```

**In Python:** Check for the error and retry after cleanup:
```python
try:
    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR, headless=False, ...)
except Error as e:
    if "existing browser session" in str(e):
        os.system("taskkill //F //IM chrome.exe")
        time.sleep(2)
        # Remove lock files
        for f in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
            p = Path(PROFILE_DIR) / f
            if p.exists(): p.unlink()
        # Retry
        context = p.chromium.launch_persistent_context(...)
```

**Alternative:** Use a fresh temp directory for each run instead of a shared profile. This avoids locking issues but loses CAPTCHA solutions between runs.

## reCAPTCHA v3 Form Submission (Utah Pattern)

reCAPTCHA v3 forms do NOT work with `form.submit()` or `requestSubmit()`. The
JavaScript event handlers that inject the reCAPTCHA token are bound to the
submit button click, not the form's submit event. Use this pattern:

```python
# 1. Get reCAPTCHA v3 token via grecaptcha.execute()
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

# 2. Click the ACTUAL submit button — form.submit() does NOT work
submit_btn = pg.query_selector("input[type='submit']")
submit_btn.click()

# 3. Wait for URL change — NOT expect_navigation (which fails intermittently)
pg.wait_for_url("**/search.html**", timeout=15000)
```

**Why form.submit() fails:** The reCAPTCHA v3 token is injected by a click
handler on the submit button, not by the form's submit event. Calling
`form.submit()` bypasses the JavaScript entirely, so the token field stays
empty and the server rejects the request.

**Why expect_navigation fails:** `pg.expect_navigation()` sometimes times out
even when the page navigates successfully. Use `pg.wait_for_url()` instead —
it polls the URL and is more reliable.

**Results page structure (Utah):** After submission, the page navigates to a
new URL (e.g., `/llv/search/search.html`). Results are multi-line with ALL
CAPS names, tab-separated status lines, and profession sub-categories. The
parser must handle:
- ALL CAPS names (not just mixed case)
- Tab-separated license+status (`7946637-1501\tACTIVE`)
- Header lines that look like names ("City\tProfession\tLicense #")

```python
# Skip known header lines
skip_words = ["LICENSEE NAME", "CITY", "STATUS", "LICENSE #",
              "SEARCH RESULTS", "DO ANOTHER", "PLEASE NOTE"]
is_header = any(sw in prev.upper() for sw in skip_words)
if is_header:
    continue
```

## API Key Security

When setting up API keys (2captcha, OpenRouter, Gemini, etc.), NEVER paste keys in chat. Always use secure input:

```python
import getpass
key = getpass.getpass("Paste your API key (hidden): ").strip()
```

Or create a setup script that prompts for the key securely. Save to `.env` file, not in chat history.

**User preference:** Kevin explicitly asked "is it safe to put it here?" when considering pasting a 2captcha key. Always default to secure input for credentials.

## CDP Session for CAPTCHA Screenshot Interception

Use Chrome DevTools Protocol to intercept CAPTCHA requests and take
screenshots of CAPTCHA images for vision model analysis:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(...)
    page = context.new_page()
    
    # Create CDP session
    cdp = context.new_cdp_session(page)
    cdp.send("Network.enable")
    
    # Track CAPTCHA-related requests
    captcha_urls = []
    def on_request(params):
        url = params.get("request", {}).get("url", "")
        if "captcha" in url.lower():
            captcha_urls.append(url)
    cdp.on("Network.requestWillBeSent", on_request)
    
    page.goto("https://target-site.com/", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    
    # Take screenshot of CAPTCHA element
    captcha_img = page.query_selector("img.BDC_CaptchaImage")
    if captcha_img:
        captcha_img.screenshot(path="captcha.png")
        # Now use a vision model to read the CAPTCHA text
```

**Use case:** BotDetect CAPTCHAs (Tennessee) are image-based. CDP lets you
capture the CAPTCHA image, then use a vision-capable LLM (GPT-4V, Gemini 2.0
Flash, Claude 3.5 Sonnet) to read the text. Requires the LLM to have vision
capabilities — text-only models (MiMo, standard GPT) cannot read images.

**Limitation:** This approach requires a vision-capable model. Free options:
- Google Gemini 2.0 Flash (15 req/min free tier, may need fresh Cloud project to avoid 429)
- OpenRouter free models (`google/gemini-2.0-flash-001:free`, `qwen/qwen-2.5-vl-72b-instruct:free`) — requires free API key from openrouter.ai/keys
- Ollama + LLaVA (local, slower, 4GB download)

**Gemini 429 pitfall:** Workspace/school Google accounts share quota and hit 429 immediately. Create a NEW Google Cloud project at console.cloud.google.com → Enable Generative Language API → Create API key. Personal Gmail accounts work without this step.

## Navigate Back to Search Page Before Each Search

After clicking submit on a search form, the page changes to a results view — the search form no longer exists. The next `page.fill()` times out waiting for the field selector.

**Fix:** Before each search (except the first), navigate back to the search URL:
```python
for i, admin in enumerate(admins, 1):
    if i > 1:
        page.goto(config["url"], timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(1)
    
    # Now safe to fill the search field
    page.fill(config["selector_last"], admin_name)
    page.click(config["selector_submit"])
```

**Without this fix:** Every search after the first times out with `Timeout 30000ms exceeded. waiting for locator("#fullName")`.

## References

- `references/webwright-vision-captcha-solving.md` — Webwright + vision model approach for image CAPTCHAs, free model options, CDP screenshot pattern
- `references/graph_explorer_token.md` — Graph Explorer access token extraction
- `references/license-verification-project.md` — License verification project details

**Affected portals:** Utah (single-page-results), and any portal where the search form is replaced by results after submission.

## Angular Mat-Select Forms (Iowa Pattern)

Angular Material forms use `mat-select` elements instead of native `<select>`. Playwright cannot interact with them via `select_option()`. Instead, click the `mat-select` to open the dropdown, then click a `mat-option`:

```python
# Select Board
page.click("mat-select[name='foldertype']")
time.sleep(2)
page.click("mat-option:has-text('Nursing Home Administrators')")
time.sleep(1)

# Select License Type
page.click("mat-select[name='folderSubType']")
time.sleep(2)
page.click("mat-option:has-text('Nursing Home Administrator')")
time.sleep(1)

# Select Status
page.click("mat-select[name='status']")
time.sleep(2)
page.click("mat-option:has-text('Active')")
time.sleep(1)
```

**Pitfalls:**
- Multiple mat-selects may look identical — use `name` attribute to distinguish
- Some forms require ALL mat-selects to be filled (Iowa requires Board, License Type, City, Status)
- Wait 1-2 seconds after each selection for Angular to update the DOM
- The submit button may be hidden until all required fields are filled — use JavaScript click: `page.evaluate("document.querySelector('button[type=submit]').click()")`

## Utah Parser: Handling ALL CAPS Names and Headers

Utah's search results output names in ALL CAPS (e.g., "KIRK RODNEY PLAYER"). The parser must handle this:

```python
# ALL CAPS names with multiple words = likely a name
elif not name and prev.isupper() and len(prev.split()) >= 2:
    parts = prev.split('\t')
    name = parts[0].strip()
    city = parts[1].strip() if len(parts) > 1 else ""
```

**Header line skipping:** Lines like "City\tProfession\tLicense #" look like names but are headers:

```python
skip_words = ["LICENSEE NAME", "CITY", "STATUS", "LICENSE #",
              "SEARCH RESULTS", "DO ANOTHER", "PLEASE NOTE",
              "CLICK THE", "PUBLIC MEETINGS", "DATA REQUEST"]
is_header = any(sw in prev.upper() for sw in skip_words)
if is_header:
    continue
```

**Tab-separated status:** Some lines have `7946637-1501\tACTIVE` (license + status on one line):

```python
elif "\t" in line:
    parts = line.split("\t")
    for part in parts:
        if part.strip() in ("ACTIVE", "EXPIRED", ...):
            status = part.strip()
            for other in parts:
                if re.match(r'^\d{5,}-\d{4}$', other.strip()):
                    license_num = other.strip()
```
