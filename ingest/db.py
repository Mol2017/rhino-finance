"""Catalog database shared by all ingest workers (stdlib only, so every venv can import it).

data/catalog.sqlite, table videos: one row per video with a status per stage.
Stage status values: NULL (not started) | 'run' | 'ok' | 'fail' | 'skip'.
A video is worked on only when queued (priority not NULL); lower priority runs first.
"""
import json
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DB = DATA / "catalog.sqlite"
RAW = DATA / "raw"
WORK = DATA / "work"
PIPELINE_VERSION = "ingest-1"

SCHEMA = """
CREATE TABLE IF NOT EXISTS videos (
  id TEXT PRIMARY KEY, ord INTEGER, category TEXT, minutes REAL, title TEXT, url TEXT,
  est_year INTEGER, upload_date TEXT,
  priority INTEGER,
  dl TEXT, asr TEXT, frm TEXT, fin TEXT,
  versions TEXT DEFAULT '{}', err TEXT, attempts INTEGER DEFAULT 0, updated_at REAL
);
CREATE INDEX IF NOT EXISTS ix_pri ON videos(priority);
"""


def connect():
    con = sqlite3.connect(DB, timeout=60, isolation_level=None)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def claim(con, stage, where):
    """Atomically pick the next queued video whose `stage` is unstarted and `where` holds; mark it 'run'."""
    con.execute("BEGIN IMMEDIATE")
    row = con.execute(
        f"SELECT * FROM videos WHERE priority IS NOT NULL AND {stage} IS NULL AND {where} "
        "ORDER BY priority LIMIT 1").fetchone()
    if row:
        con.execute(f"UPDATE videos SET {stage}='run', updated_at=? WHERE id=?", (time.time(), row["id"]))
    con.execute("COMMIT")
    return row


def finish(con, vid, stage, status, version=None, err=None, **cols):
    sets, args = [f"{stage}=?", "updated_at=?"], [status, time.time()]
    if err is not None:
        sets += ["err=?", "attempts=attempts+1"]
        args.append(f"{stage}: {err}"[:2000])
    for k, v in cols.items():
        sets.append(f"{k}=?")
        args.append(v)
    con.execute(f"UPDATE videos SET {', '.join(sets)} WHERE id=?", (*args, vid))
    if version:
        v = json.loads(con.execute("SELECT versions FROM videos WHERE id=?", (vid,)).fetchone()[0] or "{}")
        v[stage] = version
        con.execute("UPDATE videos SET versions=? WHERE id=?", (json.dumps(v), vid))


def reset_running(con):
    """After a crash: put stages left in 'run' back to unstarted."""
    for s in ("dl", "asr", "frm", "fin"):
        con.execute(f"UPDATE videos SET {s}=NULL WHERE {s}='run'")
