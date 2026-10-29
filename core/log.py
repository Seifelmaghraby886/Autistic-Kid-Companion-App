"""
ARIA OS — shared diagnostic log.

Every important step of the voice pipeline calls `log()`. It prints to the
console AND appends to `aria_os.log` in the project folder, so when something
misbehaves the parent/developer can simply share that one file.
"""

from datetime import datetime
from pathlib import Path

_LOG_FILE = Path(__file__).parent.parent / "aria_os.log"
_session_marked = False


def log(msg):
    """Print a diagnostic line and append it to aria_os.log."""
    global _session_marked
    print(f"[ARIA-OS] {msg}", flush=True)
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            if not _session_marked:
                _session_marked = True
                f.write(f"\n===== ARIA OS session "
                        f"{datetime.now():%Y-%m-%d %H:%M:%S} =====\n")
            f.write(f"[{datetime.now():%H:%M:%S}] {msg}\n")
    except Exception:
        pass
