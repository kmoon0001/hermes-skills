# Utah DOPL Data Request / Roster Cost Control

Use this when ENSG Utah Health Facility Administrator verification is blocked by the public lookup/reCAPTCHA path and the user considers buying a Utah DOPL data request roster.

## Key discovery

Utah's DOPL data request page can overcharge if the parent profession checkbox is used without limiting child type/status.

Data request page:
`https://secure.utah.gov/datarequest/professionals/index.html`

Useful form values observed:
- Parent Health Facility Administrator group: `professionTypes=_231p`
  - includes Health Facility Administrator + Temporary Health Facility Administrator
  - with all statuses produced 1,691 records / about $49.73
- Specific Health Facility Administrator only: `professionTypes=231_232l`
  - all statuses produced 1,680 records / about $49.40
  - Active only produced 410 records / about $11.30
- Temporary Health Facility Administrator only: `professionTypes=231_233l`
  - produced 11 records / minimum $5.00
- Active status: `licenseStatuses=481`
- Expired status: `licenseStatuses=483`

Recommended paid selection:
1. Uncheck all profession boxes.
2. Check only the child license type `Health Facility Administrator` (`231_232l`), not the parent group.
3. Check only `Active` registration status (`481`).
4. Choose `without address/phone/email`.
5. Choose Excel format unless record count exceeds Excel limit.
6. One-time list only unless the user explicitly wants recurring list charges.

This yields a statewide active-HFA roster that is much cheaper and sufficient for ENSG matching.

## User preference / approach

Kevin does not want unnecessary paid bulk data. Before buying:
- Count ENSG Utah rows from the master workbook.
- If only a few admins are needed, try targeted public lookup first.
- If buying is justified, use Active HFA-only, not all statuses and not the full parent profession group.

Observed ENSG workbook at the time had 32 Utah facility/admin rows and 29 unique Utah admins, so targeted lookup may be viable.

## Automation notes

Existing helper:
`D:/license-verification/data_request_automation.py`

For email/download intake after the Utah roster is bought or emailed:

```bash
cd D:/license-verification
python data_request_automation.py --poll-email --email-days 30 --max-emails 50 --build-supplements --build-final --open-final
```

For downloaded files:

```bash
D:/license-verification/import_data_request_downloads.cmd
```

Gmail profile helper:
`D:/license-verification/email_settings.py`

Do not print or ask for passwords in chat. Kevin successfully configured Gmail app password locally; verify presence/login without exposing secrets.
