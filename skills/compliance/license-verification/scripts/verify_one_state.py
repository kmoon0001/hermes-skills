#!/usr/bin/env python
"""Verify a single state scraper against one admin name."""
import sys
from pathlib import Path

# Allow running from skill dir or repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "license-verification"))

state_module = sys.argv[1] if len(sys.argv) > 1 else "texas"
admin_name = sys.argv[2] if len(sys.argv) > 2 else "Test Admin"

try:
    mod = __import__(f"states.{state_module}", fromlist=["verify"])
    result = mod.verify(admin_name)
    print(result)
except Exception as e:
    print({"status": "ERROR", "note": str(e)})
