# Semi-Automated Browser for CAPTCHA States

## Overview

When state licensing portals block automation with reCAPTCHA/CAPTCHA, the free workaround is a semi-automated browser:
1. Tool opens a real Chrome window
2. User solves ONE CAPTCHA manually
3. Tool automatically searches all admin names for that state
4. Results saved to JSON

This requires zero API keys, zero cost, and only ~1 minute of manual work per state per month.

## Why Other Approaches Fail

| Approach | Result |
|----------|--------|
| playwright-stealth / anti-detection | Does NOT bypass reCAPTCHA v3. Only hides automation flags. |
| SeleniumBase CDP | Launches stealthy Chrome but reCAPTCHA still blocks. |
| Persistent Chrome profile + storage state | ReCAPTCHA v3 re-evaluates every load. Saved cookies don't help. |
| Residential proxy (without manual solve) | Helps IP reputation but doesn't solve the CAPTCHA challenge itself. |

reCAPTCHA v3 scores on IP reputation + cookie history + behavioral patterns. Datacenter IPs get flagged. The only free path is letting a human solve the challenge once.

## Usage

```bash
cd D:/license-verification
python semi_auto.py
```

1. The script shows available CAPTCHA states and admin counts
2. Pick a state
3. A Chrome window opens to the state's lookup page
4. Solve the CAPTCHA if present
5. Press ENTER when the search form is visible
6. The tool fills each name and searches
7. Results save to `results/STATE_semi_auto.json`

## State Configs

| State | URL | Last Name Selector | First Name Selector | Submit Selector |
|-------|-----|--------------------|---------------------|-----------------|
| South Carolina | https://verify.llronline.com/LicLookup/LTC/LTC.aspx?div=35 | #ctl00_ContentPlaceHolder1_UserInputGen_txt_lastName | #ctl00_ContentPlaceHolder1_UserInputGen_txt_firstName | #ctl00_ContentPlaceHolder1_btn_find |
| Tennessee | https://verify.tn.gov/ | #-33701226759 | #177334431563 | button:has-text("Search") |
| Utah | https://secure.utah.gov/llv/search/index.html | #fullName | #fullName (same field) | input[type='submit'][value='Search'] |
| Washington | https://wahelms.my.site.com/s/license-search | #lastName | #firstName | button:has-text('Search') |
| Kansas | https://prolicenseverify.ks.gov/ | #lastName | #firstName | button:has-text('Search') |

Notes:
- TN uses auto-generated negative IDs. Verified via label association: label "Last Name" → id=-33701226759, label "First Name" → id=177334431563.
- UT uses a single `#fullName` text field (full name, not separate first/last).
- UT has 420 total inputs on the page; use the specific selectors above.
- WA uses Salesforce Lightning-style page with standard text inputs.
- KS uses standard HTML form inputs.

## Admin Counts (from ENSG Excel)

- South Carolina: 9 admins
- Tennessee: 11 admins
- Utah: 32 admins
- Washington: 18 admins
- Kansas: 17 admins

## Chrome Profile

The script uses `D:/license-verification/chrome_profile` as a persistent Playwright context. This preserves cookies between runs but does NOT bypass reCAPTCHA v3 — it only means you don't have to log in again if the site has a login step.

## Limitations

- reCAPTCHA v3 may challenge you even with cookies/IP reputation
- Some sites use bot-detection beyond reCAPTCHA (e.g., WA uses Salesforce which may fingerprint the browser)
- If the site aggressively flags Playwright, you may need to run with headless=False in a visible Chrome window and interact normally
- This is NOT a fully automated solution — it requires ~5 minutes of manual work per state per month

## Error Handling

If the submit button click fails because the element is hidden:
- The user didn't solve the CAPTCHA yet
- Or the site has additional anti-bot measures

The script does not auto-retry hidden buttons. It is the user's responsibility to ensure the search form is ready before pressing ENTER.
