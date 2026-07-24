# Gmail SMTP for Cron Job Email Delivery

## When to Use

Any cron job that needs to deliver results via email (not just save locally). Pattern: agent compiles a report, then sends it via Python smtplib to the user's Gmail.

## Prerequisites

1. **Gmail App Password** (not regular password):
   - Requires 2-Step Verification enabled on the Google account
   - Generate at: https://myaccount.google.com/apppasswords
   - Name it something like "Hermes" for easy identification
   - It's a 16-character string (e.g., `jtbhkxzpunrjiyar`)

2. **Store credentials in `~/.hermes/.env`**:
   ```
   GMAIL_USER=kevinmoon7@gmail.com
   GMAIL_APP_PASSWORD=jtbhkxzpunrjiyar
   ```

## Sending Script (embed in cron job prompt)

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

sender = os.environ.get("GMAIL_USER")
password = os.environ.get("GMAIL_APP_PASSWORD")
recipient = sender  # send to self, or override

if not password:
    print("ERROR: GMAIL_APP_PASSWORD not set in .env")
else:
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient
    msg["Subject"] = "Your Report Subject Here"
    msg.attach(MIMEText(report_text, "plain"))

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender, password)
    server.sendmail(sender, recipient, msg.as_string())
    server.quit()
    print("Email sent successfully!")
```

## Key Details

- **Port 587 + STARTTLS** (not 465 SSL — Gmail hangs on implicit SSL)
- **No `from` field needed** — Gmail overrides it with the authenticated account
- **App passwords bypass 2FA** — that's the whole point, no OAuth dance needed
- **Cron jobs run with `skip_memory=True`** by default — env vars from `.env` are loaded at startup, so `os.environ.get()` works
- **Test first** — always send a test email before scheduling the cron job

## Cron Job Integration

Update the cron job prompt to include the email send at the end:

```
AFTER compiling the report, send it via email using Python smtplib.
Use the GMAIL_USER and GMAIL_APP_PASSWORD env vars.
Subject line: "Subject: 📧 Your Report Title"
```

## Pitfalls

- **App password expires if 2FA is disabled** — keep 2FA on
- **Gmail rate limits** — ~500 emails/day for free accounts, more than enough for weekly reports
- **Spam filtering** — emails from your own address to yourself usually land in inbox, not spam. If they go to spam, check the sender/recipient match
- **`hermes update` can break `.env`** — the update process rewrites `.env`. Always re-verify credentials after a hermes update: `grep GMAIL ~/.hermes/.env`
