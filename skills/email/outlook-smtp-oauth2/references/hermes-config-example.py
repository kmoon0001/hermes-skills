"""
Working example: Send email via Outlook SMTP with OAuth2 (MSAL).
Tested 2026-06-24 with Microsoft 365 / Exchange Online.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import msal

# --- CONFIG ---
CLIENT_ID = "6e457684-7c36-4aed-b83a-0faa37651239"
TENANT_ID = "99f33a73-3947-4753-a0b9-4956c4ad60f2"
EMAIL = "kmoon@ensignservices.net"
SMTP_SERVER = "outlook.office365.com"
SMTP_PORT = 587  # MUST be 587 + STARTTLS, NOT 465

# --- GET TOKEN ---
app = msal.PublicClientApplication(
    client_id=CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}"
)

# Try cached token first
accounts = app.get_accounts()
if accounts:
    result = app.acquire_token_silent(
        ["https://outlook.office365.com/.default"],
        account=accounts[0]
    )
else:
    result = None

if not result:
    # Device flow — user visits URL and enters code
    flow = app.initiate_device_flow(
        scopes=["https://outlook.office365.com/.default"]
    )
    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)

access_token = result["access_token"]

# --- SEND EMAIL ---
msg = MIMEMultipart()
msg["From"] = EMAIL
msg["To"] = EMAIL
msg["Subject"] = "Test Email via OAuth2"
msg.attach(MIMEText("Hello from Outlook SMTP with OAuth2!", "plain"))

server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
server.ehlo()
server.starttls()
server.ehlo()

# XOAUTH2 auth string: Ctrl-A delimited, NOT base64
auth_string = f"user={EMAIL}\x01auth=Bearer {access_token}\x01\x01"
code, response = server.docmd("AUTH", "XOAUTH2 " + auth_string)

if code == 235:
    print("AUTH successful!")
    server.sendmail(EMAIL, EMAIL, msg.as_string())
    print("Email sent!")
else:
    print(f"AUTH failed: {code} {response}")

server.quit()
