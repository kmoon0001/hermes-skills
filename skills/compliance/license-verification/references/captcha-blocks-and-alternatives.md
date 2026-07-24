# CAPTCHA Blocks, PDF Rosters, and Paid Data (2026-06-23)

## States that were "blocked" but now work

### Nebraska — PDF Roster (FREE)
- **URL:** https://dhhs.ne.gov/licensure/Documents/LTCRoster.pdf
- **Format:** PDF with facility names, administrator names, license numbers
- **Updated:** Monthly, on or about the 15th
- **Requires:** `pip install pdfplumber`
- **Verified:** Kristie Kallemeyn #324003, Alice Smith #034001
- **Key pattern:** Search for "Name, Administrator" in text → look backward for 6-digit license number on FAX line → extract facility name from "Total Licensed" line

## States blocked by reCAPTCHA/CAPTCHA (cannot automate)

| State | Blocker | Alternative |
|-------|---------|-------------|
| Alaska | HTTP 403 | None found |
| Colorado | CAPTCHA | None found |
| Nevada | SSL cert error | None found |
| South Carolina | reCAPTCHA | None found |
| Tennessee | CAPTCHA | None found |
| Utah | reCAPTCHA | Paid data download ($0.01/record) |
| Washington | reCAPTCHA | None found |

## Utah Paid Data Download
- **URL:** https://secure.utah.gov/datarequest/professionals/index.html
- **Cost:** $0.01/record, min $5 for first 200
- **Profession:** "Health Facility Administrator"
- **Includes:** Name, License Type, License Status
- **With approval:** Address, Phone, Email
- **Use case:** 32 UT facilities × $0.01 = $0.32/month after $5 setup

## CAPTCHA-Solving Services (if needed later)
- 2Captcha: ~$3/1,000 CAPTCHAs
- Anti-Captcha: ~$1-3/1,000
- CapSolver: specialized in reCAPTCHA/hCaptcha
- Cost for 426 facilities: ~$1.28/month
- Ethical consideration: public license lookups, not high-security systems
