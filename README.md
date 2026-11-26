# rhino-finance

A personal study project that models how the YouTube channel 视野环球财经 (Rhino) makes US-stock decisions: the process, not the results.

- `ingest/`, `learn/`, `ledger/`, `rhino/pipeline/`: download, transcribe, OCR and extract teaching videos into method notes (raw media and transcripts are not in this repo).
- `rhino/skill/rhino-stock-analysis/`: a Claude Code skill that applies the method to a live ticker, with a Yahoo Finance data script.
- `docs/`: the method write-ups (valuation, support/entry, the overall decision flow).
- `eval/`, `rhino/eval/`: ledger backtests and skill test runs.

Not investment advice.
