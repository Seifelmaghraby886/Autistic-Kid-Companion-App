"""
ARIA OS — Shell  (the voice-first home environment)
===================================================
This is the screen ARIA boots into. There is no menu to learn: ARIA's face
*is* the home. She greets the child by name, listens automatically, talks
back, and opens any tool by voice.

Large touch tiles are shown as a visible, reassuring backup — the app runs in
kiosk mode (no mouse/keyboard) and a child can tap a tile — but the child
never *has* to use them. The whole screen is driven by the persistent
ConversationEngine; the shell only displays its state.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont

from ui.components import GlassCard, ARIAFaceWidget, ParticleBackground
from ui.styles import MAIN_STYLE, COLORS


# ── localized status line per listening state ─────────────────────────
_STATUS = {
    "IDLE":      {"en": "Ready",                 "ar": "جاهزة",                  "de": "Bereit"},
    "GREETING":  {"en": "Hello!",                "ar": "أهلاً بيك!",             "de": "Hallo!"},
    "LISTENING": {"en": "I'm listening…  🎙️",    "ar": "أنا بسمعك…  🎙️",        "de": "Ich höre zu…  🎙️"},
    "HEARD":     {"en": "Got it…",               "ar": "فهمت…",                  "de": "Verstanden…"},
    "THINKING":  {"en": "Thinking…",             "ar": "بفكّر…",                 "de": "Ich denke nach…"},
    "SPEAKING":  {"en": "ARIA is talking…",      "ar": "أريا بتتكلم…",           "de": "ARIA spricht…"},
    "OPENING":   {"en": "Opening that for you…", "ar": "بفتحهالك…",              "de": "Wird geöffnet…"},
    "PAUSED":    {"en": "Paused",                "ar": "متوقفة",                 "de": "Pausiert"},
    "COMFORT":   {"en": "Let's take a calm moment  💙", "ar": "خلينا ناخد لحظة هدوء  💙", "de": "Eine ruhige Pause  💙"},
    "ERROR":     {"en": "One moment…",           "ar": "لحظة واحدة…",            "de": "Einen Moment…"},
}

_HINT = {
    "en": "Just talk to me — say things like “ARIA, open games” or “I feel sad”.",
    "ar": "كلّمني وبس — زي «أريا افتحي الألعاب» أو «أنا حزين».",
    "de": "Sprich einfach mit mir — z. B. „ARIA, öffne Spiele“ oder „Ich bin traurig“.",
}
_HEARD_PREFIX = {"en": "you said:  ", "ar": "إنت قلت:  ", "de": "du sagtest:  "}

# small badge in the top bar: does the camera see the child?
_PRESENCE = {
    "seen":    {"en": "👀  I see you",        "ar": "👀  شايفاك",          "de": "👀  Ich sehe dich"},
    "looking": {"en": "👁  Looking for you…",  "ar": "👁  بدور عليك…",      "de": "👁  Ich suche dich…"},
}

# tap-to-talk button label per listening state (a reliable manual backup)
_TAP_LABEL = {
    "idle":      {"en": "Tap to talk to ARIA", "ar": "دوس عشان تكلّم أريا",  "de": "Zum Reden tippen"},
    "listening": {"en": "Listening… speak now", "ar": "بسمعك… اتكلّم دلوقتي", "de": "Ich höre… sprich"},
    "thinking":  {"en": "ARIA is thinking…",    "ar": "أريا بتفكّر…",        "de": "ARIA denkt…"},
    "speaking":  {"en": "Tap to talk",          "ar": "دوس عشان تتكلم",      "de": "Zum Reden tippen"},
}

# camera-distress comfort offer (a soft card shown over the shell — never forced)
_COMFORT_TEXT = {
    "en": "I'm here with you 💙\nWould you like a calm moment together?",
    "ar": "أنا معاك 💙\nتحب ناخد لحظة هدوء سوا؟",
    "de": "Ich bin bei dir 💙\nMöchtest du einen ruhigen Moment?",
}
_COMFORT_BTN_CALM = {"en": "🌿  Calm Zone", "ar": "🌿  ركن الهدوء", "de": "🌿  Ruhe-Zone"}
_COMFORT_BTN_OK   = {"en": "😊  I'm okay",  "ar": "😊  أنا كويس",   "de": "😊  Mir geht's gut"}

# tile key -> (emoji, {lang: label}, accent colour) — verbal-child home
_TILES = [
    ("talk",      "💬", {"en": "Talk",     "ar": "اتكلم",   "de": "Reden"},   COLORS["teal"]),
    ("calm",      "🌿", {"en": "Calm Zone","ar": "الهدوء",  "de": "Ruhe"},    COLORS["neon_cyan"]),
    ("schedule",  "📅", {"en": "My Day",   "ar": "يومي",    "de": "Mein Tag"},COLORS["lavender_mid"]),
    ("games",     "🎮", {"en": "Games",    "ar": "ألعاب",   "de": "Spiele"},  COLORS["warning"]),
    ("camera",    "😊", {"en": "Feelings", "ar": "مشاعري",  "de": "Gefühle"}, COLORS["success"]),
    ("dashboard", "⊞",  {"en": "More",     "ar": "المزيد",  "de": "Mehr"},    COLORS["neon_purple"]),
]
# Non-verbal home: the picture / communication board is FIRST because for a
# non-verbal child it *is* their voice and must never be buried in menus.
_TILES_NON_VERBAL = [
    ("comms",     "🗣️", {"en": "Picture Talk", "ar": "صور للكلام", "de": "Bilder-Sprache"}, COLORS["teal"]),
    ("calm",      "🌿", {"en": "Calm Zone",    "ar": "الهدوء",     "de": "Ruhe"},           COLORS["neon_cyan"]),
    ("games",     "🎮", {"en": "Games",        "ar": "ألعاب",      "de": "Spiele"},         COLORS["warning"]),
    ("schedule",  "📅", {"en": "My Day",       "ar": "يومي",       "de": "Mein Tag"},       COLORS["lavender_mid"]),
    ("camera",    "😊", {"en": "Feelings",     "ar": "مشاعري",     "de": "Gefühle"},        COLORS["success"]),
    ("dashboard", "⊞",  {"en": "More",         "ar": "المزيد",     "de": "Mehr"},           COLORS["neon_purple"]),
]


class ShellTile(QFrame):
    """A large, touch-friendly module tile. Tapping it navigates by key."""

    clicked = Signal(str)

    def __init__(self, key, icon, label, color, parent=None):
        super().__init__(parent)
        self._key = key
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(150, 134)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.86);
                border: 2px solid {color};
                border-radius: 22px;
            }}
            QFrame:hover {{ background: rgba(255,255,255,0.99); }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 16, 10, 14)
        lay.setSpacing(8)
        lay.setAlignment(Qt.AlignCenter)

        ic = QLabel(icon)
        ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet("font-size: 44px; background: transparent; border: none;")

        tx = QLabel(label)
        tx.setAlignment(Qt.AlignCenter)
        tx.setStyleSheet(
            f"font-size: 15px; font-weight: 700; color: {COLORS['text']};"
            f"background: transparent; border: none;"
        )
        lay.addWidget(ic)
        lay.addWidget(tx)

    def mousePressEvent(self, event):
        self.clicked.emit(self._key)
        super().mousePressEvent(event)


class ARIAShell(QWidget):
    """Voice-first home. Displays the ConversationEngine; opens tools by key."""

    navigate = Signal(str)

    def __init__(self, child_id, engine, parent=None):
        super().__init__(parent)
        self.child_id = child_id
        self.engine = engine
        import database.db_manager as db
        self._child = db.get_child(child_id) or {}
        self._lang = self._child.get("language", "en")
        self.setStyleSheet(MAIN_STYLE)
        self._build_ui()
        self._connect_engine()

        # The shell owns the "start" trigger. This timer is a child widget,
        # so if the child taps away before it fires, ARIAMainWindow's cleanup
        # stops it — ARIA never starts listening on top of another screen.
        self._start_timer = QTimer(self)
        self._start_timer.setSingleShot(True)
        self._start_timer.timeout.connect(self._start_engine)
        self._start_timer.start(600)

    def _start_engine(self):
        """Begin ARIA's greeting + hands-free listening once the shell settled."""
        if self.engine is not None and not self.engine.is_started():
            self.engine.start()
        # Non-verbal children: ARIA scans the home tiles after the greeting
        # so the child can nod at the one they want.
        if self._child.get("communication_level") == "non_verbal":
            QTimer.singleShot(5500, self.start_scan_menu)

    # ── construction ─────────────────────────────────────────────────
    def _build_ui(self):
        self._bg = ParticleBackground(self)
        self._bg.lower()

        root = QVBoxLayout(self)
        root.setContentsMargins(46, 22, 46, 26)
        root.setSpacing(12)

        root.addLayout(self._build_top_bar())
        root.addStretch(1)

        # ARIA face — the heart of the home screen
        self._face = ARIAFaceWidget(size=212)
        root.addWidget(self._face, alignment=Qt.AlignHCenter)

        # status line under the face
        self._status = QLabel(self._tr(_STATUS, "GREETING"))
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setStyleSheet(
            f"font-size: 17px; font-weight: 800; color: {COLORS['teal_deep']};"
        )
        root.addWidget(self._status)

        # live microphone level — lets a parent SEE that ARIA hears the child
        self._mic_bar = QProgressBar()
        self._mic_bar.setRange(0, 100)
        self._mic_bar.setValue(0)
        self._mic_bar.setTextVisible(False)
        self._mic_bar.setFixedSize(260, 8)
        root.addWidget(self._mic_bar, alignment=Qt.AlignHCenter)

        # conversation card — ARIA's reply + what the child said
        card = GlassCard(self, radius=22)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(30, 20, 30, 20)
        cl.setSpacing(6)
        self._reply = QLabel("…")
        self._reply.setWordWrap(True)
        self._reply.setAlignment(Qt.AlignCenter)
        self._reply.setStyleSheet(
            f"font-size: 20px; font-weight: 600; color: {COLORS['text']};"
            f"background: transparent;"
        )
        self._reply.setMinimumHeight(66)
        self._heard = QLabel("")
        self._heard.setWordWrap(True)
        self._heard.setAlignment(Qt.AlignCenter)
        self._heard.setStyleSheet(
            f"font-size: 13px; font-style: italic; color: {COLORS['text_light']};"
            f"background: transparent;"
        )
        cl.addWidget(self._reply)
        cl.addWidget(self._heard)
        root.addWidget(card)

        # tap-to-talk — a big, reliable manual backup. ARIA also listens
        # hands-free, but a child can always tap this to talk right now.
        self._talk_btn = QPushButton("🎙   " + self._tr(_TAP_LABEL, "idle"))
        self._talk_btn.setCursor(Qt.PointingHandCursor)
        self._talk_btn.setFixedHeight(62)
        self._talk_btn.setMinimumWidth(330)
        self._talk_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['teal_deep']});
                color: white; border: none; border-radius: 31px;
                font-size: 17px; font-weight: 800; padding: 0 38px;
            }}
            QPushButton:hover  {{ background: {COLORS['teal_glow']}; color: {COLORS['text']}; }}
            QPushButton:pressed {{ background: {COLORS['teal_deep']}; }}
        """)
        self._talk_btn.clicked.connect(self._on_talk_btn)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._talk_btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        # gentle hint
        hint = QLabel(self._lang_pick(_HINT))
        hint.setAlignment(Qt.AlignCenter)
        hint.setWordWrap(True)
        hint.setStyleSheet(f"font-size: 12px; color: {COLORS['text_dim']};")
        root.addWidget(hint)

        root.addStretch(1)

        # AI suggestion card — the intelligence bus proposes the next
        # activity from the session context; tapping it navigates there.
        self._suggest_dest = None
        self._suggest_card = QPushButton()
        self._suggest_card.setCursor(Qt.PointingHandCursor)
        self._suggest_card.setVisible(False)
        self._suggest_card.setMinimumHeight(52)
        self._suggest_card.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(0,191,168,0.14), stop:1 rgba(179,136,255,0.14));
                color: {COLORS['text']};
                border: 1.6px solid rgba(0,191,168,0.45);
                border-radius: 16px;
                padding: 10px 26px; font-size: 15px; font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(0,191,168,0.26), stop:1 rgba(179,136,255,0.26));
            }}
        """)
        self._suggest_card.clicked.connect(self._open_suggestion)
        root.addWidget(self._suggest_card, alignment=Qt.AlignCenter)
        try:
            from core.child_context import get_context
            ctx = get_context()
            ctx.suggestion_ready.connect(self._on_suggestion)
            QTimer.singleShot(900, lambda: ctx.request_suggestion(self._lang))
            # Long idles on the home screen: refresh the suggestion every
            # 2 minutes so it tracks the child's latest mood and activity.
            self._suggest_timer = QTimer(self)
            self._suggest_timer.timeout.connect(
                lambda: ctx.request_suggestion(self._lang))
            self._suggest_timer.start(120_000)
        except Exception:
            pass

        # touch-backup tiles — for a non-verbal child, surface the picture
        # board first so it's never buried under menus.
        tile_set = (_TILES_NON_VERBAL
                    if self._child.get("communication_level") == "non_verbal"
                    else _TILES)
        tiles = QHBoxLayout()
        tiles.setSpacing(16)
        tiles.setAlignment(Qt.AlignCenter)
        for key, icon, labels, color in tile_set:
            tile = ShellTile(key, icon, self._lang_pick(labels), color)
            tile.clicked.connect(self.navigate.emit)
            tiles.addWidget(tile)
        root.addLayout(tiles)
        # cache for the scan menu
        self._tile_set = tile_set

        # comfort offer card — a soft overlay shown when the camera notices
        # sustained distress. Never forced: two big choices, auto-dismisses.
        self._comfort_card = self._build_comfort_card()
        self._comfort_card.hide()
        self._comfort_timer = QTimer(self)
        self._comfort_timer.setSingleShot(True)
        self._comfort_timer.timeout.connect(self._comfort_dismiss)

        # right-to-left layout for Arabic
        if self._lang == "ar":
            self.setLayoutDirection(Qt.RightToLeft)

    # ── AI suggestion card ────────────────────────────────────────────
    def _on_suggestion(self, dest: str, title: str, reason: str):
        """Fill and reveal the suggestion card (queued from a worker thread)."""
        try:
            self._suggest_dest = dest
            self._suggest_card.setText(f"{title}   ·   {reason}")
            self._suggest_card.setVisible(True)
        except RuntimeError:
            return  # shell was torn down before the suggestion arrived

        # Pre-readers can't use a text card — ARIA says it out loud, once,
        # a few seconds after the greeting so the audio never overlaps.
        # Non-verbal children skip this: their scan menu speaks instead.
        if (not getattr(self, "_suggestion_spoken", False)
                and self._child.get("communication_level") != "non_verbal"):
            self._suggestion_spoken = True

            def _speak_it(r=reason):
                try:
                    from speech.tts_engine import speak
                    speak(r, self._child_id, style="soft")
                except Exception:
                    pass
            QTimer.singleShot(6000, _speak_it)

    def _open_suggestion(self):
        if self._suggest_dest:
            self.navigate.emit(self._suggest_dest)

    def _build_top_bar(self):
        top = QHBoxLayout()
        brand = QLabel("ARIA OS")
        brand.setStyleSheet(
            f"font-size: 25px; font-weight: 900; color: {COLORS['teal']};"
            f"letter-spacing: 7px;"
        )
        top.addWidget(brand)

        name = (self._child.get("name") or "").split(" ")[0]
        if name:
            who = QLabel(f"  ·  {name}")
            who.setStyleSheet(f"font-size: 15px; color: {COLORS['text_light']};")
            top.addWidget(who)
        top.addStretch()

        # presence badge — tells the user whether ARIA can see them
        self._presence_lbl = QLabel(self._lang_pick(_PRESENCE["looking"]))
        self._presence_lbl.setStyleSheet(f"""
            QLabel {{
                background: rgba(122,140,170,0.16); color: {COLORS['text_light']};
                border: 1.2px solid rgba(122,140,170,0.35); border-radius: 14px;
                padding: 6px 14px; font-size: 12px; font-weight: 700;
            }}
        """)
        top.addWidget(self._presence_lbl)
        top.addSpacing(10)

        gear_btn = QPushButton("⚙  Setup")
        gear_btn.setCursor(Qt.PointingHandCursor)
        gear_btn.setFixedHeight(42)
        gear_btn.setToolTip("Provider Control Center")
        gear_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(122,140,170,0.14); color: {COLORS['text_light']};
                border: 1.5px solid rgba(122,140,170,0.35); border-radius: 14px;
                padding: 6px 16px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(122,140,170,0.30); }}
        """)
        gear_btn.clicked.connect(lambda: self.navigate.emit("providers"))
        top.addWidget(gear_btn)
        top.addSpacing(8)

        parent_btn = QPushButton("👤  Parent")
        parent_btn.setCursor(Qt.PointingHandCursor)
        parent_btn.setFixedHeight(42)
        parent_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(0,191,168,0.12); color: {COLORS['teal_deep']};
                border: 1.5px solid {COLORS['teal']}; border-radius: 14px;
                padding: 8px 22px; font-size: 13px; font-weight: 700;
            }}
            QPushButton:hover {{ background: rgba(0,191,168,0.24); }}
        """)
        parent_btn.clicked.connect(lambda: self.navigate.emit("parent"))
        top.addWidget(parent_btn)
        return top

    # ── engine wiring ────────────────────────────────────────────────
    def _connect_engine(self):
        if self.engine is None:
            return
        self.engine.state_changed.connect(self._on_state)
        self.engine.aria_replied.connect(self._on_reply)
        self.engine.user_said.connect(self._on_user_said)
        self.engine.emotion_updated.connect(self._on_emotion)
        self.engine.partial_volume.connect(self._on_volume)
        self.engine.listening_error.connect(self._on_listen_error)

    def _on_talk_btn(self):
        """Tap-to-talk: ask the engine to listen right now."""
        if self.engine is not None:
            self.engine.listen_now()

    def _on_volume(self, level):
        if hasattr(self, "_mic_bar"):
            self._mic_bar.setValue(int(max(0.0, min(1.0, level)) * 100))

    def _on_listen_error(self, msg):
        warn = {
            "en": "I can't hear the microphone — tap 🎙 to talk",
            "ar": "مش لاقية الميكروفون — دوس 🎙 عشان تتكلم",
            "de": "Kein Mikrofon — tippe 🎙 zum Reden",
        }
        self._status.setText(warn.get(self._lang, warn["en"]))

    def _on_state(self, state):
        self._status.setText(self._tr(_STATUS, state))
        if hasattr(self, "_mic_bar") and state != "LISTENING":
            self._mic_bar.setValue(0)
        if hasattr(self, "_talk_btn"):
            key = {"LISTENING": "listening", "THINKING": "thinking",
                   "SPEAKING": "speaking"}.get(state, "idle")
            self._talk_btn.setText("🎙   " + self._tr(_TAP_LABEL, key))
        face = self._face
        if state == "LISTENING":
            face.set_speaking(False)
            face.set_expression("listening")
        elif state == "THINKING":
            face.set_speaking(False)
            face.set_expression("thinking")
        elif state == "SPEAKING":
            face.set_speaking(True)
        elif state == "GREETING":
            face.set_expression("happy")
        elif state == "COMFORT":
            face.set_speaking(False)
            face.set_expression("comfort")
        elif state in ("PAUSED", "IDLE", "ERROR"):
            face.set_speaking(False)

    def _on_reply(self, resp):
        if not isinstance(resp, dict):
            return
        self._reply.setText(resp.get("reply", ""))
        self._face.set_expression(resp.get("face_expression", "calm"))
        self._face.set_speaking(True)

    def _on_user_said(self, text):
        if text:
            self._heard.setText(self._lang_pick(_HEARD_PREFIX) + text)

    def _on_emotion(self, emotion):
        # ambient camera emotion (Phase 3): reflect it softly when idle
        if self.engine is not None and getattr(self.engine, "_auto", None):
            if self.engine._auto.state.value in ("LISTENING", "IDLE", "PAUSED"):
                self._face.set_expression(emotion)

    def set_emotion(self, emotion):
        """Called by ARIAMainWindow when the ambient emotion changes."""
        self._on_emotion(emotion)

    # ── camera presence feedback ─────────────────────────────────────
    def set_presence(self, present: bool):
        """Camera-presence feedback so the child SEES that ARIA sees them."""
        if not hasattr(self, "_presence_lbl"):
            return
        key = "seen" if present else "looking"
        self._presence_lbl.setText(self._lang_pick(_PRESENCE[key]))
        col = COLORS["success"] if present else COLORS["text_light"]
        bg = "rgba(0,217,160,0.18)" if present else "rgba(122,140,170,0.16)"
        self._presence_lbl.setStyleSheet(f"""
            QLabel {{
                background: {bg}; color: {col};
                border: 1.2px solid {col}; border-radius: 14px;
                padding: 6px 14px; font-size: 12px; font-weight: 700;
            }}
        """)

    # ── head-gesture handling (scan mode + comfort card) ─────────────
    def on_gesture(self, gesture: str):
        """Receive a head nod / shake from FaceInputEngine via main."""
        # If the scan menu is active, feed it.
        if getattr(self, "_scan", None) is not None and self._scan.is_active():
            self._scan.on_gesture(gesture)
            return
        # If the comfort card is showing, nod = accept, shake = dismiss.
        if hasattr(self, "_comfort_card") and self._comfort_card.isVisible():
            if gesture == "nod":
                self._comfort_accept()
            elif gesture == "shake":
                self._comfort_dismiss()

    # ── scan menu (non-verbal: ARIA reads options aloud, child nods/shakes) ─
    def start_scan_menu(self):
        """ARIA reads the tiles aloud one by one — the child nods to pick."""
        if getattr(self, "_scan", None) is None:
            try:
                from core.scan_mode import ScanController
                self._scan = ScanController(self.child_id, parent=self)
                self._scan.option_spoken.connect(self._on_scan_option)
                self._scan.finished.connect(self._on_scan_finished)
            except Exception:
                return
        if self._scan.is_active():
            return
        options = [(self._lang_pick(labels), key)
                   for key, icon, labels, color in self._tile_set]
        self._scan.start(options, on_select=self._on_scan_pick)

    def _on_scan_option(self, index, label):
        """Highlight the tile ARIA is currently reading."""
        # status hints what ARIA is asking
        hint = {"en": f"… {label}?", "ar": f"… {label}؟", "de": f"… {label}?"}
        try:
            self._status.setText(hint.get(self._lang, hint["en"]))
        except Exception:
            pass

    def _on_scan_pick(self, key):
        """The child nodded — open that tool."""
        self.navigate.emit(key)

    def _on_scan_finished(self, value):
        """Scan ended (selection or 3-pass timeout)."""
        if value is None:
            # No choice after 3 passes — quietly resume listening for verbal kids
            if self.engine is not None:
                try:
                    self.engine.resume_listening()
                except Exception:
                    pass
            try:
                self._status.setText(self._tr(_STATUS, "IDLE"))
            except Exception:
                pass

    # ── comfort offer (camera-distress) ──────────────────────────────
    def _build_comfort_card(self):
        card = QFrame(self)
        card.setObjectName("comfortCard")
        card.setFixedSize(470, 250)
        card.setStyleSheet(f"""
            QFrame#comfortCard {{
                background: rgba(255,255,255,0.99);
                border: 3px solid {COLORS['neon_purple']};
                border-radius: 28px;
            }}
        """)
        v = QVBoxLayout(card)
        v.setContentsMargins(32, 26, 32, 26)
        v.setSpacing(18)

        self._comfort_msg = QLabel(self._lang_pick(_COMFORT_TEXT))
        self._comfort_msg.setWordWrap(True)
        self._comfort_msg.setAlignment(Qt.AlignCenter)
        self._comfort_msg.setStyleSheet(
            f"font-size: 19px; font-weight: 700; color: {COLORS['text']};"
            f"background: transparent; border: none;"
        )
        v.addWidget(self._comfort_msg)

        btns = QHBoxLayout()
        btns.setSpacing(14)
        calm = QPushButton(self._lang_pick(_COMFORT_BTN_CALM))
        calm.setCursor(Qt.PointingHandCursor)
        calm.setFixedHeight(58)
        calm.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {COLORS['teal']}, stop:1 {COLORS['neon_cyan']});
                color: white; border: none; border-radius: 18px;
                font-size: 15px; font-weight: 800;
            }}
            QPushButton:hover {{ background: {COLORS['teal_glow']}; }}
        """)
        calm.clicked.connect(self._comfort_accept)
        okay = QPushButton(self._lang_pick(_COMFORT_BTN_OK))
        okay.setCursor(Qt.PointingHandCursor)
        okay.setFixedHeight(58)
        okay.setStyleSheet(f"""
            QPushButton {{
                background: rgba(122,140,170,0.16); color: {COLORS['text']};
                border: 1.5px solid rgba(122,140,170,0.40); border-radius: 18px;
                font-size: 15px; font-weight: 800;
            }}
            QPushButton:hover {{ background: rgba(122,140,170,0.30); }}
        """)
        okay.clicked.connect(self._comfort_dismiss)
        btns.addWidget(calm, 1)
        btns.addWidget(okay, 1)
        v.addLayout(btns)
        return card

    def show_comfort_offer(self, emotion="sad"):
        """Gently surface a Calm Zone offer (camera noticed sustained distress)."""
        if not hasattr(self, "_comfort_card"):
            return
        self._comfort_msg.setText(self._lang_pick(_COMFORT_TEXT))
        self._face.set_expression("comfort")
        self._position_comfort_card()
        self._comfort_card.show()
        self._comfort_card.raise_()
        self._comfort_timer.start(22000)     # auto-dismiss if the child ignores it

    def _position_comfort_card(self):
        if not hasattr(self, "_comfort_card"):
            return
        cw, ch = self._comfort_card.width(), self._comfort_card.height()
        self._comfort_card.move(max(0, (self.width() - cw) // 2),
                                max(0, (self.height() - ch) // 2))

    def _comfort_accept(self):
        self._comfort_timer.stop()
        self._comfort_card.hide()
        self.navigate.emit("calm")

    def _comfort_dismiss(self):
        self._comfort_timer.stop()
        self._comfort_card.hide()

    # ── helpers ──────────────────────────────────────────────────────
    def _lang_pick(self, mapping):
        return mapping.get(self._lang, mapping.get("en", ""))

    def _tr(self, table, key):
        entry = table.get(key, table.get("IDLE", {}))
        return entry.get(self._lang, entry.get("en", key))

    def resizeEvent(self, event):
        if hasattr(self, "_bg"):
            self._bg.resize(self.size())
        if hasattr(self, "_comfort_card") and self._comfort_card.isVisible():
            self._position_comfort_card()
        super().resizeEvent(event)
