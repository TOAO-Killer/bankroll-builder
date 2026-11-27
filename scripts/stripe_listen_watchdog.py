"""Thin wrapper: run stripe_listen_watchdog from .pyc when source is absent."""
from __future__ import annotations

import marshal
import runpy
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import _pyc_bootstrap  # noqa: F401

_pyc = _HERE / "__pycache__" / "stripe_listen_watchdog.cpython-312.pyc"
if not _pyc.is_file():
    raise SystemExit(f"missing watchdog bytecode: {_pyc}")

# Prefer executing the compiled module body as __main__ so argparse sees argv.
code = marshal.loads(_pyc.read_bytes()[16:])
# Ensure cwd is repo root for relative paths inside watchdog.
import os

os.chdir(_ROOT)
sys.argv[0] = str(_HERE / "stripe_listen_watchdog.py")
exec(code, {"__name__": "__main__", "__file__": str(_HERE / "stripe_listen_watchdog.py")})
