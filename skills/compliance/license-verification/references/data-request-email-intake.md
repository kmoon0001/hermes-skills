# ENSG Data Request Email/Download Intake

Session-derived implementation notes for automating state roster/data-request intake without automating CAPTCHA/payment checkout.

## Files in `D:/license-verification`

- `data_request_automation.py`
  - Loads `.env` from the project directory via `python-dotenv` when available.
  - Creates `.eml` request drafts with `--create-email-drafts`.
  - Imports roster-like files from Downloads with `--scan-downloads --hours 72`.
  - Imports a specific file with `--import-file <path> --state UTAH`.
  - Polls IMAP attachments with `--poll-email` when `IMAP_*` env vars are configured.
  - Builds Utah supplemental workbooks from CSV/XLSX roster imports with `--build-supplements`.
  - Rebuilds the final workbook with `--build-final`, merging `utah_roster_refresh_*.xlsx` and not forcing Utah to manual review in that path.

- `email_settings.py`
  - Manages non-secret account/profile settings.
  - Gmail profile command:
    `python email_settings.py --imap-profile gmail --smtp-profile gmail --report-to kevinmoon7@gmail.com,lee85lisa@gmail.com --show`
  - ENSG/M365 profile command:
    `python email_settings.py --imap-profile ensg --smtp-profile ensg --report-to kevinmoon7@gmail.com,lee85lisa@gmail.com --show`
  - Does not print or request passwords.

- `import_data_request_downloads.cmd`
  - User-facing one-click helper: scans Downloads, builds supplements, builds final, opens workbook.

- `use_gmail_email_settings.cmd` / `use_ensg_email_settings.cmd`
  - Switch non-secret email profile settings.

## Gmail settings used for temporary intake/sending

`.env` non-secret values:

```env
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
IMAP_USER=kevinmoon7@gmail.com
IMAP_FOLDER=INBOX
SMTP_USER=kevinmoon7@gmail.com
```

`config.json` email sending values:

```json
{
  "email": {
    "to": ["kevinmoon7@gmail.com", "lee85lisa@gmail.com"],
    "from": "kevinmoon7@gmail.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": true
  }
}
```

Secret values are only local and must not be pasted in chat:

```env
IMAP_PASSWORD=<Google app password>
SMTP_PASSWORD=<Google app password>
```

Google app passwords are normally 16 characters after removing spaces. The normal Gmail password usually will not work for raw IMAP/SMTP.

## Validation pattern

When Kevin asks to double-check credentials, do not print secrets. Use a redacted/static check and safe login probes:

- Confirm required `.env` keys exist.
- For passwords, print only present/length/space status.
- Test IMAP with `imaplib.IMAP4_SSL(host, 993).login(user, password)`.
- Test SMTP with `smtplib.SMTP('smtp.gmail.com', 587).starttls(); login(user, password)`.
- Redact username/password from any exception text before reporting.

Successful session result for Gmail profile:

```text
STATIC_CHECK=PASS
IMAP_LOGIN_TEST=PASS
SMTP_LOGIN_TEST=PASS
```

## User-facing answer for Utah data request effort

- Manual Utah data request/download: low-to-medium difficulty. First run about 10–25 minutes because of form/payment/download; later runs about 2–5 minutes.
- Fully automating state checkout/payment/CAPTCHA is not worth it and should not be the default path.
- Preferred workflow: Kevin completes browser payment/download or receives the email; automation imports the downloaded/attached roster, builds the Utah supplemental workbook, and rebuilds the final report.

## Pitfalls

- Do not create fake/test roster files in project result directories without cleaning them up before final report generation.
- Do not automate payment/CAPTCHA checkout unless explicitly requested and legally/operationally approved.
- Do not ask Kevin to paste passwords in chat; ask him to enter them directly into `.env`/Notepad or browser prompts.
- If opening `.env`, use Notepad via `cmd.exe /c start notepad "D:\license-verification\.env"`.
