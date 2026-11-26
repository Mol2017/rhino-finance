"""Learn worker: turn each fully ingested teaching video into a clean transcript and a method extract.

  python3 learn/worker.py [--model opus] [--id VIDEO_ID] [--limit N]

Claims videos with fin='ok', `lrn` unstarted, and either category member_teaching or a negative
priority (hand-picked episodes, e.g. weekly ep 79), in priority order. Two headless Claude calls,
following rhino/pipeline/CLEAN_SPEC.md:
  1. transcript + OCR (+ table rows for weekly)  -> data/clean/<id>.md   (readable, no summarising)
  2. data/clean/<id>.md                          -> data/extract/<id>.json (principles, methods, cases)
Logs to stdout (run.sh sends it to data/logs/learn.log).
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ingest"))
sys.path.insert(0, str(ROOT / "ledger"))
from db import RAW, claim, connect, finish  # noqa: E402
from prompt_input import build  # noqa: E402

CLEAN, EXTRACT = ROOT / "data/clean", ROOT / "data/extract"
SPEC = ROOT / "rhino/pipeline/CLEAN_SPEC.md"
VERSION_TAG = "learn-worker-1"
WHERE = "fin='ok' AND (category='member_teaching' OR priority < 0)"

ROLE = ("You process one member video of the Chinese US-stock channel 视野环球财经 (host: Rhino). "
        "Follow the spec below exactly. Inputs are an ASR transcript without punctuation (homophone errors are common) "
        "and OCR of deduplicated keyframes (teaching slides). You may open at most 6 keyframe images with Read "
        "(path data/raw/<video_id>/<file>) when a slide's OCR is garbled and its content matters.")
STEP1 = ("TASK: write the readable transcript `clean.md` described in section 1 of the spec, in Chinese. "
         "Keep every substantive sentence; do not summarise. Your final message must be ONLY the markdown "
         "(no code fence, no comments before or after).")
STEP2 = ("TASK: write `extract.json` described in section 2 of the spec from the cleaned transcript below. "
         "Be complete: every transferable rule, threshold, formula, data source and worked example he gives. "
         "Your final message must be ONLY the JSON object (no prose, no code fence).")
TOOLS = ["--allowedTools", "Read", "--disallowedTools", "Bash", "Edit", "Write", "WebFetch", "WebSearch",
         "Agent", "NotebookEdit"]


def table_rows(vid):
    f = RAW / vid / "table_frames.json"
    if not f.exists():
        return ""
    seen, out = set(), []
    for fr in json.load(open(f)):
        for r in fr["rows"]:
            if r not in seen:
                seen.add(r)
                out.append(r)
    return "\n## TABLE ROWS (OCR of the spreadsheet, first occurrence of each row)\n" + "\n".join(out) + "\n"


def call(prompt, model):
    cmd = ["claude", "-p", "--model", model, "--output-format", "json", "--no-session-persistence",
           "--strict-mcp-config", *TOOLS]
    r = subprocess.run(cmd, input=prompt, capture_output=True, text=True, cwd=ROOT, timeout=2400)
    if r.returncode != 0:
        raise RuntimeError(f"claude exit {r.returncode}: {(r.stderr or r.stdout)[-400:]}")
    res = json.loads(r.stdout)
    if res.get("is_error"):
        raise RuntimeError(f"claude error: {str(res.get('result'))[-400:]}")
    return res["result"], res.get("total_cost_usd") or 0


def parse_json(text):
    a = text.find("{")
    if a < 0:
        raise ValueError("no JSON object in output")
    return json.JSONDecoder().raw_decode(text[a:])[0]


def run(vid, model):
    t0, cost = time.time(), 0.0
    spec = SPEC.read_text()
    md, c = call(f"{ROLE}\n\n# SPEC\n{spec}\n\n{STEP1}\n\n# INPUT\n{build(vid)}{table_rows(vid)}", model)
    cost += c
    md = md.strip()
    if md.startswith("```"):
        md = md.split("\n", 1)[1].rsplit("```", 1)[0]
    CLEAN.mkdir(parents=True, exist_ok=True)
    (CLEAN / f"{vid}.md").write_text(md)
    p2 = f"{ROLE}\n\n# SPEC\n{spec}\n\n{STEP2}\n\n# CLEANED TRANSCRIPT\nvideo_id: {vid}\n{md}"
    for attempt in (1, 2):
        txt, c = call(p2, model)
        cost += c
        try:
            ex = parse_json(txt)
            break
        except (json.JSONDecodeError, ValueError):
            if attempt == 2:
                raise
    ex["video_id"] = vid
    ex["extractor"] = {"worker": VERSION_TAG, "model": model, "cost_usd": round(cost, 3),
                       "seconds": round(time.time() - t0), "clean_chars": len(md)}
    EXTRACT.mkdir(parents=True, exist_ok=True)
    json.dump(ex, open(EXTRACT / f"{vid}.json", "w"), ensure_ascii=False, indent=1)
    return ex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="opus")
    ap.add_argument("--id")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    con = connect()
    if "lrn" not in [r[1] for r in con.execute("PRAGMA table_info(videos)")]:
        con.execute("ALTER TABLE videos ADD COLUMN lrn TEXT")
    done, idle, fails = 0, 0, 0
    while True:
        row = (con.execute("SELECT * FROM videos WHERE id=?", (a.id,)).fetchone() if a.id
               else claim(con, "lrn", WHERE))
        if not row:
            busy = con.execute("SELECT count(*) FROM videos WHERE priority IS NOT NULL AND fin IS NULL "
                               "AND (category='member_teaching' OR priority < 0) AND dl IS NOT 'fail'").fetchone()[0]
            if busy == 0 or idle > 4 * 3600:
                print("nothing left", flush=True)
                return
            idle += 60
            time.sleep(60)
            continue
        idle = 0
        vid = row["id"]
        try:
            ex = run(vid, a.model)
            e = ex["extractor"]
            finish(con, vid, "lrn", "ok", version=f"{VERSION_TAG} {a.model}")
            print(f"ok {vid} principles={len(ex.get('principles', []))} methods={len(ex.get('methods', []))} "
                  f"cases={len(ex.get('stock_cases', []))} ${e['cost_usd']:.2f} {e['seconds']}s "
                  f"{row['title'][:40]}", flush=True)
            fails = 0
        except Exception as ex:  # noqa: BLE001
            finish(con, vid, "lrn", "fail", err=repr(ex))
            print(f"FAIL {vid} {ex!r}", flush=True)
            fails += 1
            if fails >= 3:
                sys.exit("3 failures in a row; stopping")
        done += 1
        if a.id or (a.limit and done >= a.limit):
            return


if __name__ == "__main__":
    main()
