---
name: outlook-smtp-oauth2
description: "Configure SMTP email with OAuth2 authentication for Microsoft Outlook/Exchange (Microsoft 365). Covers MSAL token acquisition, XOAUTH2 string format, and Hermes config.json setup. Use when sending email via Outlook SMTP with OAuth2 instead of basic auth."
version: 1.0.0
author: community
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Email, SMTP, OAuth2, Outlook, Exchange, Microsoft365]
prerequisites:
  commands: [python3]
  python_packages: [msal]
---

# Outlook SMTP with OAuth2 Authentication

Configure SMTP email sending through Microsoft 365 / Outlook using OAuth2 tokens instead of basic auth (which Microsoft is deprecating).

## Critical Pitfalls

1. **Port 465 (SSL) silently hangs.** Outlook SMTP does NOT support implicit SSL on port 465. The connection appears to open but never completes the handshake. Always use **port 587 with STARTTLS**.

2. **XOAUTH2 uses Ctrl-A delimiters, NOT base64.** The XOAUTH2 auth string format is:
   ```
   user={email}\x01auth=Bearer {token}\x01\x01
   ```
   where `\x01` is the ASCII SOH character (Ctrl-A, byte 0x01). This is NOT base64-encoded — it's sent as a raw byte string. Python example:
   ```python
   auth_string = f"user={email}\x01auth=Bearer {token}\x01\x01"
   ```

3. **MSAL scope for Outlook SMTP** is `https://outlook.office365.com/.default` (not the Graph API scope).

## MSAL Token Acquisition

```python
import msal

app = msal.PublicClientApplication(
    client_id="YOUR_CLIENT_ID",
    authority=f"https://login.microsoftonline.com/YOUR_TENANT_ID"
)

# Device flow (interactive, no redirect URI needed)
flow = app.initiate_device_flow(scopes=["https://outlook.office365.com/.default"])
print(flow["message"])  # User visits URL + enters code
result = app.acquire_token_by_device_flow(flow)
access_token = result["access_token"]
```

## SMTP Connection (Python smtplib)

```python
import smtplib
import base64

server = smtplib.SMTP("outlook.office365.com", 587)
server.ehlo()
server.starttls()
server.ehlo()

# XOAUTH2 auth string — Ctrl-A delimited, NOT base64
auth_string = f"user={email}\x01auth=Bearer {access_token}\x01\x01"
code, response = server.docmd("AUTH", "XOAUTH2 " + auth_string)
```

## Hermes config.json Setup

For Hermes Agent's built-in email alerts feature:

```json
{
  "email": {
    "provider": "custom",
    "smtp_server": "outlook.office365.com",
    "smtp_port": 587,
    "use_tls": true,
    "smtp_user": "GRAPH_USER",
    "from_address": "yourname@yourdomain.com"
  }
}
```

- `provider: "custom"` tells Hermes to use the specified SMTP settings
- `smtp_user: "GRAPH_USER"` — Hermes checks env var `SMTP_USER` for the username
- Access token must be refreshed before each send (MSAL handles caching)
- Creds can be in env vars (`SMTP_USER`, `SMTP_PASSWORD`) or config.json fields

## Full Working Example

See `references/hermes-config-example.py` for a complete script that acquires an MSAL token and sends email through Hermes-compatible SMTP.

## Common Errors

| Symptom | Cause | Fix |
|---------|-------|-----|
| Connection hangs on port 465 | Outlook doesn't support implicit SSL | Use port 587 + STARTTLS |
| `535 5.7.3 Authentication unsuccessful` | Wrong auth format | Use Ctrl-A delimited XOAUTH2, not base64 |
| `AADSTS65001` | User hasn't consented to app | Admin consent or user consent flow needed |
| Token expired | Access tokens expire in ~1 hour | Use MSAL's token cache with refresh tokens |
