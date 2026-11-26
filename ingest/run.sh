#!/usr/bin/env bash
# Start the three ingest workers in the background; logs in data/logs/.
# Safe to re-run: stages left 'run' by a crash are reset first.
cd "$(dirname "$0")/.." || exit 1
python3 ingest/catalog.py reset
L=data/logs; mkdir -p $L
nohup python3 ingest/download_worker.py >> $L/download.log 2>&1 &
nohup ~/.local/share/whisper-venv/bin/python ingest/asr_worker.py >> $L/asr.log 2>&1 &
for i in 1 2 3; do OCR_THREADS=6 nohup .venvs/tools/bin/python ingest/frames_worker.py >> $L/frames.log 2>&1 & done
echo "started; tail -f $L/*.log ; python3 ingest/catalog.py status"
# ledger extraction (headless Claude, cheaper model) follows the finished videos
nohup python3 ledger/worker.py --model sonnet >> $L/ledger.log 2>&1 &
nohup python3 learn/worker.py --model opus >> $L/learn.log 2>&1 &
