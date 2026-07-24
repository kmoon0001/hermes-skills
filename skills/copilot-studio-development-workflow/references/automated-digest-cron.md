# Automated Digest Cron — Setup Guide

For ongoing monitoring of Copilot Studio, Power Platform, Hermes, and AI agent development news, this cron job searches broadly, compiles a structured digest, and delivers it. Created for the user's "AI Agent Dev Weekly Digest" job.

## Prerequisites

1. Hermes cron system enabled
2. For email delivery: Gmail App Password + Python smtplib

## Gmail Email Setup (one-time)

```bash
# 1. Get App Password from https://myaccount.google.com/apppasswords
# 2. Create credentials file at:
#    ~/AppData/Local/hermes/profiles/<profile>/secrets/gmail_creds.py
EMAIL = "your@email.com"
APP_PASSWORD = "xxxx xxxx xxxx xxxx"

# 3. Create send script at scripts/send_digest.py
```

## Cron Job Creation

```bash
# Create the job
hermes cron create \
  --name "AI Agent Dev Weekly Digest" \
  --schedule "0 9 * * 1,4" \
  --prompt "Research and compile a digest of latest news..."
```

## Prompt Structure

The cron prompt should have three phases:

1. **Research** — search each domain separately using web_search + web_extract
2. **Compile** — format into a structured digest with sections and links
3. **Send** — pipe the compiled text through the send script, then output in final response

## Delivery

- `deliver: local` — output appears in the origin conversation
- Or use the send script for email: have the cron agent run `echo "DIGEST" | python scripts/send_digest.py`

## Search Areas

- Microsoft Copilot Studio / Power Platform updates
- Hermes Agent releases (GitHub)
- AI agent development tools and MCP
- Free AI models / OpenRouter / Codex
- Google News for relevant industry stories
