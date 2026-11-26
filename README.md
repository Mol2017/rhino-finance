# rhino-stock-analysis

A Claude Code skill that applies the decision process of the YouTube channel 视野环球财经 (Rhino) to a US stock: forward value range, support/resistance strength, bottoming candles, the 9 buy points, the 18 no-buy rules, left-side tranches and scenario plans.

```
skills/rhino-stock-analysis/
├── SKILL.md            workflow and output format
├── references/         01 valuation · 02 support/resistance · 03 buy points · 04 no-buy checklist
│                       05 position and risk · 06 market context · 07 indicators
└── scripts/
    └── rhino_data.py   Yahoo Finance fact sheet for one ticker (needs `pip install yfinance`)
```

## Install

```bash
git clone https://github.com/Mol2017/rhino-finance.git
ln -s "$PWD/rhino-finance/skills/rhino-stock-analysis" ~/.claude/skills/rhino-stock-analysis
```

Then ask Claude Code something like "用 Rhino 的方法分析 TSM".

A personal study tool. Not investment advice.
