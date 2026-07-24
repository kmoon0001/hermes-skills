@echo off
cd /d D:\license-verification
REM Optional: set SMTP_USER and SMTP_PASSWORD as system env vars for email alerts
python run_nightly.py
REM Exit with same code as python process
exit /b %ERRORLEVEL%
