"""python -m bankroll entry (loads .pyc modules when .py sources are absent)."""
from __future__ import annotations

import sys
from pathlib import Path

_scripts = Path(__file__).resolve().parents[1] / "scripts"
if str(_scripts) not in sys.path:
    sys.path.insert(0, str(_scripts))
import _pyc_bootstrap  # noqa: F401,E402

from bankroll.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
