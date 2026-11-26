# rhino-stock-analysis

A Claude Code skill that applies the decision process of the YouTube channel 视野环球财经 (Rhino) to a US stock: forward value range, support/resistance strength, bottoming candles, the 9 buy points, the 18 no-buy rules, left-side tranches and scenario plans.

- `rhino/skill/rhino-stock-analysis/SKILL.md`: the workflow and output format.
- `references/01-07`: valuation, support/resistance, buy points, no-buy checklist, position and risk, market context, indicators.
- `scripts/rhino_data.py`: prints a Yahoo Finance fact sheet for one ticker (needs `pip install yfinance`).

Install: copy or symlink `rhino/skill/rhino-stock-analysis` into `~/.claude/skills/`.

A personal study tool. Not investment advice.
