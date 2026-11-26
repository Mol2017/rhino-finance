# How Rhino makes a decision (draft, 2026-11-24)

Sources so far:
- **What he teaches:** the 7 reference notes in `rhino/skill/rhino-stock-analysis/references/`. Valuation comes from 17 teaching episodes ([valuation-method.md](valuation-method.md)); support, bottoming candles, entry style and indicators from 38 ([support-entry-method.md](support-entry-method.md)). The remaining teaching videos have only been read by title ([video-topic-map.md](video-topic-map.md)).
- **What he does:** 743 stock calls and 249 index calls from daily videos, Jan–Sep 2024 (`data/ledger/`).

Marked **[taught]** = he says it in a teaching video; **[seen]** = visible in what he does in the dailies; **[title only]** = we only know the topic exists.

## 1. The whole thing in one paragraph

He is a **valuation-anchored zone buyer who mostly waits**. Valuation decides *whether* a stock is worth owning and roughly *what price* is cheap. Chart structure decides *where* to buy (support zones rated by strength). A list of veto rules decides *when not to*. A confirmation candle or a close decides *when exactly*. Money goes in small tranches (2/4/6% of the portfolio) at pre-planned zones, and a pre-stated price level decides when the idea is wrong. On most days for most stocks the answer is "hold" or "wait for price X".

## 2. The decision flow

Each step can stop the process. Steps run in this order in his daily videos.

**Step 0 · Who is asking and on what horizon** (topics 1, 8)
- Long-term, swing or day trade decides which chart he reads (daily is the minimum; weekly for big structure) and how far away the defence level sits. [taught]
- Advice depends on your position: heavy, light, or none. Someone with a big position at a high price gets "trim into the resistance"; someone with no position gets "wait for the zone". [seen]

**Step 1 · Market gate: is this a market to act in?** (topics 3, 4, 6)
- Labels the index structure: up / range / rebound / down / bear. The line between "up" and "rebound" is the **Fibonacci 61.8% retracement of the last up-leg, on a close**. Lose it and every bounce is "just a rebound" until proven otherwise. [taught + seen]
- Reads breadth (how many stocks are rising, which sectors), VIX, then flows: CTA positioning, option gamma, hedge-fund exposure. [seen; flows taught in topic 4, title only]
- Writes **if/then scenarios** for QQQ, SPY, SOXX: "hold zone A → target B; close below A → rebound mindset, trim into strength; below C → bear, hold cash". [seen]
- In 2024 his market stance was "neutral" about three-quarters of the time. "Risk-on" came almost only when the structure was "up"; "defensive" was most common when it was "down". [seen]

**Step 2 · Is the stock worth owning at all?** (topics 2, 11)
- Forward value range = his PE band × consensus EPS for this and next fiscal year. Below the band = under, inside = fair, above = over. [taught]
- Filters out: EPS falling next year ("recession type"), weak businesses even when cheap, things he can't value (commodities, biotech), small caps under $5–10B. [taught]
- Checks EPS revisions trend and, sometimes, ERP vs the 10-year yield. [taught]
- PE band: the stock's 2018–19 PE low/high on adjusted earnings; the median PE × this year's EPS is the fair price at year-end. He overrides it for recovering earnings (use next year), matured growth stocks (a growth-matched "normal PE") and paper-cheap stocks. Details: [valuation-method.md](valuation-method.md). [taught]

**Step 3 · Where would he buy? Map the zones.** (topics 6, 7)
- Only liquid stocks: daily dollar volume under ~$10M is deleted unread. [taught]
- First "points": Fibonacci 38.2/61.8 on the latest swing (a close below 61.8% ends the up-structure), trendlines, necklines, prior highs/lows. Then "zones": dense trading zones framed by 2–3+ wick tests, big-volume candle bodies, 3-touch wick lines within 1%. [taught]
- Rates each zone 小 / 中 / 强 / 超强 with 7 principles: points beat zones, longer time beats shorter, more volume beats less, time beats a short volume burst, confluence = strongest. Volume is always relative and judged by eye; moves on shrinking volume are "耍流氓". Details: [support-entry-method.md](support-entry-method.md). [taught]
- Tags each zone with its use: 止跌长线 (long-term buy), 突破右侧 (breakout re-entry), 减仓 (trim). His holdings cards list 4–8 zones per stock. [seen]

**Step 4 · Veto: the 18 "do not buy" rules.** (topic 7)
- Any single one blocks a buy; no weighing. [taught]
- The ones he actually cites most: closing at a new recent low (NB1), just broke a strong support (NB2), price floating far above support after a jump (NB12), news-driven move (NB17), weak-volume bounce (NB4). [seen]
- In the backtest, NB3 (61.8% just broke) and NB1 hold up; the sector-laggard rule NB6 does not. [tested]

**Step 5 · Trigger: what makes today the day.** (topics 5, 6, 7)
- Long-term (left side, his default): price inside the fair value range **and** on a strong zone **and** a bottoming candle there, in a clear downtrend. Candles ranked hammer > engulfing > morning star > inverted hammer > harami; the 2026 buy points keep only the engulfing and the hammer, each with "prior day 缩量, signal day 放量". [taught]
- Valuation is the switch between left and right side: in range → left-side tranches; back to overvalued → no long-term adds, only a small right-side swing. [taught]
- Indicators only filter and veto (RSI6 >90; >80 with top divergence). None is a trigger alone. [taught]
- Swing: one of the 9 buy points (breakout-and-retest, engulfing on volume, hammer at a new low…), with reward ≥ risk to the next resistance. [taught]
- Confirmation is a **close or open**, never intraday; no orders in the first 30 minutes. [taught]
- In practice most of his written plans are plain limit zones ("add 4% at 85–87"); explicit "wait for a reversal candle" appears in ~5% of plans, mostly during sell-offs. [seen; may be partly the extractor]

**Step 6 · Size and spread.** (topic 8)
- Tranches of 2%, 4% or 6% of the portfolio per zone; the top zone first, lower zones held in reserve. One buy per zone. [seen + taught]
- Taught split: 2–4 tranches, usually 2-3-5 or 3-3-4 tenths, placed on strong supports inside the value range; "buy more as certainty rises, not as price falls"; 30–50% filled before a rebound is fine. [taught]
- Must be able to sit through another 30–40% drop; stop goes under the zone; similar stocks share one exposure cap. [taught]

**Step 7 · Defence and exits.** (topics 7, 8, 12)
- Every core holding has a stated level: "close below X → trim half / back to range / turn bearish". Exits are almost always a **close below** a level. [seen]
- Technical trims are not bearish views; he buys back lower or above the breakout. [taught + seen]
- Sells outright only when the business thesis breaks ("摔杯"). [taught]

## 3. What his behaviour shows (743 stock calls, 2024)

| What he said to do | Share |
|---|---|
| wait (wants it, conditions not met) | 52% |
| hold | 33% |
| avoid | 12% |
| buy / add / trim / sell | 3% |

- **Valuation sets the candidate list, not the timing.** Stocks he labelled "under" still got "wait" or "hold" 83% of the time. "Over" stocks were also mostly "wait" or "hold" (76%); the difference is that "avoid" was twice as common (21% vs 14%).
- **Stance and action are separate.** "bull" stocks were mostly "hold" or "wait"; "avoid" almost always came with "bear" or "neutral".
- **No-buy rules are cited ~6× more than buy points (69 vs 12 citations).** His process is mostly about not acting.

## 4. The 13 teaching topics: where each one sits

| # | Topic | Videos | Role in the decision | What we know |
|---|---|---|---|---|
| 1 | Approach & trading style | 13 | Step 0: horizon and style | title only (15 long-term rules, 12 facts) |
| 2 | Fundamentals & valuation | 44 | Step 2: worth owning? | method known; PE band choice missing |
| 3 | Macro, rates, cycles | 25 | Step 1 background | title only |
| 4 | Institutional behaviour & flows | 26 | Step 1 flows; open/close confirmation | seen in dailies; title only |
| 5 | Candlestick patterns | 26 | Step 5 trigger | **ranking and grades known** (12 eps) |
| 6 | Indicators | 36 | Steps 1, 3, 4, 5: Fib, volume, RSI(6,24) | core ones known (Fib, volume, RSI, MA, MACD, Boll, DeMark); exotic ones title only |
| 7 | Support/resistance & entry points | 29 | Steps 3–5: the core | **well covered** (17 eps) |
| 8 | Position sizing & risk | 30 | Steps 0, 6, 7 | partly |
| 9 | Options, ETFs, tools | 20 | Outside the core: income while waiting, hedges | title only |
| 10 | Long-term allocation | 11 | A separate path: index strategies, DCA | title only |
| 11 | Sector & theme research | 51 | Step 2 universe; sector context | title only |
| 12 | Psychology | 16 | Step 7 discipline | partly |
| 13 | Data sources | 10 | Data layer for the skill | title only |

## 5. Open questions the teaching videos should answer
1. ~~How he chooses the PE band per stock~~: answered in [valuation-method.md](valuation-method.md). Still open: the exact rule for moving a band.
2. The 15 long-term rules and 12 facts (ep 211, public 投资定位): does horizon change the flow above?
3. How he decides tranche size (2 vs 4 vs 6%) and total position per stock.
4. ~~When valuation and chart disagree, which wins?~~ Valuation decides whether, the chart decides when. Cheap but broken: wait for a lower tier (a broken chart in the value range may mean the value gets cut). Expensive but breaking out: no long-term adds, only a small swing ([support-entry-method.md](support-entry-method.md) §4).
5. ~~Which indicators he actually uses~~: RSI(6,24) as a veto is core; 200-day MA and MACD zero axis are context; Bollinger, KDJ, DeMark 9 are confirmation only ([support-entry-method.md](support-entry-method.md) §3). Still open: how often each appears in his daily calls.
6. Where options fit: partly answered. While waiting on a left-side plan he sells puts at the lower planned entry, only with cash to take the shares [292]. The rest of the options lessons are not processed.
7. Is a stop triggered by an intraday break or a close? Patterns say "break"; the morning star says close.
8. Are the 2021 left-side limits (50% cap, 25% account stop) still in force, and how is a trade classified in advance as swing-left (stop when support breaks) vs long-hold left (keep adding)?
