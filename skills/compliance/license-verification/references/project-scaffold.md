# Project Scaffold — License Verification

## Repository
https://github.com/kmoon0001/license-verification

## Folder Layout
```
D:/license-verification/
├── config.json              # Email, paths, state scraper map
├── verify_licenses.py       # Main script: read → verify → report → email
├── bootstrap.py             # Excel → CMS matching
├── states/                  # One scraper per state (17 total)
│   ├── alabama.py           # ✅ ASP.NET WebForms
│   ├── alaska.py            # 🚫 HTTP 403
│   ├── arizona.py           # ✅ NCIA Board (Thentia Cloud)
│   ├── california.py        # ⚠️ ASP.NET WebForms
│   ├── colorado.py          # 🚫 CAPTCHA
│   ├── idaho.py             # ⚠️ DOPL search
│   ├── iowa.py              # ⚠️ Amanda Portal
│   ├── kansas.py            # ⚠️ KSBN search
│   ├── nebraska.py          # 🚫 reCAPTCHA
│   ├── nevada.py            # 🚫 SSL cert error
│   ├── oregon.py            # ⚠️ OHLO search
│   ├── south_carolina.py    # ⚠️ LLR search
│   ├── tennessee.py         # 🚫 CAPTCHA
│   ├── texas.py             # ✅ TULIP LWC shadow DOM
│   ├── utah.py              # 🚫 reCAPTCHA
│   ├── washington.py        # ⚠️ HELMS search
│   └── wisconsin.py         # ⚠️ License Lookup search
├── reports/                 # Output Excel reports
├── docs/                    # Steering docs, verification log
│   ├── steering.md
│   └── verification-log.md
└── .gitignore
```

## State Scraper Interface
Every scraper must match:
```python
def verify_<state>(admin_name: str) -> dict:
    return {
        "status": "Active|Inactive|Expired|NOT FOUND|ERROR|BLOCKED",
        "expiration": "MM/DD/YYYY|YYYY-MM-DD|",
        "url": "https://...",
        "note": "...",
        "days_until_expiry": int | None
    }
```

## Git Workflow
1. Test each state individually with a real admin name
2. Commit after each verified state
3. Push to GitHub after each commit
4. Update docs/verification-log.md with results
