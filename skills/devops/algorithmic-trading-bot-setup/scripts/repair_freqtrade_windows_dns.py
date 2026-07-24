#!/usr/bin/env python3
"""Use Windows system DNS for aiohttp when the pycares diagnostic split is proven.

Run with the Freqtrade virtual environment's Python. Idempotent. This keeps
aiodns/pycares installed for ccxt dependency integrity while changing aiohttp's
default resolver inside this isolated environment.
"""
from pathlib import Path
import aiohttp

resolver = Path(aiohttp.__file__).with_name("resolver.py")
old = "DefaultResolver: _DefaultType = AsyncResolver if aiodns_default else ThreadedResolver"
new = "DefaultResolver: _DefaultType = ThreadedResolver"
text = resolver.read_text(encoding="utf-8")

if new in text:
    print(f"Already configured: {resolver}")
elif old in text:
    resolver.write_text(text.replace(old, new), encoding="utf-8")
    print(f"Configured Windows system DNS resolver: {resolver}")
else:
    raise SystemExit(
        f"Expected aiohttp resolver assignment not found in {resolver}. "
        "Do not patch blindly; inspect the installed aiohttp version."
    )
