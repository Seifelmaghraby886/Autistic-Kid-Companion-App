"""Parent Dashboard — overview, command center, alerts, settings, test center."""

import json
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QFrame, QGridLayout, QFileDialog,
    QScrollArea, QLineEdit, QComboBox, QCheckBox
)
from PySide6.QtCore import Qt, Signal

from ui.components import C, GlassCard, MAIN_STYLE
from data import database as db


class ParentDashboard(QWidget):
    close_requested = Signal()

    def __init__(self, controller, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setStyleSheet(MAIN_STYLE)
        self._build()

    def _build(self):
        L = QVBoxLayout(self); L.setContentsMargins(28, 22, 28, 22); L.setSpacing(14)
        top = QHBoxLayout()
        back = QPushButton("← Exit Parent Mode")
        back.setMaximumWidth(200)
        back.setStyleSheet(f"""
            QPushButton {{ background: rgba(0,191,168,0.15); color: {C['cyan']};
                border: 1.5px solid {C['teal']}; border-radius: 10px;
                padding: 9px 14px; font-size: 12px; }}
        """)
        back.clicked.connect(self.close_requested.emit)
        t = QLabel("👤  Parent Dashboard")
        t.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {C['cyan']};")
        top.addWidget(back); top.addSpacing(16); top.addWidget(t); top.addStretch()
        L.addLayout(top)

        tabs = QTabWidget()
        tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border: 1px solid rgba(0,191,168,0.3); border-radius: 12px;
                background: {C['bg2']}; }}
            QTabBar::tab {{ background: rgba(255,255,255,0.05); color: {C['text_dim']};
                padding: 10px 18px; margin: 4px; border-radius: 8px;
                font-size: 12px; font-weight: 600; }}
            QTabBar::tab:selected {{ background: rgba(0,229,255,0.20); color: {C['cyan']}; }}
        """)
        tabs.addTab(self._overview_tab(), "Overview")
        tabs.addTab(self._command_tab(),  "Command Center")
        tabs.addTab(self._alerts_tab(),   "Alerts")
        tabs.addTab(self._sessions_tab(), "Sessions")
        tabs.addTab(self._schedule_tab(), "Schedule")
        tabs.addTab(self._settings_tab(),"AI & Voice")
        tabs.addTab(self._test_tab(),    "Test Center")
        L.addWidget(tabs)

    # ── Overview ─────────────────────────────────────────────
    def _overview_tab(self):
        w = QWidget(); L = QVBoxLayout(w); L.setSpacing(12); L.setContentsMargins(16,16,16,16)
        cid = self.controller.child_id
        child = db.get_child(cid) or {}
        state = db.get_child_state(cid)

        row = QHBoxLayout()
        for label, val, color in [
            ("Child", child.get("name", "—"), C["cyan"]),
            ("Age", str(child.get("age", "—")), C["soft"]),
            ("Language", child.get("language", "—"), C["purple"]),
            ("Current Emotion", state.get("current_emotion", "neutral"), C["warn"]),
            ("Stress", state.get("stress_level", "low"), C["alert"]),
        ]:
            card = GlassCard(w, dark=True)
            cl = QVBoxLayout(card); cl.setContentsMargins(16, 14, 16, 14)
            k = QLabel(label.upper())
            k.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {color}; letter-spacing: 2px;")
            v = QLabel(str(val))
            v.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {C['text']};")
            cl.addWidget(k); cl.addWidget(v)
            row.addWidget(card)
        L.addLayout(row)

        # Provider status
        status_card = GlassCard(w, dark=True)
        sl = QVBoxLayout(status_card); sl.setContentsMargins(20, 14, 20, 14)
        sl.addWidget(self._heading("PROVIDER STATUS"))
        ps = self.controller.provider_status()
        ai_lbl = QLabel(f"AI:    {ps['ai'].get('name','?')}    "
                       f"{'✓ available' if ps['ai'].get('available') else '✗ '+ps['ai'].get('reason','unavailable')}")
        ai_lbl.setStyleSheet(f"font-size: 13px; color: {C['text']};")
        sl.addWidget(ai_lbl)
        for v in ps.get("voice", []):
            vl = QLabel(f"Voice: {v.get('name','?'):14s}    "
                       f"{'✓' if v.get('available') else '✗'}")
            vl.setStyleSheet(f"font-size: 12px; color: {C['text_dim']}; font-family: Consolas, monospace;")
            sl.addWidget(vl)
        sum_lbl = QLabel(f"Summary: {ps.get('summary')}")
        sum_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {C['cyan']}; padding-top: 6px;")
        sl.addWidget(sum_lbl)
        L.addWidget(status_card)
        L.addStretch()
        return w

    # ── Command Center ───────────────────────────────────────
    def _command_tab(self):
        w = QWidget(); L = QVBoxLayout(w); L.setSpacing(10); L.setContentsMargins(16,16,16,16)
        L.addWidget(self._heading("PARENT COMMAND CENTER"))
        grid = QGridLayout(); grid.setSpacing(10)
        cmds = [
            ("🌿 Open Calm Zone",      lambda: self.controller.tools.open_calm_zone.emit()),
            ("🗨 Open AAC",             lambda: self.controller.tools.open_aac.emit("all")),
            ("📅 Open Schedule",       lambda: self.controller.tools.open_schedule.emit()),
            ("🪥 Brushing Tutorial",   lambda: self.controller.tools.open_tutorial.emit("brush_teeth")),
            ("🧼 Washing Tutorial",    lambda: self.controller.tools.open_tutorial.emit("wash_hands")),
            ("📖 Generate Story",       lambda: self.controller.tools.open_story.emit("calm_night")),
            ("🎮 Open Games",           lambda: self.controller.tools.open_game.emit()),
            ("🤖 Robot Comfort Mode",  lambda: self.controller.robot.send({
                "face":"sad_soft","voice":"comfort","led":"calm_blue",
                "movement":"stay_still","mode":"comfort"})),
        ]
        for i, (name, fn) in enumerate(cmds):
            b = QPushButton(name)
            b.setMinimumHeight(54)
            b.clicked.connect(fn)
            grid.addWidget(b, i // 2, i % 2)
        L.addLayout(grid)

        # Auto-listening toggle
        tog = QCheckBox("Auto-listening enabled (child does not press to talk)")
        tog.setChecked(True)
        tog.toggled.connect(self.controller.set_auto_listening)
        L.addWidget(tog)

        export = QPushButton("📤 Export Session Report")
        export.clicked.connect(self._export_report)
        L.addWidget(export)
        L.addStretch()
        return w

    def _export_report(self):
        cid = self.controller.child_id
        data = {
            "child": db.get_child(cid),
            "state": db.get_child_state(cid),
            "sessions": db.list_sessions(cid, 20),
            "alerts": db.list_alerts(cid, 30),
            "recent_emotions": db.recent_emotions(cid, 60),
            "exported_at": datetime.now().isoformat(),
        }
        path, _ = QFileDialog.getSaveFileName(self, "Save report",
                                              "aria_report.json", "JSON (*.json)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    # ── Alerts ───────────────────────────────────────────────
    def _alerts_tab(self):
        w = QWidget(); L = QVBoxLayout(w); L.setContentsMargins(16,16,16,16)
        L.addWidget(self._heading("RECENT ALERTS"))
        sc = QScrollArea(); sc.setWidgetResizable(True); sc.setFrameShape(QFrame.NoFrame)
        sc.setStyleSheet("background: transparent;")
        inner = QWidget(); il = QVBoxLayout(inner); il.setSpacing(8)
        for a in db.list_alerts(self.controller.child_id, 30):
            card = GlassCard(inner, dark=True)
            cl = QHBoxLayout(card); cl.setContentsMargins(16, 10, 16, 10)
            sev = a.get("severity", "low")
            color = {"high": C["alert"], "medium": C["warn"], "low": C["soft"]}.get(sev, C["text_dim"])
            type_lbl = QLabel(a.get("type","")); type_lbl.setStyleSheet(f"color: {color}; font-weight: 700;")
            type_lbl.setMinimumWidth(160)
            msg_lbl = QLabel(a.get("message","")); msg_lbl.setStyleSheet(f"color: {C['text']};")
            msg_lbl.setWordWrap(True)
            ts_lbl = QLabel(a.get("timestamp","")[:19]); ts_lbl.setStyleSheet(f"color: {C['text_dim']};")
            cl.addWidget(type_lbl); cl.addWidget(msg_lbl, 1); cl.addWidget(ts_lbl)
            il.addWidget(card)
        il.addStretch()
        sc.setWidget(inner)
        L.addWidget(sc)
        return w

    # ── Sessions ─────────────────────────────────────────────
    def _sessions_tab(self):
        w = QWidget(); L = QVBoxLayout(w); L.setContentsMargins(16,16,16,16)
        L.addWidget(self._heading("RECENT SESSIONS"))
        for s in db.list_sessions(self.controller.child_id, 20):
            card = GlassCard(w, dark=True)
            cl = QVBoxLayout(card); cl.setContentsMargins(16, 12, 16, 12)
            head = QLabel(f"#{s['id']}  ·  {s.get('start_time','')[:19]}  ·  risk: {s.get('risk_level','normal')}")
            head.setStyleSheet(f"color: {C['cyan']}; font-weight: 700;")
            cl.addWidget(head)
            if s.get("summary"):
                summ = QLabel(s["summary"]); summ.setStyleSheet(f"color: {C['text_dim']};")
                cl.addWidget(summ)
            L.addWidget(card)
        L.addStretch()
        return w

    # ── Schedule editor ──────────────────────────────────────
    def _schedule_tab(self):
        w = QWidget(); L = QVBoxLayout(w); L.setContentsMargins(16,16,16,16)
        L.addWidget(self._heading("DAILY SCHEDULE"))
        for item in db.list_schedule(self.controller.child_id):
            row = QHBoxLayout()
            row.addWidget(QLabel(item.get("icon","📅")))
            t = QLabel(item.get("title",""))
            t.setStyleSheet(f"color: {C['text']}; font-weight: 600;")
            t.setMinimumWidth(180)
            time = QLabel(item.get("time","")); time.setStyleSheet(f"color: {C['text_dim']};")
            status = QLabel(item.get("status","pending"))
            status.setStyleSheet(f"color: {C['success'] if item.get('status') == 'done' else C['warn']};")
            row.addWidget(t); row.addWidget(time); row.addStretch(); row.addWidget(status)
            box = QFrame(); box.setLayout(row)
            L.addWidget(box)

        addrow = QHBoxLayout()
        self._new_title = QLineEdit(); self._new_title.setPlaceholderText("New task title…")
        self._new_time = QLineEdit(); self._new_time.setPlaceholderText("HH:MM")
        self._new_time.setMaximumWidth(100)
        addb = QPushButton("+ Add")
        addb.setMaximumWidth(100)
        addb.clicked.connect(self._add_schedule)
        addrow.addWidget(self._new_title); addrow.addWidget(self._new_time); addrow.addWidget(addb)
        L.addLayout(addrow)
        L.addStretch()
        return w

    def _add_schedule(self):
        title = self._new_title.text().strip()
        time = self._new_time.text().strip()
        if not title: return
        db.add_schedule(self.controller.child_id, title, "📅", time)
        self._new_title.clear(); self._new_time.clear()

    # ── AI & Voice settings ──────────────────────────────────
    def _settings_tab(self):
        w = QWidget(); L = QVBoxLayout(w); L.setSpacing(12); L.setContentsMargins(16,16,16,16)
        L.addWidget(self._heading("AI & VOICE PROVIDERS"))

        info = QLabel(
            "ARIA OS works fully offline with MockAI + offline TTS.\n"
            "Add a Claude or ElevenLabs API key in .env to unlock premium quality."
        )
        info.setStyleSheet(f"color: {C['text_dim']}; font-size: 12px; padding-bottom: 8px;")
        info.setWordWrap(True)
        L.addWidget(info)

        ps = self.controller.provider_status()
        for v in ps.get("voice", []):
            row = QHBoxLayout()
            name_lbl = QLabel(v.get("name", "?"))
            name_lbl.setStyleSheet(f"color: {C['text']}; font-weight: 600;")
            stat_lbl = QLabel("✓ available" if v.get("available") else "✗ unavailable")
            stat_lbl.setStyleSheet(f"color: {C['success'] if v.get('available') else C['alert']};")
            use_btn = QPushButton("Use this voice")
            use_btn.setMaximumWidth(160)
            use_btn.clicked.connect(lambda checked, n=v.get("name"): self.controller.tts.set_provider(n))
            row.addWidget(name_lbl, 1); row.addWidget(stat_lbl); row.addWidget(use_btn)
            box = QFrame(); box.setLayout(row)
            L.addWidget(box)

        refresh = QPushButton("🔄 Reload providers (re-read .env)")
        refresh.clicked.connect(self.controller.refresh_providers)
        L.addWidget(refresh)

        test_ai = QPushButton("🧠 Test AI provider")
        test_ai.clicked.connect(self._test_ai)
        L.addWidget(test_ai)
        test_voice = QPushButton("🔊 Test voice provider")
        test_voice.clicked.connect(self._test_voice)
        L.addWidget(test_voice)

        self._status_out = QTextEdit(); self._status_out.setReadOnly(True)
        self._status_out.setMaximumHeight(180)
        L.addWidget(self._status_out)
        L.addStretch()
        return w

    def _test_ai(self):
        prof = db.get_child(self.controller.child_id)
        r = self.controller.ai.generate_response("Hello ARIA", prof, {}, [])
        self._status_out.setPlainText(json.dumps(r, ensure_ascii=False, indent=2))

    def _test_voice(self):
        self.controller.tts.speak("Hello, I am ARIA. This is a voice test.",
                                  language="en", voice_style="soft")
        self._status_out.setPlainText("Voice test: spoken (check your speakers).")

    # ── Test Center ──────────────────────────────────────────
    def _test_tab(self):
        w = QWidget(); L = QVBoxLayout(w); L.setSpacing(12); L.setContentsMargins(16,16,16,16)
        L.addWidget(self._heading("TEST CENTER"))
        runb = QPushButton("▶ Run All Tests")
        runb.clicked.connect(self._run_tests)
        L.addWidget(runb)
        self._test_out = QTextEdit(); self._test_out.setReadOnly(True)
        L.addWidget(self._test_out, 1)

        # Show last run results
        last = db.last_test_results(20)
        if last:
            summ = QLabel(f"Last run: {last[0]['timestamp'][:19]}  ·  {len(last)} results")
            summ.setStyleSheet(f"color: {C['text_dim']}; font-size: 11px;")
            L.addWidget(summ)
        return w

    def _run_tests(self):
        import subprocess, sys
        from pathlib import Path
        self._test_out.setPlainText("Running tests…\n")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                cwd=str(Path(__file__).parent.parent),
                capture_output=True, text=True, timeout=120,
            )
            out = (proc.stdout or "") + "\n" + (proc.stderr or "")
            self._test_out.setPlainText(out[-6000:])
            # Save to DB
            passed = "OK" in out and "FAILED" not in out
            db.log_test("all_tests", "pass" if passed else "fail", out[-2000:])
        except Exception as e:
            self._test_out.setPlainText(f"Error running tests: {e}")
            db.log_test("all_tests", "error", str(e))

    def _heading(self, text):
        h = QLabel(text)
        h.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {C['cyan']}; letter-spacing: 3px;")
        return h
