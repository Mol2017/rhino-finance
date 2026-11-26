"""Ledger worker: for each fully ingested daily video, extract the decision ledger with headless Claude.

  python3 ledger/worker.py [--model sonnet] [--limit N] [--id VIDEO_ID]

Claims videos whose ingest is finished (fin='ok') and whose `led` stage is unstarted, newest
priority first (same order as ingest). Writes data/ledger/<id>.json and logs cost per video to
data/logs/ledger.log. Spec: eval/LEDGER_SPEC.md. The model may open keyframe images with Read
when OCR is garbled; it has no other tools.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ingest"))
sys.path.insert(0, str(ROOT / "ledger"))
from db import RAW, claim, connect, finish  # noqa: E402
from prompt_input import build  # noqa: E402

OUT = ROOT / "data/ledger"
SPEC = ROOT / "eval/LEDGER_SPEC.md"
REFS = ROOT / "rhino/skill/rhino-stock-analysis/references"
CATS = "('public_daily', 'public_evergreen')"
VERSION_TAG = "ledger-worker-1"

INSTRUCTIONS = """You extract a decision ledger from one daily video of the Chinese US-stock channel 视野环球财经 (host: Rhino).
Follow the spec below exactly. The inputs are the ASR transcript and per-keyframe OCR text. When an OCR line from a
holdings card or level table is garbled and the number matters, open that frame image with the Read tool
(path: data/raw/<video_id>/<file>). Open at most 8 images.
If the video contains no stock or index view (e.g. pure news or teaching), return the file shape with empty lists.
Your final message must be ONLY the JSON object (no prose, no code fence)."""


def prompt(vid):
    rules = (REFS / "04-no-buy-checklist.md").read_text() + "\n" + (REFS / "03-buy-points.md").read_text()
    return (f"{INSTRUCTIONS}\n\n# SPEC\n{SPEC.read_text()}\n\n# RULE BOOK (ids for rules_cited)\n{rules}\n\n"
            f"# INPUT\n{build(vid)}")


def parse(text):
    """First complete JSON object in the reply; ignores anything the model wrote after it."""
    a = text.find("{")
    if a < 0:
        raise ValueError("no JSON object in output")
    obj, _ = json.JSONDecoder().raw_decode(text[a:])
    return obj


def check(vid, led):
    """Cheap sanity checks recorded in the file: quotes found in transcript, zones ordered."""
    tr = re.sub(r"\s", "", "".join(s["text"] for s in json.load(open(RAW / vid / "transcript.json"))["segments"]))
    items = led.get("stocks", []) + led.get("market", [])
    quotes = [x.get("quote") for x in items if x.get("quote")]
    missing = [q for q in quotes if re.sub(r"\s", "", q) not in tr]
    bad_zone = sum(1 for s in led.get("stocks", []) for z in (s.get("supports") or []) + (s.get("resistances") or [])
                   if isinstance(z.get("low"), (int, float)) and isinstance(z.get("high"), (int, float))
                   and z["low"] > z["high"])
    return {"quotes": len(quotes), "quotes_not_in_transcript": len(missing), "zones_reversed": bad_zone}


def run(vid, model):
    p = prompt(vid)
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--no-session-persistence",
           "--strict-mcp-config", "--allowedTools", "Read",
           "--disallowedTools", "Bash", "Edit", "Write", "WebFetch", "WebSearch", "Agent", "NotebookEdit"]
    t0 = time.time()
    cost = 0.0
    for attempt in (1, 2):           # one retry: the model occasionally emits invalid JSON
        r = subprocess.run(cmd, input=p, capture_output=True, text=True, cwd=ROOT, timeout=1200)
        if r.returncode != 0:
            raise RuntimeError(f"claude exit {r.returncode}: {(r.stderr or r.stdout)[-400:]}")
        res = json.loads(r.stdout)
        cost += res.get("total_cost_usd") or 0
        if res.get("is_error"):
            raise RuntimeError(f"claude error: {str(res.get('result'))[-400:]}")
        try:
            led = parse(res["result"])
            break
        except json.JSONDecodeError:
            if attempt == 2:
                raise
    res["total_cost_usd"] = cost
    led["video_id"] = vid
    led["extractor"] = {"worker": VERSION_TAG, "model": model, "spec": led.get("spec"),
                        "input_chars": len(p), "cost_usd": res.get("total_cost_usd"),
                        "seconds": round(time.time() - t0), "check": check(vid, led)}
    OUT.mkdir(parents=True, exist_ok=True)
    json.dump(led, open(OUT / f"{vid}.json", "w"), ensure_ascii=False, indent=1)
    return led


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--id")
    a = ap.parse_args()
    con = connect()
    cols = [r[1] for r in con.execute("PRAGMA table_info(videos)")]
    if "led" not in cols:
        con.execute("ALTER TABLE videos ADD COLUMN led TEXT")
    done, idle, fails = 0, 0, 0
    while True:
        if a.id:
            row = con.execute("SELECT * FROM videos WHERE id=?", (a.id,)).fetchone()
        else:
            row = claim(con, "led", f"fin='ok' AND category IN {CATS}")
        if not row:
            busy = con.execute("SELECT count(*) FROM videos WHERE priority IS NOT NULL AND fin IS NULL "
                               f"AND category IN {CATS} AND dl IS NOT 'fail'").fetchone()[0]
            if busy == 0 or idle > 4 * 3600:
                print("nothing left", flush=True)
                return
            idle += 60
            time.sleep(60)
            continue
        idle = 0
        vid = row["id"]
        try:
            led = run(vid, a.model)
            e = led["extractor"]
            finish(con, vid, "led", "ok", version=f"{VERSION_TAG} {a.model} {e['spec']}")
            print(f"ok {vid} {row['upload_date']} stocks={len(led.get('stocks', []))} "
                  f"market={len(led.get('market', []))} ${e['cost_usd']:.3f} {e['seconds']}s check={e['check']}",
                  flush=True)
            fails = 0
        except Exception as ex:  # noqa: BLE001
            finish(con, vid, "led", "fail", err=repr(ex))
            print(f"FAIL {vid} {ex!r}", flush=True)
            fails += 1
            if fails >= 3:
                sys.exit("3 failures in a row; stopping")
        done += 1
        if a.id or (a.limit and done >= a.limit):
            return


if __name__ == "__main__":
    main()
