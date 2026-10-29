"""
ARIA Embedded YouTube Player
Uses QtWebEngine to embed YouTube videos in-app for tutorials.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

from ui.styles import COLORS


YOUTUBE_EMBED_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin: 0; padding: 0; background: #0A1428; overflow: hidden; }}
  .video-wrap {{
    position: relative;
    width: 100%;
    height: 100vh;
    background: #0A1428;
  }}
  iframe {{
    position: absolute;
    top: 0; left: 0;
    width: 100%;
    height: 100%;
    border: none;
  }}
</style>
</head>
<body>
<div class="video-wrap">
  <iframe
    src="https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0&modestbranding=1&fs=1"
    allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
    allowfullscreen>
  </iframe>
</div>
</body>
</html>
"""


class YouTubePlayerDialog(QDialog):
    def __init__(self, video_id, title="Video", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"📺  {title}")
        self.setMinimumSize(960, 600)
        self.resize(1100, 700)
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLORS['navy']};
            }}
            QLabel {{
                color: white;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(8)

        # Header
        hdr = QHBoxLayout()
        title_lbl = QLabel(f"📺  {title}")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: white;")
        close_btn = QPushButton("✕  Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255,107,126,0.20);
                color: #FF6B7E;
                border: 1px solid rgba(255,107,126,0.4);
                border-radius: 10px;
                padding: 8px 16px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(255,107,126,0.35); }}
        """)
        close_btn.clicked.connect(self.accept)
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        hdr.addWidget(close_btn)
        layout.addLayout(hdr)

        # Web view
        self._view = QWebEngineView()
        try:
            s = self._view.settings()
            s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
            s.setAttribute(QWebEngineSettings.PlaybackRequiresUserGesture, False)
            s.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        except Exception:
            pass

        html = YOUTUBE_EMBED_HTML.format(video_id=video_id)
        self._view.setHtml(html, QUrl("https://www.youtube.com"))
        layout.addWidget(self._view, 1)

    def closeEvent(self, event):
        try:
            self._view.setHtml("")  # Stop playback
        except Exception:
            pass
        super().closeEvent(event)
