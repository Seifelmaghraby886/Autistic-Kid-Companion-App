"""
ARIA Database Manager
SQLite-based persistent storage for all profiles, sessions, and logs.
"""

import sqlite3
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path


DB_PATH = Path(__file__).parent / "aria.db"


def get_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()


def init_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS parents (
            parent_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT NOT NULL,
            relationship TEXT DEFAULT 'parent',
            pin_hash     TEXT NOT NULL,
            email        TEXT,
            phone        TEXT,
            preferred_report_language TEXT DEFAULT 'en',
            emergency_contact TEXT,
            created_at   TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS children (
            child_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id          INTEGER REFERENCES parents(parent_id),
            name               TEXT NOT NULL,
            age                INTEGER,
            language           TEXT DEFAULT 'en',
            communication_level TEXT DEFAULT 'short_sentences',
            sensory_mode       TEXT DEFAULT 'calm',
            created_at         TEXT DEFAULT CURRENT_TIMESTAMP,
            last_active        TEXT
        );

        CREATE TABLE IF NOT EXISTS child_preferences (
            child_id        INTEGER PRIMARY KEY REFERENCES children(child_id),
            favorite_topics TEXT DEFAULT '[]',
            known_triggers  TEXT DEFAULT '[]',
            calming_methods TEXT DEFAULT '[]',
            preferred_games TEXT DEFAULT '[]',
            blocked_topics  TEXT DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS device_settings (
            child_id            INTEGER PRIMARY KEY REFERENCES children(child_id),
            microphone_id       INTEGER DEFAULT 0,
            microphone_name     TEXT DEFAULT 'Default',
            camera_id           INTEGER DEFAULT 0,
            camera_name         TEXT DEFAULT 'Default',
            camera_resolution   TEXT DEFAULT '640x480',
            mirror_camera       INTEGER DEFAULT 1,
            emotion_smoothing_seconds INTEGER DEFAULT 5
        );

        CREATE TABLE IF NOT EXISTS voice_settings (
            child_id    INTEGER PRIMARY KEY REFERENCES children(child_id),
            tts_engine  TEXT DEFAULT 'edge-tts',
            voice_name  TEXT DEFAULT 'en-US-JennyNeural',
            voice_style TEXT DEFAULT 'soft',
            speed       INTEGER DEFAULT -20,
            pitch       INTEGER DEFAULT -5,
            volume      REAL DEFAULT 0.8
        );

        CREATE TABLE IF NOT EXISTS sessions (
            session_id           INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id             INTEGER REFERENCES children(child_id),
            start_time           TEXT,
            end_time             TEXT,
            dominant_emotion     TEXT,
            comfort_mode_count   INTEGER DEFAULT 0,
            activities_completed TEXT DEFAULT '[]',
            session_summary      TEXT
        );

        CREATE TABLE IF NOT EXISTS emotion_logs (
            log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id    INTEGER REFERENCES children(child_id),
            timestamp   TEXT DEFAULT CURRENT_TIMESTAMP,
            source      TEXT,
            emotion     TEXT,
            confidence  REAL,
            action_taken TEXT
        );

        CREATE TABLE IF NOT EXISTS chat_logs (
            chat_id          INTEGER PRIMARY KEY AUTOINCREMENT,
            child_id         INTEGER REFERENCES children(child_id),
            timestamp        TEXT DEFAULT CURRENT_TIMESTAMP,
            user_message     TEXT,
            aria_reply       TEXT,
            detected_emotion TEXT,
            suggested_activity TEXT,
            comfort_mode     INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ai_memory (
            child_id              INTEGER PRIMARY KEY REFERENCES children(child_id),
            memory_summary        TEXT DEFAULT '',
            favorite_interaction  TEXT DEFAULT '',
            last_topic            TEXT DEFAULT '',
            last_comfort_strategy TEXT DEFAULT '',
            updated_at            TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    conn.close()


# ─── Parents ────────────────────────────────────────────────────────────────

def create_parent(name, relationship, pin, email="", phone="",
                  report_lang="en", emergency_contact=""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO parents (name, relationship, pin_hash, email, phone,
                             preferred_report_language, emergency_contact)
        VALUES (?,?,?,?,?,?,?)
    """, (name, relationship, hash_pin(pin), email, phone,
          report_lang, emergency_contact))
    conn.commit()
    pid = c.lastrowid
    conn.close()
    return pid


def verify_parent_pin(parent_id, pin):
    conn = get_connection()
    row = conn.execute(
        "SELECT pin_hash FROM parents WHERE parent_id=?", (parent_id,)
    ).fetchone()
    conn.close()
    if row:
        return row["pin_hash"] == hash_pin(pin)
    return False


def get_all_parents():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM parents ORDER BY created_at").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_parent(parent_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM parents WHERE parent_id=?", (parent_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_parent(parent_id, **kwargs):
    if not kwargs:
        return
    if "pin" in kwargs:
        kwargs["pin_hash"] = hash_pin(kwargs.pop("pin"))
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [parent_id]
    conn = get_connection()
    conn.execute(f"UPDATE parents SET {sets} WHERE parent_id=?", vals)
    conn.commit()
    conn.close()


# ─── Children ───────────────────────────────────────────────────────────────

def create_child(parent_id, name, age, language="en",
                 communication_level="short_sentences", sensory_mode="calm"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO children (parent_id, name, age, language,
                              communication_level, sensory_mode)
        VALUES (?,?,?,?,?,?)
    """, (parent_id, name, age, language, communication_level, sensory_mode))
    conn.commit()
    child_id = c.lastrowid

    # Pick default voice based on language
    default_voice = {
        "en": "en-US-JennyNeural",
        "ar": "ar-EG-SalmaNeural",
        "de": "de-DE-KatjaNeural",
    }.get(language, "en-US-JennyNeural")

    # Initialize related tables
    c.execute("INSERT OR IGNORE INTO child_preferences (child_id) VALUES (?)", (child_id,))
    c.execute("INSERT OR IGNORE INTO device_settings (child_id) VALUES (?)", (child_id,))
    c.execute("""INSERT OR IGNORE INTO voice_settings (child_id, voice_name)
                 VALUES (?, ?)""", (child_id, default_voice))
    c.execute("INSERT OR IGNORE INTO ai_memory (child_id) VALUES (?)", (child_id,))
    conn.commit()
    conn.close()
    return child_id


def get_children_for_parent(parent_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM children WHERE parent_id=? ORDER BY name", (parent_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_children():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM children ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_child(child_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM children WHERE child_id=?", (child_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_child(child_id, **kwargs):
    if not kwargs:
        return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [child_id]
    conn = get_connection()
    conn.execute(f"UPDATE children SET {sets} WHERE child_id=?", vals)
    conn.commit()
    conn.close()


def update_child_last_active(child_id):
    conn = get_connection()
    conn.execute(
        "UPDATE children SET last_active=? WHERE child_id=?",
        (datetime.now().isoformat(), child_id)
    )
    conn.commit()
    conn.close()


def clear_child_history(child_id):
    """Erase activity-only data for a child (logs + sessions).

    Keeps the profile, preferences, device/voice settings, and AI memory.
    Use this when a parent wants a 'fresh start' without losing setup.
    """
    conn = get_connection()
    for tbl in ("emotion_logs", "chat_logs", "sessions"):
        conn.execute(f"DELETE FROM {tbl} WHERE child_id=?", (child_id,))
    conn.commit()
    conn.close()


def delete_child(child_id):
    """Fully delete a child profile and every row referencing it.

    Wipes: child row + preferences + device_settings + voice_settings +
    ai_memory + sessions + emotion_logs + chat_logs. Runs in a single
    transaction. If the deleted child was the active one in
    `settings.active_child_id`, that setting is cleared so the home
    screen falls back to the picker.

    Returns True on success, False on any error (caller may surface a toast).
    """
    conn = get_connection()
    try:
        conn.execute("BEGIN")
        # Order matters less because PRAGMA foreign_keys = ON would cascade
        # for ON DELETE CASCADE FKs — but the schema declares plain
        # REFERENCES, so we explicitly clean every child-scoped table.
        for tbl in (
            "emotion_logs", "chat_logs", "sessions",
            "child_preferences", "device_settings",
            "voice_settings", "ai_memory",
        ):
            conn.execute(f"DELETE FROM {tbl} WHERE child_id=?", (child_id,))
        conn.execute("DELETE FROM children WHERE child_id=?", (child_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        return False
    conn.close()

    # If this was the active child, clear the pointer so the app
    # falls back to the welcome picker on next boot.
    try:
        active = get_setting("active_child_id")
        if active and int(active) == int(child_id):
            set_setting("active_child_id", None)
    except Exception:
        pass
    return True


def get_child_preferences(child_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM child_preferences WHERE child_id=?", (child_id,)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        for k in ["favorite_topics", "known_triggers", "calming_methods",
                  "preferred_games", "blocked_topics"]:
            try:
                d[k] = json.loads(d[k])
            except Exception:
                d[k] = []
        return d
    return {}


def update_child_preferences(child_id, **kwargs):
    for k, v in kwargs.items():
        if isinstance(v, list):
            kwargs[k] = json.dumps(v)
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [child_id]
    conn = get_connection()
    conn.execute(
        f"INSERT OR IGNORE INTO child_preferences (child_id) VALUES (?)", (child_id,)
    )
    conn.execute(
        f"UPDATE child_preferences SET {sets} WHERE child_id=?", vals
    )
    conn.commit()
    conn.close()


# ─── Device & Voice Settings ─────────────────────────────────────────────────

def get_device_settings(child_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM device_settings WHERE child_id=?", (child_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def update_device_settings(child_id, **kwargs):
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [child_id]
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO device_settings (child_id) VALUES (?)", (child_id,)
    )
    conn.execute(f"UPDATE device_settings SET {sets} WHERE child_id=?", vals)
    conn.commit()
    conn.close()


def get_voice_settings(child_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM voice_settings WHERE child_id=?", (child_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def update_voice_settings(child_id, **kwargs):
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [child_id]
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO voice_settings (child_id) VALUES (?)", (child_id,)
    )
    conn.execute(f"UPDATE voice_settings SET {sets} WHERE child_id=?", vals)
    conn.commit()
    conn.close()


# ─── Sessions ────────────────────────────────────────────────────────────────

def start_session(child_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO sessions (child_id, start_time) VALUES (?,?)",
        (child_id, datetime.now().isoformat())
    )
    conn.commit()
    sid = c.lastrowid
    conn.close()
    return sid


def end_session(session_id, dominant_emotion="neutral",
                comfort_count=0, activities=None, summary=""):
    conn = get_connection()
    conn.execute("""
        UPDATE sessions SET end_time=?, dominant_emotion=?,
        comfort_mode_count=?, activities_completed=?, session_summary=?
        WHERE session_id=?
    """, (
        datetime.now().isoformat(), dominant_emotion, comfort_count,
        json.dumps(activities or []), summary, session_id
    ))
    conn.commit()
    conn.close()


def get_sessions_for_child(child_id, limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM sessions WHERE child_id=? ORDER BY start_time DESC LIMIT ?",
        (child_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── Emotion Logs ────────────────────────────────────────────────────────────

def log_emotion(child_id, emotion, confidence, source="camera", action="none"):
    conn = get_connection()
    conn.execute("""
        INSERT INTO emotion_logs (child_id, timestamp, source, emotion, confidence, action_taken)
        VALUES (?,?,?,?,?,?)
    """, (child_id, datetime.now().isoformat(), source, emotion, confidence, action))
    conn.commit()
    conn.close()


def get_emotion_logs(child_id, limit=100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM emotion_logs WHERE child_id=? ORDER BY timestamp DESC LIMIT ?",
        (child_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_emotion_summary(child_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    rows = conn.execute(
        "SELECT emotion, COUNT(*) as cnt FROM emotion_logs "
        "WHERE child_id=? AND timestamp LIKE ? GROUP BY emotion",
        (child_id, f"{today}%")
    ).fetchall()
    conn.close()
    return {r["emotion"]: r["cnt"] for r in rows}


# ─── Chat Logs ───────────────────────────────────────────────────────────────

def log_chat(child_id, user_msg, aria_reply, detected_emotion="neutral",
             suggested_activity="none", comfort_mode=False):
    conn = get_connection()
    conn.execute("""
        INSERT INTO chat_logs (child_id, timestamp, user_message, aria_reply,
                               detected_emotion, suggested_activity, comfort_mode)
        VALUES (?,?,?,?,?,?,?)
    """, (child_id, datetime.now().isoformat(), user_msg, aria_reply,
          detected_emotion, suggested_activity, int(comfort_mode)))
    conn.commit()
    conn.close()


def get_chat_logs(child_id, limit=50):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM chat_logs WHERE child_id=? ORDER BY timestamp DESC LIMIT ?",
        (child_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── AI Memory ───────────────────────────────────────────────────────────────

def get_ai_memory(child_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM ai_memory WHERE child_id=?", (child_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else {}


def update_ai_memory(child_id, **kwargs):
    kwargs["updated_at"] = datetime.now().isoformat()
    sets = ", ".join(f"{k}=?" for k in kwargs)
    vals = list(kwargs.values()) + [child_id]
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO ai_memory (child_id) VALUES (?)", (child_id,)
    )
    conn.execute(f"UPDATE ai_memory SET {sets} WHERE child_id=?", vals)
    conn.commit()
    conn.close()


# ─── App Settings ─────────────────────────────────────────────────────────────

def get_setting(key, default=None):
    conn = get_connection()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    if row:
        try:
            return json.loads(row["value"])
        except Exception:
            return row["value"]
    return default


def set_setting(key, value):
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)",
        (key, json.dumps(value))
    )
    conn.commit()
    conn.close()


# Initialize on import
init_database()
