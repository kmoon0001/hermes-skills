# Data Request / Download Intake Automation

Use this when a CAPTCHA-blocked state offers a roster/data export or sends a public-records/data-request response by email.

## Goal

Avoid re-searching CAPTCHA portals. Kevin completes any payment/CAPTCHA/browser checkout manually, then the project automates the repeatable parts:

1. detect/download/import the roster file,
2. parse it into a state supplemental workbook,
3. merge that workbook into the final max-coverage report,
4. keep browser payment/CAPTCHA out of automation.

## Project Files

- Main script: `D:/license-verification/data_request_automation.py`
- User helper: `D:/license-verification/import_data_request_downloads.cmd`
- Imported files: `D:/license-verification/cache/data_requests/<STATE>/received/`
- Email drafts: `D:/license-verification/cache/data_requests/email_drafts/`
- Utah supplemental output: `D:/license-verification/results/utah_roster_refresh_*.xlsx`

## User-Facing Flow

When Kevin downloads a Utah DOPL export/roster:

```bat
D:\license-verification\import_data_request_downloads.cmd
```

Equivalent terminal command:

```bash
cd D:/license-verification
python data_request_automation.py --scan-downloads --hours 72 --build-supplements --build-final --open-final
```

This scans `C:/Users/kevin/Downloads`, imports roster-like files, builds supplemental workbooks, rebuilds the final report, and opens Excel.

## Email Drafts

Create data-request drafts without sending:

```bash
cd D:/license-verification
python data_request_automation.py --create-email-drafts --draft-states UTAH,TENNESSEE,ALASKA
```

Drafts are `.eml` files under `cache/data_requests/email_drafts/`. Kevin can open/review/send them himself.

## Email Attachment Polling

The script supports IMAP attachment polling, but do not ask Kevin to paste passwords in chat. Configure environment variables locally instead:

```bash
export IMAP_HOST=...
export IMAP_USER=...
export IMAP_PASSWORD=...
python data_request_automation.py --poll-email --email-days 30 --build-supplements --build-final
```

## Utah Roster Parsing

For Utah, CSV/XLSX rows are matched to ENSG Utah admins by normalized first/last name. The parser looks for flexible column labels:

- name: `Licensee Name`, `Full Name`, `Name`, or first/last columns
- license: `License Number`, `License #`, `Credential Number`, etc.
- status: `Status`, `License Status`, `Credential Status`
- expiration: `Expiration`, `Expire`, `Renewal`, `Expiry`

Rows are filtered toward Health Facility Administrator/NHA/HFA when possible.

Normal final builds still gate Utah as manual. The data-request automation final build intentionally overrides manual states to `ALASKA,TENNESSEE` only so a roster-backed Utah supplemental workbook can win.

## Ad-Hoc Verification Pattern

When this workflow is edited and there is no canonical test suite, create a temporary verification script using Python `tempfile` under `C:/Users/kevin/AppData/Local/Temp` with prefix `hermes-verify-`.

A good offline verification script should:

1. `py_compile` `data_request_automation.py`.
2. Assert `config.json` contains `utah_roster_refresh_*.xlsx` in `final_report.supplemental_report_patterns`.
3. Assert `import_data_request_downloads.cmd` calls the expected flags.
4. Monkeypatch/fake `cms_data` to avoid network/cache side effects.
5. Redirect `CACHE_DIR`, `RESULTS_DIR`, and `DOWNLOADS_DIR` to a temporary directory.
6. Create request drafts and assert `.eml` files exist.
7. Read a couple of real Utah admins from the master Excel.
8. Create a temporary Utah roster in the fake Downloads directory.
9. Run `scan_downloads()` and `maybe_build_supplements()`.
10. Open the generated workbook and assert `Detailed Results` exists and the sample admins are `PASS`.
11. Delete the temporary verification script and any fake project files if the test did not run in isolated paths.

Report this explicitly as **ad-hoc targeted verification**, not full suite green.

## Pitfalls

- Do not automate payment or CAPTCHA checkout. Kevin should complete those in the browser.
- Do not merge fake/test roster files into real `results/`; use isolated temp directories or delete artifacts immediately.
- Do not force Utah out of manual review in the normal `build_final_max_coverage.py` path. Only roster-backed data-request automation should do that.
- Do not store mailbox credentials in code/config or ask Kevin to paste them in chat.
