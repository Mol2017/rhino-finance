"""Table mode for spreadsheet-heavy videos (weekly valuation episodes).

Every SAMPLE_EVERY seconds: OCR the frame, rebuild rows from box y-coordinates,
keep the frame only if its row text differs enough from the last kept frame.
Output: media/<id>/table_frames.json  [{"t":sec, "rows":["cell | cell | ..."]}]
usage: python table_frames.py <media_dir> <id> [...]   (OCR venv python)
"""
import json, subprocess, sys, tempfile
from pathlib import Path
from rapidocr_onnxruntime import RapidOCR

SAMPLE_EVERY = 5
MIN_NEW = 0.15   # keep frame if >=15% of its rows are new vs last kept frame
UI_NOISE = {"开始", "插入", "页面布局", "公式", "数据", "审阅", "视图", "帮助", "fx", "B", "C", "D", "E", "F", "G", "H", "K", "M"}


def rows_from(res):
    boxes = []
    for box, text, score in res or []:
        if score < 0.6 or text.strip() in UI_NOISE:
            continue
        ys = [p[1] for p in box]; xs = [p[0] for p in box]
        boxes.append(((min(ys) + max(ys)) / 2, min(xs), max(ys) - min(ys), text.strip()))
    boxes.sort()
    rows, cur, cy = [], [], None
    for y, x, h, t in boxes:
        if cy is not None and abs(y - cy) > max(h * 0.6, 6):
            rows.append(cur); cur, cy = [], None
        if cy is None:
            cy = y          # row anchored at its first box's centre
        cur.append((x, t))
    if cur: rows.append(cur)
    return [" | ".join(t for _, t in sorted(r)) for r in rows]


def main():
    media = Path(sys.argv[1]); ocr = RapidOCR()
    for vid in sys.argv[2:]:
        d = media / vid
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(d / "video.mp4" if (d / "video.mp4").exists() else d / "full.mp4"),
                            "-vf", f"fps=1/{SAMPLE_EVERY}", "-q:v", "2", f"{tmp}/c%05d.jpg"], check=True)
            kept, last = [], set()
            for i, f in enumerate(sorted(Path(tmp).glob("c*.jpg"))):
                res, _ = ocr(str(f))
                rows = rows_from(res)
                new = set(rows) - last
                if rows and len(new) >= MIN_NEW * len(rows):
                    kept.append({"t": i * SAMPLE_EVERY, "rows": rows}); last = set(rows)
        json.dump(kept, open(d / "table_frames.json", "w"), ensure_ascii=False, indent=1)
        print(vid, "kept", len(kept), flush=True)


if __name__ == "__main__":
    main()
