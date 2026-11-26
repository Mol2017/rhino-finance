"""Extract de-duplicated keyframes + local OCR for media/<id>/video.mp4.

Output: media/<id>/frames/*.jpg and media/<id>/frames.json
  [{"t": seconds, "file": "...", "ocr": "text lines"}]
usage: python keyframes.py <media_dir> [id ...]   (run with the OCR venv python)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import imagehash
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

SAMPLE_EVERY = 10      # seconds between candidate frames
HASH_DIST = 10         # phash distance below which a frame counts as a duplicate
NOISE = re.compile(r"视野环球财经|YouTube唯一平台")  # channel watermark


def extract(video: Path, tmp: Path):
    tmp.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video),
                    "-vf", f"fps=1/{SAMPLE_EVERY},scale=1280:-1", "-q:v", "3",
                    str(tmp / "c%05d.jpg")], check=True)
    return sorted(tmp.glob("c*.jpg"))


def main():
    media = Path(sys.argv[1])
    ids = sys.argv[2:] or sorted(p.name for p in media.iterdir() if (p / "video.mp4").exists())
    ocr = RapidOCR()
    for vid in ids:
        d = media / vid
        if (d / "frames.json").exists() or not (d / "video.mp4").exists():
            continue
        cands = extract(d / "video.mp4", d / "_cand")
        out_dir = d / "frames"
        out_dir.mkdir(exist_ok=True)
        kept, last = [], None
        for i, f in enumerate(cands):
            h = imagehash.phash(Image.open(f))
            if last is not None and h - last < HASH_DIST:
                f.unlink()
                continue
            last = h
            t = i * SAMPLE_EVERY
            res, _ = ocr(str(f))
            lines = [r[1] for r in (res or []) if r[2] > 0.6 and not NOISE.search(r[1])]
            name = f"t{t:05d}.jpg"
            f.rename(out_dir / name)
            kept.append({"t": t, "file": f"frames/{name}", "ocr": "\n".join(lines)})
        for f in (d / "_cand").glob("*.jpg"):
            f.unlink()
        (d / "_cand").rmdir()
        json.dump(kept, open(d / "frames.json", "w"), ensure_ascii=False, indent=1)
        print(f"{vid} candidates={len(cands)} kept={len(kept)}", flush=True)


if __name__ == "__main__":
    main()
