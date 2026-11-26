# What actually helps a trading decision: first evidence (2026-11-22)

Full tables: [results/rules_2026-11-22.md](results/rules_2026-11-22.md). Code: [rules.py](rules.py) (rule definitions), [backtest.py](backtest.py).

## Setup
- 507 stocks: today's S&P 500 plus TSM, ASML and a few others he covers. Signals from 2008-10 to 2026-10, the last date with a full 20-day outcome.
- Liquid names only: price ≥ $5 and ≥ $20M daily volume.
- Entry at the close of the signal day.
- Measures:
  - **excess vs SPY** after 5 / 20 / 60 days;
  - **1:1 win rate**: within 20 days, does a target hit before a stop of the same size? Two stops are tested: 2×ATR, and just under the signal day's low.
- **Bias warning:** the list is today's members, so stocks that later failed are missing. That flatters every long signal, dip-buying most of all. Compare rules with each other and with the baseline, not with zero.

## Results

### 1. The buy points, done mechanically, don't reach his ~65% win rate

| | 1:1 win rate (signal-day-low stop) | excess vs SPY, 20 days |
|---|---|---|
| Any stock, any day | 48% | +0.27% |
| Best buy point (BP6, volume-confirmed engulfing) | 54% | +0.54% |
| Other buy points (BP1, 5, 7, 8, 9) | 46–52% | about the same as any day |

- **2020–2026:** almost every buy point is at or below baseline.
- **His extra conditions add little.** BP6 with volume and trend conditions is only ~0.25% better than a plain engulfing candle. A hammer without his conditions does about as well as BP7 with them.
- **So the edge isn't the candle pattern.** If he really wins ~65%, it must come from what the code can't see: which support zone, whether price is inside his valuation range, and the market regime. That is exactly what the ledger is meant to test.

### 2. Some no-buy rules help, one works backwards

Each rule is judged within its own context. Downside rules are compared on dip days (≥8% below the 20-day high). Upside rules are compared on days that close at a 20-day high.

| Rule | Excess return of flagged days vs others: 20 d / 60 d | Same direction in all 3 periods? | Verdict |
|---|---|---|---|
| NB3 just broke the Fibonacci 61.8% level of the recent up-swing | −0.5% / −1.1% | yes | **keep: strongest rule** |
| NB11 new high on below-average volume | −0.2% / −0.25% | yes | keep, small effect |
| NB1 close at a 20-day closing low | −0.2% / −0.6% | 60-day yes; 20-day only in 2020-26 | keep, mostly a 60-day effect |
| NB4 bounce on shrinking volume | ≈ 0 | — | no measurable effect |
| NB15 / NB16 RSI6 > 90, or bearish divergence | slightly worse at 5 d, ≈ 0 after | mixed | short-term only |
| NB12 jump of ≥10% in 3 days to a new high | −0.14% at 5 d, **+2.8%** at 60 d | no | only a short-term rule; momentum wins on longer horizons |
| NB6 worst 10% of its sector that day | **+0.3% / +0.9%** | yes, all periods | **backwards for returns**: sector losers rebound more. It does cut the up-rate by ~2 points, so it avoids volatility, not loss |

### 3. What the evidence implies for the model
- The no-buy rules that hold up are about **structure breaking**: NB3 (61.8% break), NB1 (new low), NB11 (weak breakout). His rule that you buy only after the structure is confirmed has support in the data.
- The single-candle triggers carry little edge by themselves. They are timing details, not the source of returns.
- The parts not yet tested are where any real edge would be:
  - support-zone strength (NB2, NB13, NB14);
  - the valuation band;
  - the market regime;
  - sizing.

  They need his own numbers, which come from the weekly tables and the decision ledger.

## Decision ledger: first score (2026-11-24, Jan–Aug 2024)

Full tables: [results/ledger_2026-11-24.md](results/ledger_2026-11-24.md). He repeats the same view day after day, so each table counts one row per episode (same ticker and same call within 30 days). The 90% intervals resample whole tickers.

| His view | Episodes (tickers) | Excess vs SPY, 60 days | 90% CI |
|---|---|---|---|
| bull | 47 (23) | +6.4% | +1.6 to +11.4 |
| neutral | 173 (91) | −4.0% | −6.3 to −1.9 |
| bear | 40 (32) | −7.2% | −12.8 to −1.2 |
| action "avoid" | 59 (45) | −6.9% | −11.0 to −2.6 |

- **Stock selection is the edge that holds up.** Bull minus bear is +13.7 points at 60 days (CI +6 to +21). The avoid effect is gone by 120 days.
- **"hold" adds nothing** (≈0). "wait" (wants to buy, conditions not met) lags by 2.5%, so not buying yet was mostly right.
- **His invalidation levels work:** 60% are crossed within 60 days, and the stock then lags SPY by 1.6% over the next 20 days.
- **Waiting for his buy zones** (179 distinct plans; the comparison is over the same window, and unfilled plans count as missed):
  - Only 58% fill within 60 days. The median fill is 2.5% below the reference price.
  - Cash held while waiting earns nothing: waiting loses 1.2 points at 60 days and 4.3 at 120 days vs buying right away.
  - Cash parked in SPY while waiting: waiting gains 1.8 points at 60 days (CI +0.3 to +3.7).
  - So the zones help only if the money stays invested while you wait. Plans that need a reversal pattern did best (+4.8 points); "other" conditions did worst (−3.9).
- **Caveats:** this is one regime (the 2024 AI rally), and the add/buy/trim counts are too small to read.

## Decision ledger pilot
- **Spec:** [LEDGER_SPEC.md](LEDGER_SPEC.md). **Scorer:** [score_ledger.py](score_ledger.py).
- **Pilot:** 3 daily videos from Nov 2026 gave 22 stock calls and 9 market calls. The numbers come from his holdings cards: cost, weight, zones, tranche sizes and confirmation conditions.
- **Model test:** the stronger and the cheaper model extracted the same video with matching numbers; only judgement fields differed. Spec v2 tightens those fields.
- **Scorer:** runs end to end, but Nov 2026 calls have no outcomes yet. The ingest now runs oldest-first from 2024, so the calls it scores will have 20–120 days of history.
