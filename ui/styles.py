"""
ARIA Global Stylesheet — FUTURISTIC HOLOGRAPHIC THEME
Deep navy + cyan/purple neon, autism-calm but stunning.
"""

COLORS = {
    # Backgrounds (light mode but with depth)
    "bg":           "#EDF2FA",
    "bg_dark":      "#0A1428",
    "bg_deeper":    "#050B18",
    "bg_navy":      "#1E2438",
    "card":         "rgba(255,255,255,0.85)",
    "card_dark":    "rgba(20,30,55,0.92)",
    # Primary teal
    "teal":         "#00BFA8",
    "teal_deep":    "#1A7FA8",
    "teal_glow":    "#5CE5DC",
    # Neon accents
    "neon_cyan":    "#00E5FF",
    "neon_purple":  "#B388FF",
    "neon_pink":    "#FF6BC4",
    "neon_lime":    "#7FFFD4",
    # Soft tones
    "lavender":     "#D8C8FF",
    "lavender_mid": "#A695FF",
    "cream":        "#FFF8F0",
    "peach":        "#FFC5B4",
    # Text
    "text":         "#1A2432",
    "text_light":   "#5A6F8A",
    "text_white":   "#FFFFFF",
    "text_dim":     "#8A9CB8",
    # Status
    "success":      "#00D9A0",
    "warning":      "#FFB73D",
    "danger":       "#FF6B7E",
    # Borders
    "border":       "rgba(0,191,168,0.22)",
    "border_focus": "rgba(0,191,168,0.85)",
    "border_neon":  "rgba(0,229,255,0.35)",
    # Effects
    "shadow":       "rgba(0,191,168,0.18)",
    "overlay":      "rgba(15,25,45,0.72)",
    # Holographic
    "holo_1":       "#00E5FF",
    "holo_2":       "#B388FF",
    "holo_3":       "#5CE5DC",
}


MAIN_STYLE = f"""
QWidget {{
    font-family: 'Segoe UI', 'SF Pro Display', 'Inter', Arial, sans-serif;
    color: {COLORS['text']};
    background: transparent;
}}

QMainWindow, QDialog {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 #E0EAFA,
        stop:0.3 #F0F4FF,
        stop:0.6 #E8F4F8,
        stop:1 #F0E8FF
    );
}}

QPushButton {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #00BFA8,
        stop:0.5 #00E5FF,
        stop:1 #1A7FA8
    );
    color: white;
    border: none;
    border-radius: 14px;
    padding: 12px 28px;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.6px;
}}

QPushButton:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #5CE5DC,
        stop:0.5 #4DECFF,
        stop:1 #00BFA8
    );
}}

QPushButton:pressed {{
    background: #1A7FA8;
    padding-top: 14px;
    padding-bottom: 10px;
}}

QPushButton:disabled {{
    background: #C0C8D4;
    color: #8A9CB8;
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    background: rgba(255,255,255,0.95);
    border: 1.5px solid rgba(0,191,168,0.25);
    border-radius: 14px;
    padding: 11px 18px;
    font-size: 14px;
    color: {COLORS['text']};
    selection-background-color: {COLORS['teal']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['teal']};
    background: white;
}}

QLineEdit::placeholder {{ color: #A8B6C8; }}

QComboBox {{
    background: rgba(255,255,255,0.92);
    border: 1.5px solid rgba(0,191,168,0.25);
    border-radius: 12px;
    padding: 9px 14px;
    font-size: 13px;
    color: {COLORS['text']};
    min-width: 140px;
}}

QComboBox:focus {{ border-color: {COLORS['teal']}; }}
QComboBox::drop-down {{ border: none; width: 30px; }}
QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 7px solid {COLORS['teal']};
    margin-right: 8px;
}}

QComboBox QAbstractItemView {{
    background: white;
    border: 1px solid rgba(0,191,168,0.25);
    border-radius: 12px;
    selection-background-color: rgba(0,191,168,0.18);
    selection-color: {COLORS['text']};
    padding: 4px;
}}

QScrollBar:vertical {{
    background: rgba(0,191,168,0.05);
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 rgba(0,191,168,0.5), stop:1 rgba(0,229,255,0.5));
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #00BFA8, stop:1 #00E5FF);
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

QScrollBar:horizontal {{
    background: rgba(0,191,168,0.05);
    height: 8px; border-radius: 4px;
}}

QScrollBar::handle:horizontal {{
    background: rgba(0,191,168,0.5);
    border-radius: 4px; min-width: 30px;
}}

QSlider::groove:horizontal {{
    background: rgba(0,191,168,0.18);
    height: 6px; border-radius: 3px;
}}

QSlider::handle:horizontal {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #00E5FF, stop:1 #B388FF);
    width: 20px; height: 20px;
    border-radius: 10px;
    margin-top: -7px; margin-bottom: -7px;
}}

QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #00BFA8, stop:0.5 #00E5FF, stop:1 #B388FF);
    border-radius: 3px;
}}

QProgressBar {{
    background: rgba(0,191,168,0.10);
    border: none; border-radius: 8px;
    height: 12px;
    text-align: center;
    font-size: 10px; font-weight: 700;
    color: {COLORS['teal_deep']};
}}

QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #00BFA8, stop:0.5 #00E5FF, stop:1 #B388FF);
    border-radius: 8px;
}}

QTabWidget::pane {{
    border: 1px solid rgba(0,191,168,0.22);
    border-radius: 18px;
    background: rgba(255,255,255,0.75);
    padding: 4px;
}}

QTabBar::tab {{
    background: rgba(0,191,168,0.06);
    border: none;
    border-radius: 12px;
    padding: 10px 22px;
    margin: 4px;
    font-size: 13px;
    color: {COLORS['text_light']};
    font-weight: 600;
}}

QTabBar::tab:selected {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #00BFA8, stop:0.6 #00E5FF, stop:1 #B388FF);
    color: white;
    font-weight: 700;
}}

QTabBar::tab:hover:!selected {{
    background: rgba(0,191,168,0.18);
    color: {COLORS['teal_deep']};
}}

QCheckBox {{
    font-size: 13px; spacing: 8px;
    color: {COLORS['text']};
}}

QCheckBox::indicator {{
    width: 22px; height: 22px;
    border: 2px solid rgba(0,191,168,0.35);
    border-radius: 7px;
    background: white;
}}

QCheckBox::indicator:checked {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
        stop:0 #00BFA8, stop:1 #00E5FF);
    border-color: {COLORS['teal']};
}}

QSpinBox {{
    background: rgba(255,255,255,0.92);
    border: 1.5px solid rgba(0,191,168,0.25);
    border-radius: 12px;
    padding: 8px 12px;
    font-size: 14px;
}}

QSpinBox:focus {{ border-color: {COLORS['teal']}; }}

QListWidget {{
    background: rgba(255,255,255,0.78);
    border: 1px solid rgba(0,191,168,0.22);
    border-radius: 16px;
    padding: 6px;
}}

QListWidget::item {{
    border-radius: 10px;
    padding: 11px 14px;
    margin: 2px;
}}

QListWidget::item:selected {{
    background: rgba(0,191,168,0.20);
    color: {COLORS['teal_deep']};
}}

QListWidget::item:hover {{ background: rgba(0,191,168,0.10); }}

QGroupBox {{
    border: 1px solid rgba(0,191,168,0.22);
    border-radius: 18px;
    margin-top: 16px; padding: 16px;
    font-size: 13px; font-weight: 700;
    color: {COLORS['teal_deep']};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px; padding: 0 6px;
    background: {COLORS['bg']};
}}

QToolTip {{
    background: {COLORS['bg_dark']};
    color: white;
    border: 1px solid {COLORS['neon_cyan']};
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 12px;
}}

QMenu {{
    background: rgba(20,30,55,0.95);
    color: white;
    border: 1px solid rgba(0,229,255,0.3);
    border-radius: 10px;
    padding: 6px;
}}

QMenu::item:selected {{
    background: rgba(0,229,255,0.2);
    border-radius: 6px;
}}

QHeaderView::section {{
    background: rgba(0,191,168,0.10);
    color: {COLORS['text']};
    font-weight: 700;
    border: none;
    padding: 10px;
    border-bottom: 1px solid rgba(0,191,168,0.2);
}}

QTableWidget {{
    background: rgba(255,255,255,0.8);
    border: 1px solid rgba(0,191,168,0.22);
    border-radius: 14px;
    gridline-color: rgba(0,191,168,0.10);
    font-size: 13px;
}}
"""


def get_emotion_color(emotion: str) -> str:
    return {
        "happy":     "#00D9A0",
        "joy":       "#00D9A0",
        "calm":      "#00BFA8",
        "neutral":   "#00BFA8",
        "sad":       "#6B9FE8",
        "sadness":   "#6B9FE8",
        "scared":    "#A695FF",
        "fear":      "#A695FF",
        "upset":     "#FF8B5C",
        "anger":     "#FF8B5C",
        "surprised": "#FFD840",
        "surprise":  "#FFD840",
        "thinking":  "#5CE5DC",
        "listening": "#00E5FF",
        "sleepy":    "#A8B8D0",
    }.get(emotion.lower(), "#00BFA8")


# ── accessibility ─────────────────────────────────────────────────────
_REDUCE_MOTION = None


def reduce_motion() -> bool:
    """True when the sensory-friendly 'reduce motion' setting is on.

    Some autistic children are hypersensitive to movement; when enabled the
    animated backgrounds render one static frame instead of animating.
    Cached for the process lifetime (config edits need a restart anyway).
    """
    global _REDUCE_MOTION
    if _REDUCE_MOTION is None:
        try:
            import json
            from pathlib import Path
            cfg_path = (Path(__file__).resolve().parent.parent
                        / "config" / "app_config.json")
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            _REDUCE_MOTION = bool(cfg.get("reduce_motion", False))
        except Exception:
            _REDUCE_MOTION = False
    return _REDUCE_MOTION
