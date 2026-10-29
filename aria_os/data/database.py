"""ARIA OS — SQLite database layer. Auto-creates schema on first run."""

import sqlite3
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "aria.db"


def _conn():
    c = sqlite3.connect(str(DB_PATH))
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def init_db():
    """Create all tables if they don't exist."""
    c = _conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            language TEXT DEFAULT 'en',
            communication_level TEXT DEFAULT 'short_sentences',
            sensory_profile_json TEXT DEFAULT '{}',
            interests_json TEXT DEFAULT '[]',
            triggers_json TEXT DEFAULT '[]',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS parents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            pin_hash TEXT,
            email TEXT,
            phone TEXT
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            mode TEXT DEFAULT 'shell',
            summary TEXT,
            risk_level TEXT DEFAULT 'normal'
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            speaker TEXT,
            text TEXT,
            emotion_estimate TEXT,
            intent TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS child_state (
            child_id INTEGER PRIMARY KEY,
            current_emotion TEXT DEFAULT 'neutral',
            current_need TEXT,
            stress_level TEXT DEFAULT 'low',
            energy_level TEXT DEFAULT 'normal',
            last_topic TEXT,
            risk_level TEXT DEFAULT 'normal',
            last_updated TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            memory_type TEXT,
            content TEXT,
            importance INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            last_used TEXT
        );
        CREATE TABLE IF NOT EXISTS emotion_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            emotion TEXT,
            confidence REAL,
            source TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS schedule_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            title TEXT,
            icon TEXT,
            time TEXT,
            status TEXT DEFAULT 'pending',
            repeat_rule TEXT
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            type TEXT,
            severity TEXT,
            message TEXT,
            resolved INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            goal_name TEXT,
            target_behavior TEXT,
            progress INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        CREATE TABLE IF NOT EXISTS robot_commands (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id INTEGER,
            command_json TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'simulated'
        );
        CREATE TABLE IF NOT EXISTS test_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            test_name TEXT,
            status TEXT,
            details TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    c.commit()
    c.close()


# ─── Children ────────────────────────────────────────────────────────
def create_child(name, age=8, language="en", communication_level="short_sentences",
                 sensory=None, interests=None, triggers=None):
    c = _conn()
    cur = c.execute("""INSERT INTO children
        (name,age,language,communication_level,sensory_profile_json,interests_json,triggers_json)
        VALUES (?,?,?,?,?,?,?)""",
        (name, age, language, communication_level,
         json.dumps(sensory or {}), json.dumps(interests or []),
         json.dumps(triggers or [])))
    cid = cur.lastrowid
    c.execute("INSERT OR IGNORE INTO child_state (child_id) VALUES (?)", (cid,))
    c.commit(); c.close()
    return cid


def get_child(cid):
    c = _conn()
    r = c.execute("SELECT * FROM children WHERE id=?", (cid,)).fetchone()
    c.close()
    if not r: return None
    d = dict(r)
    for k in ("sensory_profile_json", "interests_json", "triggers_json"):
        try: d[k] = json.loads(d[k])
        except Exception: pass
    return d


def list_children():
    c = _conn()
    rows = c.execute("SELECT * FROM children ORDER BY id").fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_or_create_default_child():
    rows = list_children()
    if rows: return rows[0]["id"]
    return create_child("Mazy", age=8, language="ar",
                        interests=["cars", "animals"], triggers=["loud sounds"])


# ─── Parents ────────────────────────────────────────────────────────
def create_parent(name, pin="1234", email="", phone=""):
    c = _conn()
    cur = c.execute("INSERT INTO parents (name,pin_hash,email,phone) VALUES (?,?,?,?)",
                    (name, hash_pin(pin), email, phone))
    pid = cur.lastrowid
    c.commit(); c.close()
    return pid


def get_or_create_default_parent():
    c = _conn()
    r = c.execute("SELECT id FROM parents LIMIT 1").fetchone()
    c.close()
    if r: return r["id"]
    return create_parent("Parent", pin="1234")


def verify_pin(pin: str) -> bool:
    c = _conn()
    r = c.execute("SELECT pin_hash FROM parents LIMIT 1").fetchone()
    c.close()
    return bool(r and r["pin_hash"] == hash_pin(pin))


# ─── Sessions ────────────────────────────────────────────────────────
def start_session(child_id, mode="shell"):
    c = _conn()
    cur = c.execute("INSERT INTO sessions (child_id,start_time,mode) VALUES (?,?,?)",
                    (child_id, datetime.now().isoformat(), mode))
    sid = cur.lastrowid
    c.commit(); c.close()
    return sid


def end_session(sid, summary="", risk_level="normal"):
    c = _conn()
    c.execute("UPDATE sessions SET end_time=?,summary=?,risk_level=? WHERE id=?",
              (datetime.now().isoformat(), summary, risk_level, sid))
    c.commit(); c.close()


def list_sessions(child_id, limit=30):
    c = _conn()
    rows = c.execute("SELECT * FROM sessions WHERE child_id=? ORDER BY id DESC LIMIT ?",
                     (child_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ─── Messages ────────────────────────────────────────────────────────
def log_message(session_id, speaker, text, emotion="", intent=""):
    c = _conn()
    c.execute("""INSERT INTO messages (session_id,speaker,text,emotion_estimate,intent)
                 VALUES (?,?,?,?,?)""", (session_id, speaker, text, emotion, intent))
    c.commit(); c.close()


def session_messages(sid, limit=200):
    c = _conn()
    rows = c.execute("SELECT * FROM messages WHERE session_id=? ORDER BY id LIMIT ?",
                     (sid, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ─── Child state ─────────────────────────────────────────────────────
def get_child_state(cid):
    c = _conn()
    r = c.execute("SELECT * FROM child_state WHERE child_id=?", (cid,)).fetchone()
    c.close()
    return dict(r) if r else {"child_id": cid, "current_emotion": "neutral",
                              "stress_level": "low", "risk_level": "normal"}


def update_child_state(cid, **kw):
    if not kw: return
    kw["last_updated"] = datetime.now().isoformat()
    c = _conn()
    c.execute("INSERT OR IGNORE INTO child_state (child_id) VALUES (?)", (cid,))
    sets = ",".join(f"{k}=?" for k in kw)
    c.execute(f"UPDATE child_state SET {sets} WHERE child_id=?", list(kw.values()) + [cid])
    c.commit(); c.close()


# ─── Memories ────────────────────────────────────────────────────────
def add_memory(child_id, memory_type, content, importance=1):
    c = _conn()
    c.execute("""INSERT INTO memories (child_id,memory_type,content,importance)
                 VALUES (?,?,?,?)""", (child_id, memory_type, content, importance))
    c.commit(); c.close()


def get_memories(child_id, limit=20):
    c = _conn()
    rows = c.execute("""SELECT * FROM memories WHERE child_id=?
                        ORDER BY importance DESC, id DESC LIMIT ?""",
                     (child_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ─── Emotion logs ────────────────────────────────────────────────────
def log_emotion(child_id, emotion, confidence=0.5, source="ai"):
    c = _conn()
    c.execute("""INSERT INTO emotion_logs (child_id,emotion,confidence,source)
                 VALUES (?,?,?,?)""", (child_id, emotion, confidence, source))
    c.commit(); c.close()


def recent_emotions(child_id, limit=50):
    c = _conn()
    rows = c.execute("""SELECT * FROM emotion_logs WHERE child_id=?
                        ORDER BY id DESC LIMIT ?""", (child_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ─── Schedule ────────────────────────────────────────────────────────
def list_schedule(child_id):
    c = _conn()
    rows = c.execute("""SELECT * FROM schedule_items WHERE child_id=?
                        ORDER BY id""", (child_id,)).fetchall()
    c.close()
    return [dict(r) for r in rows]


def add_schedule(child_id, title, icon="📅", time="", status="pending"):
    c = _conn()
    c.execute("""INSERT INTO schedule_items (child_id,title,icon,time,status)
                 VALUES (?,?,?,?,?)""", (child_id, title, icon, time, status))
    c.commit(); c.close()


def update_schedule_status(item_id, status):
    c = _conn()
    c.execute("UPDATE schedule_items SET status=? WHERE id=?", (status, item_id))
    c.commit(); c.close()


# ─── Alerts ──────────────────────────────────────────────────────────
def add_alert(child_id, alert_type, severity, message):
    c = _conn()
    c.execute("""INSERT INTO alerts (child_id,type,severity,message)
                 VALUES (?,?,?,?)""", (child_id, alert_type, severity, message))
    c.commit(); c.close()


def list_alerts(child_id, limit=50):
    c = _conn()
    rows = c.execute("""SELECT * FROM alerts WHERE child_id=?
                        ORDER BY id DESC LIMIT ?""", (child_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ─── Settings ────────────────────────────────────────────────────────
def get_setting(key, default=None):
    c = _conn()
    r = c.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
    c.close()
    if not r: return default
    try: return json.loads(r["value"])
    except Exception: return r["value"]


def set_setting(key, value):
    c = _conn()
    c.execute("INSERT OR REPLACE INTO app_settings (key,value) VALUES (?,?)",
              (key, json.dumps(value)))
    c.commit(); c.close()


# ─── Robot commands ──────────────────────────────────────────────────
def log_robot_command(child_id, command):
    c = _conn()
    c.execute("INSERT INTO robot_commands (child_id,command_json) VALUES (?,?)",
              (child_id, json.dumps(command)))
    c.commit(); c.close()


def recent_robot_commands(child_id, limit=20):
    c = _conn()
    rows = c.execute("""SELECT * FROM robot_commands WHERE child_id=?
                        ORDER BY id DESC LIMIT ?""", (child_id, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ─── Test results ────────────────────────────────────────────────────
def log_test(name, status, details=""):
    c = _conn()
    c.execute("""INSERT INTO test_results (test_name,status,details)
                 VALUES (?,?,?)""", (name, status, details))
    c.commit(); c.close()


def last_test_results(limit=50):
    c = _conn()
    rows = c.execute("""SELECT * FROM test_results
                        ORDER BY id DESC LIMIT ?""", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# Initialise on import
init_db()
