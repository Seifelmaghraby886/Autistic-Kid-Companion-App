"""ARIA OS — entry point. Opens directly into the auto-listening shell."""

import sys
import os
import traceback
from pathlib import Path

# Make sure relative imports work
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from core.app_controller import AppController
from ui.shell_window import ShellWindow


def _excepthook(exc_type, exc, tb):
    err = "".join(traceback.format_exception(exc_type, exc, tb))
    print(f"\n{'='*60}\nUnhandled error (logged, not raised):\n{err}\n{'='*60}\n")
    try:
        with open(Path(__file__).parent / "crash.log", "a", encoding="utf-8") as f:
            f.write(err + "\n---\n")
    except Exception:
        pass


sys.excepthook = _excepthook


def main():
    # Pre-init pygame mixer on main thread so TTS playback works reliably
    try:
        import pygame
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
    except Exception as e:
        print(f"[pygame mixer pre-init skipped: {e}]")

    app = QApplication(sys.argv)
    app.setApplicationName("ARIA OS")
    app.setOrganizationName("ARIA")

    controller = AppController()
    window = ShellWindow(controller)
    window.show()

    rc = app.exec()
    try:
        controller.shutdown()
    except Exception:
        pass
    sys.exit(rc)


if __name__ == "__main__":
    main()
