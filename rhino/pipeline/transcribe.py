"""Batch-transcribe media/<id>/audio.m4a -> media/<id>/transcript.json with faster-whisper.

usage: python transcribe.py <media_dir> [id ...]
Run with the whisper venv python (~/.local/share/whisper-venv/bin/python).
"""
import json
import sys
import time
from pathlib import Path

from faster_whisper import BatchedInferencePipeline, WhisperModel

PROMPT = (
    "以下是美股财经节目《视野环球财经》，主讲人Rhino，简体中文，带标点。"
    "常见词：标普SPX、SPY、纳指QQQ、费城半导体SOXX、SMH、CTA、对冲基金、EPS、前瞻估值、"
    "支撑、压力、止跌、回撤、NVDA、TSM、MSFT、GOOG、AMZN、META、AAPL、AMD、AVGO、TSLA、ISRG、VIX。"
)


def main():
    media = Path(sys.argv[1])
    ids = sys.argv[2:] or sorted(p.name for p in media.iterdir() if (p / "audio.m4a").exists())
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    pipe = BatchedInferencePipeline(model=model)
    for vid in ids:
        src = media / vid / "audio.m4a"
        dst = media / vid / "transcript.json"
        if dst.exists() or not src.exists():
            continue
        t0 = time.time()
        segs, info = pipe.transcribe(
            str(src), language="zh", batch_size=int(__import__("os").environ.get("ASR_BATCH", "8")), vad_filter=True,
            initial_prompt=PROMPT, condition_on_previous_text=False,
        )
        out = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
        el = time.time() - t0
        json.dump({"id": vid, "duration": info.duration, "asr_seconds": round(el, 1),
                   "segments": out}, open(dst, "w"), ensure_ascii=False, indent=0)
        print(f"{vid} dur={info.duration/60:.1f}min asr={el:.0f}s speed={info.duration/el:.1f}x", flush=True)


if __name__ == "__main__":
    main()
