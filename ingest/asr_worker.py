"""Transcribe downloaded videos -> data/raw/<id>/transcript.json (faster-whisper large-v3, GPU).

usage: ~/.local/share/whisper-venv/bin/python ingest/asr_worker.py
Env: ASR_BATCH (default 8). Exits after IDLE_EXIT seconds with nothing to do and the download queue empty.
"""
import json
import os
import time

from faster_whisper import BatchedInferencePipeline, WhisperModel, __version__ as fw_version

from db import RAW, WORK, claim, connect, finish

MODEL = "large-v3"
PROMPT = (
    "以下是美股财经节目《视野环球财经》，主讲人Rhino，简体中文，带标点。"
    "常见词：标普SPX、SPY、纳指QQQ、费城半导体SOXX、SMH、CTA、对冲基金、EPS、前瞻估值、"
    "支撑、压力、止跌、回撤、NVDA、TSM、MSFT、GOOG、AMZN、META、AAPL、AMD、AVGO、TSLA、ISRG、VIX。"
)
VERSION = f"faster-whisper {fw_version} {MODEL} fp16 vad batched prompt-v1"


def main():
    con = connect()
    model = WhisperModel(MODEL, device="cuda", compute_type="float16")
    pipe = BatchedInferencePipeline(model=model)
    batch = int(os.environ.get("ASR_BATCH", "8"))
    idle = 0
    while True:
        row = claim(con, "asr", "dl='ok'")
        if not row:
            left = con.execute("SELECT count(*) FROM videos WHERE priority IS NOT NULL AND dl IS NULL OR dl='run'").fetchone()[0]
            if left == 0 and idle > 120:
                print("done", flush=True)
                return
            idle += 15
            time.sleep(15)
            continue
        idle = 0
        vid = row["id"]
        try:
            t0 = time.time()
            segs, info = pipe.transcribe(str(WORK / vid / "full.mp4"), language="zh", batch_size=batch,
                                         vad_filter=True, initial_prompt=PROMPT, condition_on_previous_text=False)
            out = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
            el = time.time() - t0
            json.dump({"id": vid, "version": VERSION, "duration": info.duration, "asr_seconds": round(el, 1),
                       "segments": out}, open(RAW / vid / "transcript.json", "w"), ensure_ascii=False, indent=0)
            finish(con, vid, "asr", "ok", version=VERSION)
            print(f"ok {vid} {info.duration/60:.1f}min {info.duration/el:.0f}x", flush=True)
        except Exception as e:  # noqa: BLE001
            finish(con, vid, "asr", "fail", err=repr(e))
            print(f"FAIL {vid} {e!r}", flush=True)


if __name__ == "__main__":
    main()
