@echo off
REM ============================================================================
REM Project Setup — One-Click Windows Task Scheduler Configuration
REM Template: replace PROJECT_NAME, PYTHON_SCRIPT paths, and task schedules.
REM ============================================================================
setlocal enabledelayedexpansion

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo ============================================================
echo   PROJECT_NAME Production Setup
echo   Project: %PROJECT_DIR%
echo ============================================================
echo.

REM ── Validate prerequisites ──────────────────────────────────────────────
if not exist "%PROJECT_DIR%\.venv\Scripts\python.exe" (
    echo [FAIL] Virtual environment not found
    echo   Run: python -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Virtual environment found

REM ── Create logs directory ───────────────────────────────────────────────
if not exist "%PROJECT_DIR%\logs" mkdir "%PROJECT_DIR%\logs"
echo [OK] Logs directory ready

set "PY=%PROJECT_DIR%\.venv\Scripts\python.exe"

REM ── Remove old tasks (idempotent) ──────────────────────────────────────
schtasks /delete /tn "PROJECT_NAME Daily Task" /f 2>nul
schtasks /delete /tn "PROJECT_NAME Watchdog" /f 2>nul

REM ── Task 1: Daily Runner (10:00 AM) ────────────────────────────────────
schtasks /create /tn "PROJECT_NAME Daily Task" /sc daily /st 10:00 /f /tr "%PY% %PROJECT_DIR%\main.py" 2>&1
if errorlevel 1 (echo [FAIL] Daily Task) else (echo [OK] Daily Task - 10:00 AM)

REM ── Task 2: Hourly Watchdog ────────────────────────────────────────────
schtasks /create /tn "PROJECT_NAME Watchdog" /sc hourly /f /tr "%PY% %PROJECT_DIR%\watchdog.py --alert-only" 2>&1
if errorlevel 1 (echo [FAIL] Watchdog) else (echo [OK] Watchdog - every hour)

echo.
echo ============================================================
echo   Setup complete!
echo   View tasks:  taskschd.msc
echo   Test now:    schtasks /run /tn "PROJECT_NAME Watchdog"
echo ============================================================
pause
exit /b 0
