"""SQLite storage for pipeline run history (data/performance.db)."""
import json
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "performance.db"

# Columns added after the first release. Older databases are migrated in place.
_EXTRA_COLUMNS = {"draft": "TEXT", "virality": "INTEGER", "rating": "INTEGER"}


def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            topic TEXT,
            tone TEXT,
            mode TEXT,
            platforms TEXT,
            retries INTEGER,
            cost REAL,
            outputs TEXT,
            draft TEXT,
            virality INTEGER,
            rating INTEGER
        )"""
    )
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(runs)")}
    for col, kind in _EXTRA_COLUMNS.items():
        if col not in existing:
            conn.execute(f"ALTER TABLE runs ADD COLUMN {col} {kind}")
    return conn


def save_run(topic, tone, mode, platforms, retries, cost, outputs, draft="", virality=None):
    """Insert a finished run and return its id."""
    with closing(_conn()) as c, c:
        cur = c.execute(
            "INSERT INTO runs (ts, topic, tone, mode, platforms, retries, cost, outputs, draft, virality) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                datetime.now().isoformat(timespec="seconds"),
                topic, tone, mode,
                json.dumps(platforms), retries, cost, json.dumps(outputs),
                draft, virality,
            ),
        )
        return cur.lastrowid


def update_outputs(run_id, outputs):
    """Keep History in sync after a hook was rewritten."""
    with closing(_conn()) as c, c:
        c.execute("UPDATE runs SET outputs = ? WHERE id = ?", (json.dumps(outputs), run_id))


def set_rating(run_id, rating):
    """rating: 1-5, or None to clear."""
    with closing(_conn()) as c, c:
        c.execute("UPDATE runs SET rating = ? WHERE id = ?", (rating, run_id))


def rated_count() -> int:
    with closing(_conn()) as c:
        return c.execute("SELECT COUNT(*) FROM runs WHERE rating IS NOT NULL").fetchone()[0]


def rated_runs(limit=200):
    """Rated runs, newest first (used by the Strategist)."""
    with closing(_conn()) as c:
        rows = c.execute(
            "SELECT * FROM runs WHERE rating IS NOT NULL ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_decode(r) for r in rows]


def today_stats():
    """(runs, cost, posts) for runs saved today (local time)."""
    today = datetime.now().strftime("%Y-%m-%d")
    with closing(_conn()) as c:
        rows = c.execute("SELECT cost, platforms FROM runs WHERE ts LIKE ?", (today + "%",)).fetchall()
    return (
        len(rows),
        sum(r["cost"] or 0 for r in rows),
        sum(len(json.loads(r["platforms"] or "[]")) for r in rows),
    )


def _decode(row):
    d = dict(row)
    d["platforms"] = json.loads(d["platforms"] or "[]")
    d["outputs"] = json.loads(d["outputs"] or "{}")
    return d


def list_runs(limit=50):
    with closing(_conn()) as c:
        rows = c.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [_decode(r) for r in rows]


def clear_runs():
    with closing(_conn()) as c, c:
        c.execute("DELETE FROM runs")