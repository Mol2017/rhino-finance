"""Download queued videos (720p mp4) into data/work/<id>/, politely, with the Chrome login.

Writes data/raw/<id>/metadata.json (trimmed info.json; real upload_date). Keeps at most
BUFFER downloaded-but-unfinished videos on disk so mp4s never pile up.
usage: python ingest/download_worker.py   (stdlib; calls the yt-dlp binary in .venvs/tools)
"""
import json
import random
import shutil
import subprocess
import sys
import time

from db import RAW, ROOT, WORK, connect, finish, claim

YTDLP = str(ROOT / ".venvs/tools/bin/yt-dlp")
BUFFER = 6
FORMAT = "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]"
KEEP = ("id", "title", "upload_date", "timestamp", "duration", "description", "chapters",
        "availability", "view_count", "like_count", "comment_count")


def main():
    con = connect()
    fails_in_row = 0
    while True:
        pending = con.execute("SELECT count(*) FROM videos WHERE dl='ok' AND fin IS NOT 'ok'").fetchone()[0]
        if pending >= BUFFER:
            time.sleep(20)
            continue
        row = claim(con, "dl", "1=1")
        if not row:
            print("queue empty", flush=True)
            return
        vid = row["id"]
        w = WORK / vid
        w.mkdir(parents=True, exist_ok=True)
        cmd = [YTDLP, "--no-update", "--cookies-from-browser", "chrome:Default", "-q", "--no-warnings",
               "--write-info-json", "--no-write-playlist-metafiles", "-f", FORMAT,
               "--merge-output-format", "mp4", "-o", str(w / "full.%(ext)s"), row["url"]]
        t0 = time.time()
        p = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True)
        mp4 = w / "full.mp4"
        if p.returncode == 0 and mp4.exists():
            info = json.load(open(w / "full.info.json"))
            r = RAW / vid
            r.mkdir(parents=True, exist_ok=True)
            json.dump({k: info.get(k) for k in KEEP}, open(r / "metadata.json", "w"), ensure_ascii=False, indent=1)
            (w / "full.info.json").unlink()
            ud = info.get("upload_date")
            finish(con, vid, "dl", "ok", version=f"yt-dlp:{FORMAT}",
                   upload_date=f"{ud[:4]}-{ud[4:6]}-{ud[6:]}" if ud else None)
            print(f"ok {vid} {mp4.stat().st_size/1e6:.0f}MB {time.time()-t0:.0f}s", flush=True)
            fails_in_row = 0
        else:
            shutil.rmtree(w, ignore_errors=True)
            finish(con, vid, "dl", "fail", err=(p.stderr or "no file")[-500:])
            print(f"FAIL {vid}: {p.stderr[-300:]}", flush=True)
            fails_in_row += 1
            time.sleep(600 * fails_in_row)          # back off: YouTube sometimes limits formats for a while
            if fails_in_row >= 5:
                sys.exit("5 failures in a row; stopping (cookies expired or rate limited?)")
        time.sleep(30 + random.randint(0, 30))


if __name__ == "__main__":
    main()
