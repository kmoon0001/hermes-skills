#!/usr/bin/env python3
"""
Watchdog — reusable health monitor skeleton.

Drop-in pattern for any project. Replace the check_* functions with your own.
Stdlib-only. Exit codes: 0=OK, 1=WARNING, 2=CRITICAL.

Usage:
    python watchdog.py              # compact status line
    python watchdog.py --verbose    # full report
    python watchdog.py --alert-only # silent when OK (for cron/Task Scheduler)
    python watchdog.py --json       # machine-readable output
    python watchdog.py --restart    # auto-restart main app if down
    python watchdog.py --notify     # Windows toast notification on problems
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

# ── Configuration ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
HEARTBEAT_FILE = ROOT / ".watchdog_heartbeat"

# Pacific time (adjust as needed)
PT_OFFSET = timezone(timedelta(hours=-7))


# ── Helpers ────────────────────────────────────────────────────────────────

def now_pt() -> str:
    return datetime.now(PT_OFFSET).strftime("%Y-%m-%d %H:%M PT")


def write_heartbeat() -> None:
    try:
        HEARTBEAT_FILE.write_text(datetime.now(timezone.utc).isoformat())
    except OSError:
        pass


def load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _api_call(url: str, timeout: int = 5) -> tuple[int, dict | None]:
    """Returns (http_code, parsed_json_or_None). 0 = connection refused."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "watchdog/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode()
            try:
                return resp.status, json.loads(body)
            except json.JSONDecodeError:
                return resp.status, {"raw": body[:200]}
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode()
            return e.code, json.loads(body)
        except Exception:
            return e.code, None
    except urllib.error.URLError:
        return 0, None
    except Exception:
        return 0, None


def send_windows_toast(title: str, message: str) -> bool:
    """Send a Windows 10/11 toast notification. Returns True on success."""
    if sys.platform != "win32":
        return False
    ps_script = f'''
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$textNodes = $template.GetElementsByTagName("text")
$textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
$textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null
$toast = [Windows.UI.Notifications.ToastNotification]::new($template)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Watchdog").Show($toast)
'''
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


# ── Check functions ────────────────────────────────────────────────────────
# Each returns (level: str, message: str, info: dict)
# level must be one of: 'ok', 'warning', 'critical', 'info'

def check_app_health() -> tuple[str, str, dict]:
    """Ping the main application. Replace URL with your app's health endpoint."""
    code, data = _api_call("http://localhost:8080/api/v1/ping")
    if code in (200, 401, 403):
        return "ok", "App is running", {"http_code": code}
    elif code == 0:
        return "critical", "App is DOWN — connection refused", {}
    else:
        return "critical", f"App returned HTTP {code}", {}


def check_disk(min_free_gb: int = 10) -> tuple[str, str, dict]:
    """Check free disk space on the project volume."""
    import shutil
    info = {}
    try:
        usage = shutil.disk_usage(str(ROOT))
        free_gb = usage.free / (1024 ** 3)
        info["free_disk_gb"] = round(free_gb, 1)
        info["total_disk_gb"] = round(usage.total / (1024 ** 3), 1)
    except OSError:
        info["free_disk_gb"] = None

    free = info.get("free_disk_gb")
    if free is not None and free <= min_free_gb:
        return "critical", f"Only {free:.1f}GB free", info
    elif free is not None and free <= min_free_gb * 2:
        return "warning", f"Low disk: {free:.1f}GB free", info
    else:
        return "ok", f"Free: {free:.0f}GB" if free else "Disk check unavailable", info


# ── Add your own check functions here ──────────────────────────────────────
# def check_data_freshness() -> tuple[str, str, dict]: ...
# def check_equity() -> tuple[str, str, dict]: ...
# def check_pipeline() -> tuple[str, str, dict]: ...


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Watchdog")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--alert-only", action="store_true")
    parser.add_argument("--restart", action="store_true")
    parser.add_argument("--notify", action="store_true")
    args = parser.parse_args()

    write_heartbeat()

    # ── Run checks ──────────────────────────────────────────────────────
    checks: list[tuple[str, str, str, dict]] = []
    for name, fn in [
        ("app", check_app_health),
        ("disk", lambda: check_disk(10)),
        # Add your checks here
    ]:
        level, msg, info = fn()
        checks.append((name, level, msg, info))

    # ── Determine overall status ────────────────────────────────────────
    all_levels = [c[1] for c in checks]
    if "critical" in all_levels:
        overall, exit_code = "CRITICAL", 2
    elif "warning" in all_levels:
        overall, exit_code = "WARNING", 1
    else:
        overall, exit_code = "OK", 0

    # Toast on problems
    if args.notify and overall in ("WARNING", "CRITICAL"):
        issues = [(n, l, m) for n, l, m, _ in checks if l in ("warning", "critical")]
        msg = " | ".join(f"{n}: {m}" for n, _, m in issues[:5])
        send_windows_toast(f"Watchdog: {overall}", msg[:250])

    # Silent when OK in alert-only mode
    if args.alert_only and overall == "OK":
        return 0

    # ── Output ──────────────────────────────────────────────────────────
    if args.json:
        print(json.dumps({
            "status": overall,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {n: {"level": l, "message": m, "info": i} for n, l, m, i in checks},
        }, indent=2))
    elif args.verbose:
        print(f"{'='*55}")
        print(f"  WATCHDOG — {now_pt()}")
        print(f"{'='*55}")
        for name, level, msg, info in checks:
            tag = level.upper().ljust(8)
            print(f"  [{tag}] {name.ljust(10)} {msg}")
            if info and level in ("warning", "critical"):
                for k, v in info.items():
                    print(f"         {k}: {v}")
        print(f"{'='*55}")
        print(f"  Overall: {overall}")
    else:
        parts = []
        for name, level, *_ in checks:
            icon = {"ok": "✓", "warning": "⚠", "critical": "✗", "info": "ℹ"}.get(level, "?")
            parts.append(f"{icon}{name}")
        status_line = f"[{overall}] {' '.join(parts)} | {now_pt()}"
        issues = [(n, l, m) for n, l, m, _ in checks if l in ("warning", "critical")]
        if issues:
            detail = " | ".join(f"{n}: {m}" for n, _, m in issues)
            print(f"{status_line}\n  {detail}")
        else:
            print(status_line)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
