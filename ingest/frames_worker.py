"""Keyframes + OCR for downloaded videos -> data/raw/<id>/frames/*.webp, frames.json
(weekly valuation / sector EPS videos also get table_frames.json via the table-mode sampler).
Then finalize: once ASR and frames are both done, delete data/work/<id>/ (the mp4).

usage: OCR_THREADS=6 .venvs/tools/bin/python ingest/frames_worker.py   (several workers can run at once)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import imagehash
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

from db import RAW, ROOT, WORK, claim, connect, finish

SAMPLE_EVERY, HASH_DIST = 10, 10
NOISE = re.compile(r"视野环球财经|YouTube唯一平台")
TABLE_CATS = {"member_weekly_valuation", "member_sector_eps"}
VERSION = f"frames-2 keyframe-decode every{SAMPLE_EVERY}s phash<{HASH_DIST} rapidocr webp80"


def sample(video: Path, tmp: Path, every: int):
    tmp.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-skip_frame", "nokey", "-i", str(video),
                    "-vf", f"fps=1/{every},scale=1280:-1", "-q:v", "3", str(tmp / "c%05d.jpg")], check=True)
    return sorted(tmp.glob("c*.jpg"))


def keyframes(ocr, vid):
    r = RAW / vid
    out = r / "frames"
    out.mkdir(exist_ok=True)
    tmp = WORK / vid / "_cand"
    cands = sample(WORK / vid / "full.mp4", tmp, SAMPLE_EVERY)
    kept, last = [], None
    for i, f in enumerate(cands):
        img = Image.open(f)
        h = imagehash.phash(img)
        if last is not None and h - last < HASH_DIST:
            continue
        last = h
        t = i * SAMPLE_EVERY
        res, _ = ocr(str(f))
        lines = [x[1] for x in (res or []) if x[2] > 0.6 and not NOISE.search(x[1])]
        name = f"t{t:05d}.webp"
        img.save(out / name, "WEBP", quality=80)
        kept.append({"t": t, "file": f"frames/{name}", "ocr": "\n".join(lines)})
    shutil.rmtree(tmp, ignore_errors=True)
    json.dump(kept, open(r / "frames.json", "w"), ensure_ascii=False, indent=1)
    return len(cands), len(kept)


def tables(vid):
    """Reuse the pilot table sampler (5 s, row-text dedupe)."""
    p = subprocess.run([sys.executable, str(ROOT / "rhino/pipeline/table_frames.py"), str(WORK), vid],
                       capture_output=True, text=True)
    src = WORK / vid / "table_frames.json"
    if p.returncode != 0 or not src.exists():
        raise RuntimeError(p.stderr[-500:])
    shutil.move(src, RAW / vid / "table_frames.json")


def finalize(con):
    for row in con.execute("SELECT id FROM videos WHERE asr='ok' AND frm='ok' AND fin IS NULL").fetchall():
        shutil.rmtree(WORK / row["id"], ignore_errors=True)
        finish(con, row["id"], "fin", "ok")


def main():
    con = connect()
    th = int(os.environ.get("OCR_THREADS", "0"))
    ocr = RapidOCR(**{f"{m}_intra_op_num_threads": th for m in ("det", "cls", "rec")}) if th else RapidOCR()
    idle = 0
    while True:
        finalize(con)
        row = claim(con, "frm", "dl='ok'")
        if not row:
            left = con.execute("SELECT count(*) FROM videos WHERE priority IS NOT NULL AND (dl IS NULL OR dl='run' OR asr IS NULL OR asr='run') AND dl IS NOT 'fail'").fetchone()[0]
            if left == 0 and idle > 120:
                finalize(con)
                print("done", flush=True)
                return
            idle += 15
            time.sleep(15)
            continue
        idle = 0
        vid = row["id"]
        try:
            t0 = time.time()
            n, k = keyframes(ocr, vid)
            ver = VERSION
            if row["category"] in TABLE_CATS:
                tables(vid)
                ver += " +table-1"
            finish(con, vid, "frm", "ok", version=ver)
            print(f"ok {vid} cand={n} kept={k} {time.time()-t0:.0f}s", flush=True)
        except Exception as e:  # noqa: BLE001
            finish(con, vid, "frm", "fail", err=repr(e))
            print(f"FAIL {vid} {e!r}", flush=True)


if __name__ == "__main__":
    main()
