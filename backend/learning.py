"""Implicit-feedback learning and listening-history store for SONORA AI.

This is a transparent, lightweight event-learning layer. It is not a neural
model or a production multi-tenant identity system. Events are stored in the
existing SQLite database and decayed by age when converted into preferences.
"""
from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "sonora.db"
ALLOWED_EVENTS = {"play", "skip", "complete", "like", "dislike", "save", "search", "queue_add"}
EVENT_WEIGHTS = {
    "play": 0.08,
    "skip": -0.22,
    "complete": 0.55,
    "like": 0.85,
    "dislike": -1.0,
    "save": 0.65,
    "search": 0.02,
    "queue_add": 0.05,
}


def connect():
    connection = sqlite3.connect(DB_PATH, timeout=15)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_learning_store():
    with connect() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS listening_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            track_id TEXT,
            event_type TEXT NOT NULL,
            duration_seconds REAL NOT NULL DEFAULT 0,
            track_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_listening_user_time ON listening_events(user_id, id DESC)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_listening_user_track ON listening_events(user_id, track_id)")


def record_event(user_id: str, event_type: str, track_id: str | None = None,
                 duration_seconds: float = 0, track: dict[str, Any] | None = None):
    if event_type not in ALLOWED_EVENTS:
        raise ValueError(f"Unsupported event type: {event_type}")
    safe_duration = max(0.0, min(float(duration_seconds or 0), 86400.0))
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO listening_events(user_id, track_id, event_type, duration_seconds, track_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, track_id, event_type, safe_duration,
             json.dumps(track or {}, ensure_ascii=False), datetime.now(timezone.utc).isoformat())
        )
        return cursor.lastrowid


def get_implicit_preferences(user_id: str) -> dict[str, float]:
    """Return recency-decayed implicit preference scores in [-1, 1]."""
    with connect() as db:
        rows = db.execute(
            "SELECT track_id, event_type, created_at FROM listening_events WHERE user_id=? AND track_id IS NOT NULL ORDER BY id DESC LIMIT 5000",
            (user_id,)
        ).fetchall()
    now = datetime.now(timezone.utc)
    totals: dict[str, float] = {}
    weights: dict[str, float] = {}
    for row in rows:
        try:
            stamp = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            age_days = max(0.0, (now - stamp).total_seconds() / 86400)
        except (ValueError, TypeError):
            age_days = 30.0
        decay = math.pow(0.5, age_days / 30.0)
        weight = decay
        value = EVENT_WEIGHTS.get(row["event_type"], 0.0)
        key = str(row["track_id"])
        totals[key] = totals.get(key, 0.0) + value * weight
        weights[key] = weights.get(key, 0.0) + weight
    return {key: max(-1.0, min(1.0, value / max(1.0, weights[key] * 0.65))) for key, value in totals.items()}


def get_listening_history(user_id: str, limit: int = 50):
    limit = max(1, min(int(limit), 200))
    with connect() as db:
        rows = db.execute(
            "SELECT track_id, event_type, duration_seconds, track_json, created_at FROM listening_events WHERE user_id=? AND track_id IS NOT NULL AND event_type IN ('play','complete','skip') ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
    history = []
    for row in rows:
        try:
            track = json.loads(row["track_json"] or "{}")
        except json.JSONDecodeError:
            track = {}
        history.append({"track_id": row["track_id"], "event": row["event_type"],
                        "duration_seconds": row["duration_seconds"], "track": track,
                        "created_at": row["created_at"]})
    return history


def get_learning_analytics(user_id: str):
    with connect() as db:
        total = db.execute("SELECT COUNT(*) FROM listening_events WHERE user_id=?", (user_id,)).fetchone()[0]
        by_type = db.execute("SELECT event_type, COUNT(*) AS n FROM listening_events WHERE user_id=? GROUP BY event_type", (user_id,)).fetchall()
        unique_tracks = db.execute("SELECT COUNT(DISTINCT track_id) FROM listening_events WHERE user_id=? AND track_id IS NOT NULL", (user_id,)).fetchone()[0]
        seconds = db.execute("SELECT SUM(duration_seconds) FROM listening_events WHERE user_id=?", (user_id,)).fetchone()[0] or 0
    return {"total_events": total, "unique_tracks": unique_tracks,
            "listened_seconds": round(seconds, 1),
            "events_by_type": {row["event_type"]: row["n"] for row in by_type}}


initialize_learning_store()
