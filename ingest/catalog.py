"""Build/queue the catalog.

  python ingest/catalog.py init                 # load rhino_catalog.csv + data/est_year.json
  python ingest/catalog.py queue CATEGORY... --years 2024-2026 [--start N]
        # queue videos newest-first; priority numbers continue after the current max unless --start
  python ingest/catalog.py status
"""
import argparse
import csv
import json

from db import DATA, ROOT, connect, reset_running


def init(con):
    years = json.load(open(DATA / "est_year.json"))
    rows = list(csv.DictReader(open(ROOT / "rhino_catalog.csv", encoding="utf-8-sig")))
    for r in rows:
        con.execute(
            "INSERT INTO videos(id, ord, category, minutes, title, url, est_year) VALUES (?,?,?,?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET ord=excluded.ord, category=excluded.category, "
            "minutes=excluded.minutes, title=excluded.title, url=excluded.url, est_year=excluded.est_year",
            (r["id"], int(r["order"]), r["category"], float(r["minutes"] or 0), r["title"], r["url"],
             years.get(r["id"])))
    print("videos:", con.execute("SELECT count(*) FROM videos").fetchone()[0])


def queue(con, cats, years, start):
    y0, y1 = (int(x) for x in years.split("-")) if years else (0, 9999)
    n = start if start is not None else (con.execute("SELECT max(priority) FROM videos").fetchone()[0] or 0) + 1
    ids = [r[0] for r in con.execute(
        f"SELECT id FROM videos WHERE priority IS NULL AND category IN ({','.join('?' * len(cats))}) "
        "AND est_year BETWEEN ? AND ? ORDER BY ord", (*cats, y0, y1))]
    for i, vid in enumerate(ids):
        con.execute("UPDATE videos SET priority=? WHERE id=?", (n + i, vid))
    print(f"queued {len(ids)} (priority {n}..{n + len(ids) - 1})")


def status(con):
    for r in con.execute(
            "SELECT category, count(*) n, sum(priority IS NOT NULL) queued, sum(dl='ok') dl, "
            "sum(asr='ok') asr, sum(frm='ok') frm, sum(fin='ok') done, "
            "sum(dl='fail' OR asr='fail' OR frm='fail') failed FROM videos GROUP BY category"):
        print(dict(r))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["init", "queue", "status", "reset"])
    ap.add_argument("cats", nargs="*")
    ap.add_argument("--years")
    ap.add_argument("--start", type=int)
    a = ap.parse_args()
    con = connect()
    {"init": lambda: init(con), "queue": lambda: queue(con, a.cats, a.years, a.start),
     "status": lambda: status(con), "reset": lambda: reset_running(con)}[a.cmd]()
