"""Result cache: identical idea + tone (Auto mode) reuses the last full result.

Stored in the same SQLite file as run history (data/performance.db).
"""
import hashlib
import json
import sqlite3
import time
from contextlib import closing

from utils.history_db import DB_PATH

TTL_DAYS = 7


def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, ts REAL NOT NULL, payload TEXT NOT NULL)"
    )
    return conn


def make_key(topic: str, tone: str) -> str:
    normalized = " ".join((topic or "").lower().split()) + "|" + (tone or "").lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get(key: str):
    """Return the cached payload (dict) or None if missing/expired."""
    with closing(_conn()) as c:
        row = c.execute("SELECT ts, payload FROM cache WHERE key = ?", (key,)).fetchone()
    if not row:
        return None
    ts, payload = row
    if time.time() - ts > TTL_DAYS * 86400:
        return None
    return json.loads(payload)


def put(key: str, payload: dict):
    with closing(_conn()) as c, c:
        c.execute(
            "INSERT OR REPLACE INTO cache (key, ts, payload) VALUES (?, ?, ?)",
            (key, time.time(), json.dumps(payload)),
        )


def count() -> int:
    with closing(_conn()) as c:
        return c.execute("SELECT COUNT(*) FROM cache").fetchone()[0]


def clear():
    with closing(_conn()) as c, c:
        c.execute("DELETE FROM cache")