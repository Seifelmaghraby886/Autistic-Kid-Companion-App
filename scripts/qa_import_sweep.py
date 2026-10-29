"""QA sweep: import every app module offscreen and report failures.

Run: py -3.11 scripts/qa_import_sweep.py
Exit code 0 = all modules import clean; 1 = failures listed on stdout.
"""
from __future__ import annotations

import importlib
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

PACKAGES = ["ai", "core", "database", "speech", "ui", "vision"]


def iter_modules():
    for pkg in PACKAGES:
        pkg_dir = ROOT / pkg
        for py in sorted(pkg_dir.glob("*.py")):
            if py.name == "__init__.py":
                yield pkg
            else:
                yield f"{pkg}.{py.stem}"


def main() -> int:
    # A QApplication must exist before some ui modules build widgets at
    # import time; create one up front.
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])

    failures: list[tuple[str, str]] = []
    passed = 0
    for mod_name in iter_modules():
        try:
            importlib.import_module(mod_name)
            passed += 1
        except Exception:
            failures.append((mod_name, traceback.format_exc(limit=3)))

    print(f"PASS {passed}  FAIL {len(failures)}")
    for name, tb in failures:
        print(f"\n=== {name} ===")
        print(tb)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
