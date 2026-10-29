"""QA: boot the full app offscreen for ~8 seconds and verify a clean run.

Creates ARIAMainWindow (splash -> welcome/shell), pumps the event loop,
then quits. Fails if any exception reaches the crash handler during the
window (crash.log must not grow).

Run: py -3.11 scripts/qa_boot_test.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

crash = ROOT / "crash.log"
size_before = crash.stat().st_size if crash.exists() else 0

from PySide6.QtWidgets import QApplication  # noqa: E402
from PySide6.QtCore import QTimer  # noqa: E402

app = QApplication.instance() or QApplication([])

import main  # noqa: E402

win = main.ARIAMainWindow()

# Give the splash + first navigation time to settle, then quit.
QTimer.singleShot(8000, app.quit)
app.exec()

# Teardown any engines the boot started (camera / mic threads).
for attr in ("_face_input", "_emotion_monitor", "_conversation"):
    eng = getattr(win, attr, None)
    if eng is not None:
        try:
            eng.stop()
        except Exception:
            pass

size_after = crash.stat().st_size if crash.exists() else 0
grew = size_after - size_before

screen = type(win._current_screen).__name__ if win._current_screen else None
print(f"boot: current screen after 8s = {screen}")
print(f"boot: crash.log grew by {grew} bytes")
if grew:
    print(crash.read_text(encoding="utf-8", errors="replace")[-1500:])
raise SystemExit(1 if grew else 0)
