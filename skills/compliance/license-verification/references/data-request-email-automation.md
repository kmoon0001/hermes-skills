# Data Request Email + Download Automation Notes

Use this reference when automating ENSG license roster/data-request intake for states where the website is manual-gated, paid, CAPTCHA-gated, or sends exports by email.

## Current durable pattern

1. Do not automate paid checkout/CAPTCHA pages unless explicitly asked and technically validated. For Utah, the safer path is:
   - Kevin completes the state purchase/download or request form in the browser.
   - The export either downloads to `C:/Users/kevin/Downloads` or arrives as a Gmail attachment.
   - Run the intake automation to import, parse, build supplement, and rebuild the final report.

2. Use `D:/license-verification/data_request_automation.py` for intake:
   - Downloaded file path:
     `python data_request_automation.py --scan-downloads --hours 72 --build-supplements --build-final --open-final`
   - Email attachment path:
     `python data_request_automation.py --poll-email --email-days 30 --max-emails 50 --build-supplements --build-final --open-final`
   - Create request drafts:
     `python data_request_automation.py --create-email-drafts --draft-states UTAH,TENNESSEE,ALASKA`

3. For Gmail/ENSG switching, use `D:/license-verification/email_settings.py`:
   - Gmail profile:
     `python email_settings.py --imap-profile gmail --smtp-profile gmail --report-to kevinmoon7@gmail.com,lee85lisa@gmail.com --show`
   - ENSG profile:
     `python email_settings.py --imap-profile ensg --smtp-profile ensg --report-to kevinmoon7@gmail.com,lee85lisa@gmail.com --show`
   - Desktop helpers: `use_gmail_email_settings.cmd`, `use_ensg_email_settings.cmd`.

4. Gmail credentials:
   - `IMAP_HOST=imap.gmail.com`
   - `IMAP_PORT=993`
   - `IMAP_USER=kevinmoon7@gmail.com`
   - `IMAP_FOLDER=INBOX`
   - `SMTP_USER=kevinmoon7@gmail.com`
   - `SMTP server=smtp.gmail.com`, port 587 STARTTLS.
   - Gmail needs a 16-character Google App Password for `IMAP_PASSWORD` and `SMTP_PASSWORD`; the normal Google password usually fails.
   - Never ask Kevin to paste the app password into chat. Open `D:/license-verification/.env` in Notepad and have him enter it locally.
   - Verify without printing secrets: check presence/length and attempt IMAP/SMTP login with redacted errors.

5. Important performance pitfall:
   - IMAP polling across a large inbox can hang or time out if every message is fetched.
   - Keep `--max-emails` bounded, typically 25-75, and search recent days only.

## User interaction pattern

Kevin prefers hands-on progress and minimal explanation. When he asks to pull up `.env`, open it in Notepad immediately using the Windows notepad opener pattern, then give only the exact lines to edit. Do not ask him to share passwords.

## Verification pattern

When changing this workflow, create an ad-hoc verification script under `C:/Users/kevin/AppData/Local/Temp` using prefix `hermes-verify-`, run it, and delete it. Summarize as ad-hoc verification, not suite green.

Useful checks:
- `py_compile` for changed Python files.
- Config has expected recipients and supplemental report patterns.
- `.env` contains non-secret host/user/port/folder settings.
- Email settings helper prints redacted settings.
- For credentials, attempt real IMAP/SMTP login but never print password values.

## Current recipient convention

Reports should include both:
- `kevinmoon7@gmail.com`
- `lee85lisa@gmail.com`

Keep this configurable through `email_settings.py`/`config.json`, not hard-coded into report generation logic.