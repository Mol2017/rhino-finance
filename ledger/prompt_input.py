"""Build the compact text input for ledger extraction from data/raw/<id>/.

Transcript: segments merged into ~20 s lines "[mm:ss] text".
OCR: lines that appear in more than 25% of frames (trading-software chrome, menus) are dropped;
each remaining frame becomes "[mm:ss] frames/tNNNNN.webp | line | line ...".
"""
import collections
import json
import re
from pathlib import Path

NOISE = re.compile(r"^[\d.,:%↑↓+\-*!/ ]+$|^(MA|EMA|VOL|MACD|BOLL|RSI)\w*[:：]?[\d.]*$|分时|多日|日K|周K|月K|1分K|^(最高价|最低价|开盘价|昨收价|平均价|振幅|换手率|市盈率|市净率|52周|委比|量比|成交|总股|流通|市值|盘后价|盘前价|平盘)")
RAW = Path(__file__).resolve().parent.parent / "data/raw"


def mmss(t):
    t = int(t)
    return f"{t // 60:02d}:{t % 60:02d}"


def transcript(vid, chunk=20):
    segs = json.load(open(RAW / vid / "transcript.json"))["segments"]
    out, cur, t0 = [], [], None
    for s in segs:
        if t0 is None:
            t0 = s["start"]
        cur.append(s["text"])
        if s["end"] - t0 >= chunk:
            out.append(f"[{mmss(t0)}] {''.join(cur)}")
            cur, t0 = [], None
    if cur:
        out.append(f"[{mmss(t0)}] {''.join(cur)}")
    return "\n".join(out)


def ocr(vid, max_share=0.25):
    frames = json.load(open(RAW / vid / "frames.json"))
    cnt = collections.Counter(l for f in frames for l in set(f["ocr"].splitlines()))
    lim = max(2, max_share * len(frames))
    out = []
    for f in frames:
        lines = [l.strip() for l in f["ocr"].splitlines()
                 if cnt[l] <= lim and len(l.strip()) >= 2 and not NOISE.search(l.strip())]
        if lines:
            out.append(f"[{mmss(f['t'])}] {f['file']} | " + " | ".join(lines))
    return "\n".join(out)


def build(vid):
    meta = json.load(open(RAW / vid / "metadata.json"))
    return (f"video_id: {vid}\nupload_date: {meta.get('upload_date')}\ntitle: {meta.get('title')}\n\n"
            f"## TRANSCRIPT (ASR, may contain homophone errors)\n{transcript(vid)}\n\n"
            f"## ON-SCREEN TEXT (OCR per keyframe; images are in data/raw/{vid}/)\n{ocr(vid)}\n")


if __name__ == "__main__":
    import sys
    print(build(sys.argv[1]))
