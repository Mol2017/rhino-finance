# How Rhino picks where and when to buy (part 2 of the model, draft 2026-11-25)

Source: 38 member teaching episodes on support/resistance, bottoming candles, entry style and indicators. Each was turned into a clean transcript (`data/clean/<id>.md`) and an extract (`data/extract/<id>.json`). Episode numbers in brackets, e.g. [283]. Part 1 (valuation) is in [valuation-method.md](valuation-method.md).

| Group | Episodes (year) |
|---|---|
| Support and resistance | 10 volume, 11 chips, 12 Fibonacci (2020) · 113 Fib extension (2022) · 161 liquidity (2023) · 213 volume zones, 222 dense zones, 224 valid highs/lows (2024) · 270 rolling VWAP, 282 option collar (2025–26) · 283 strength rating (2026) |
| Bottoming candles and patterns | 15 gaps, 16 hammer, 17 inverted hammer, 18 W bottom, 24 engulfing, 28 harami, 45 relay vs bottom, 47 inverse H&S, 49 morning star (2020–21) · 124 validity ranking (2022) · 150 flag, 151 cup and handle (2023) |
| Entry style | 26, 27 valuation + chart (2021) · 37 right side, 39 left side (2021) · 223 chasing new highs (2024) · 272 open/close (2026) · 292 left-side tranches (2026) · 301 18 no-buy rules, 302 9 buy points (2026) |
| Indicators | 22 MA, 23 timeframes (2020) · 30 RSI, 31 MACD (2021) · 52 Bollinger (2021) · 127 DeMark 9/13 (2023) |

## 1. The idea in one paragraph

Support and resistance don't predict; they move the odds from 50:50 to 60:40 or 70:30, and they work because institutions' algorithms use the same levels [283]. He first maps **points** (Fibonacci levels, necklines, trendlines), then **zones** (long sideways ranges with heavy volume), and rates each zone 小/中/强/超强. The buy happens only when three things line up: price is inside the value range from part 1, price sits on a **strong** zone, and a **bottoming candle** confirms there on a **close**. Before that, 18 veto rules can each kill the trade. Indicators are filters and vetoes, never triggers on their own. Every break and every confirmation is judged on the close (or the opening auction), never intraday.

## 2. The steps

### Step 1 · Can the chart be trusted at all?
- **Liquidity floor.** Average daily dollar volume under ~$20M is borderline; under ~$10M he deletes the stock without studying it [213, 224]. A $1B company trading $3M a day can be pushed around by $500k, so no pattern there means anything [161, 27].
- **Size.** Market cap $20B+ normally, $10B hard floor, never under $5B, no OTC [301, 302]. (2021 was looser: $1B+ [39].)
- **Efficient market only.** Small caps, news-driven names and "demon stocks" (妖股) break the rules; Chinese ADRs often do too [22, 213].

### Step 2 · Pick the timeframe
- Daily is the minimum for US stocks. Weekly shows the big zones and trend; daily sets the prices and the entry [23, 283].
- 1h/30m only show the fight at a level (how a breakout happens, gap timing against news). Below 30m is noise [23].
- **Trade the timeframe you watch** (看什么周期做什么周期). A 30m break only counts once it changes the daily chart. The bigger timeframe always wins and caps the smaller one [23].
- Strip off moving averages and read bare candles (裸K) when mapping levels [12, 213, 222].

### Step 3 · Map the points (structure first)
- **Decide the structure:** up, down or range. Fibonacci only applies in a trend, not in a box [12].
- **Draw Fibonacci on the latest swing** (high and low). If structures nest, move up to weekly or monthly. If levels come out too dense ("everything is support"), switch to a bigger structure, preferably one that already tested its 61.8% [12, 113].
- **Levels that matter:** 38.2% and 61.8% day to day; 50% sometimes; 23.6% ignored [12, 113]. Depth tells force: 38.2 light, 50 medium, 61.8 the limit.
- **61.8% decides the trend, on a close** [12, 283]:
  - Close below 61.8% = 破位: the up-structure is over, rallies are for selling, the next look is the 100% (prior low). If that breaks too, redraw on the next larger structure. "Can see" a level is not "must reach" it.
  - An intraday break recovered the same or next day is only 刺破; the level still holds.
  - In a down-structure, a rally that stops at 38.2/50/61.8 is just a 反弹. A close above 61.8% = 反转, target the prior high. After a break he draws the broken leg inverted and uses its 61.8% as the reversal-confirmation level [283, 113].
- **Other points:** trendlines, channel edges, flag/cup lines, necklines (H&S, W, M), prior swing highs and lows, round numbers [283, 113].
- **Targets (Fib extension):** only while the structure is intact. Anchors: trend low A, high B, pullback low C; every extension level is resistance, 50–61.8% decides whether price can get back to the prior high [113].

### Step 4 · Map the zones
In order of use:
1. **Dense trading zone (密集交易区)** [222]. Nearest first. Frame it with wicks that tested the level 2–3+ times; inside, the densest run of bodies is the core. Lookback: under a year works best, two years usable, three or more unreliable. A thin or empty band under a zone makes its lower edge critical: nobody holds cost below it, so price falls fast.
2. **Volume-candle zone (增量K线)** [213, 222]. Recent big-volume candles with long bodies and short wicks (no stars, hammers or shooting stars). Mark top, middle and bottom of the body; the middle is the bull/bear line. A green one below price is support; a red one above is resistance. This is the fallback for steep moves that left no sideways base.
3. **Valid highs/lows (有效高低点)** [224]. Short-term, daily, last 1–6 months. Wick extremes, **at least 3 touches within 1%** (two don't count). A break is >1% beyond the wicks or a gap open below. A hold that gets bought back up is a buy point.
4. **Secondary, never alone:**
   - Chip distribution: direction only, ignore the broker's printed S/R numbers [11].
   - 5-day rolling VWAP (hlc3): institutional cost and trend state; a fresh break on volume = institutions selling; first reclaim with the line turning up = possible reversal [270].
   - Quarter-end SPX option collar (index only): long put ~5% OTM = support, short call 3–5% OTM = ceiling; matters only in moves >5% [282].

### Step 5 · Rate each zone 小 / 中 / 强 / 超强
**The seven principles [283]:**
1. Points beat zones. When a point sits inside a zone, the half of the zone on the point's side is stronger.
2. A longer structure's point beats a shorter one's.
3. A zone traded longer beats one traded shorter.
4. At similar duration, more volume beats less.
5. **Time beats a short volume burst**: a 3-month box beats a 3-day spike.
6. Strength is fuzzy; don't quantify it.
7. Strength is relative and changes with tests; compare a stock only with itself.

**Extra rules:**
- **Confluence is the strongest:** Fib + channel bottom + range bottom = "very, very strong" [283]; a dense-zone edge crossing a rising trendline = the key level and a potential excellent buy [222].
- **Repeated tests with volume strengthen** a level (小/中 → 强). He never says tests weaken one [283, 224].
- **Weak by construction:** fast rallies with no base, areas crossed on low volume (空虚地带), short low-volume tops, shrinking-volume platforms [283, 161, 222].
- **How deep a pullback goes into a volume candle:** holds at the top edge = very strong; at the middle = strong; through the bottom = role flips [213].
- **Role reversal everywhere:** broken support becomes resistance. Resistance flips to support only on a **close above the upper edge** [222, 272].
- **Structure fully destroyed** (all Fib levels lost, new lows): no points left, rate zones by time, then volume [283].
- Only 强 vs 中 really matters; 小 is noise. 超强 appears only as a label on multi-year long-term zones and is never defined [283, 213].
- Write the lower edge a little wider than the line (315 not 320) [283].

### Step 6 · Volume decides whether a move is real
- **Purely relative, judged by eye:** this bar vs the previous bar, or vs the recent average. No multiple, no fixed MA length [10, 213]. (Ep 301's "volume 5-day average turning down" is the only MA mention.)
- 增量 breakout = valid; 缩量 breakout = wait, possible trap. 增量 breakdown = the trend has turned; 缩量 breakdown = wait, possible bear trap [10].
- **缩量 rises and falls are "耍流氓"** (not to be trusted); the range they cross has no support or resistance [161]. "A breakdown on volume is the most real decline" [161].
- A pattern formed on 缩量 is pending, not invalid; it becomes valid if volume arrives [10].

### Step 7 · Veto: the 18 do-not-buy rules (unchanged, see 04)
Single-condition veto; any one blocks the buy [301]. Refinements from this batch:
- NB4 "缩量 rebound" matches ep 45's relay signal: a stop day on volume followed by a shrinking-volume rally that fails at structure.
- NB15–16 (RSI): 2026 is looser than 2021. In 2021 RSI6 >80 alone meant don't chase [30]; in 2026 >90 is an absolute veto and >80 vetoes only with a top divergence [301].
- Add from other episodes: a gap down through a long platform, even inside the value range, means "information we can't see", wait for the next tier [27]; earnings close, EPS expected down quarter on quarter, and price gapping through support (ITW) [26]; daily dollar volume of a few hundred thousand [27].

### Step 8 · The bottoming signal (止跌)
**Hard gate: a clear downtrend** (lower lows; a bounce that fails the prior high still counts). A candle in a sideways box is ignored; only the engulfing may sit in a post-decline range [16, 17, 24, 28, 49]. Support raises the grade but no episode makes it a gate; his 2026 long-term rule does require strong support [302].

**Ranking of bottoming candles [124]:** hammer > bullish engulfing > morning star > inverted hammer > bullish harami. Topping: shooting star > hanging man > bearish engulfing > evening star > bearish harami. Typical forms justify more size; weak forms wait ~2 days for a better signal.

| Candle | Must have | Grade / volume | Invalid when |
|---|---|---|---|
| Hammer [16, 124] | Lower shadow ≥2× body, little or no upper shadow, in a downtrend | Best: body bottom below the prior body bottom, body top inside the prior body. Gapped hammer through key structure = only a gap-fill bounce. Open and close both above the prior body = not a hammer. Needs 放量 (2026: prior day 缩量 to a recent low, hammer day 放量 [302]) | Shadow low breaks |
| Bullish engulfing [24, 124] | Bullish body closes above the prior candle's high | Deeper gap-down open is better. 2026: prior day 缩量, engulfing day 放量 with a big body [302] | Its low breaks |
| Morning star [49, 124] | Bear, star/doji, bull | C clears A's body top and upper shadow (2022; 2021 was "close above A's open"). C volume ≥⅔ of max(A, B); <½ invalid | Close below the low of the three |
| Inverted hammer [17, 124] | Upper shadow ≥2× body, clearly above-average volume | An early warning; inverted hammer followed by a hammer is much stronger. Buy only after a close above its body within 5 days | Close below its body |
| Harami [28, 124] | Small body (and shadows, 2022) inside the prior body | No volume needed (selling dried up). Ranked last | Prior low breaks |

**Multi-candle patterns:**
- **W bottom [18]:** prior downtrend; first rally ≥10%; lows ≥half a month apart; second low equal or higher (if lower, ≤3%, at most 5%); volume at the second low ≥ the first; **放量 neckline break**. Target = neckline + (neckline − low). Buy the break (stop 3% under the neckline) or the 缩量 retest in 3–5 days. Skip if the gap-up leaves less upside than downside.
- **Inverse H&S [47]:** ≥20 days to a month; rallies after the head and right shoulder on more volume; 放量 neckline break, >3% beyond = true; back under by 3% = false, stop out. Target = head-to-neckline distance added at the break.
- **Bull flag [150]:** steep pole on volume; flag volume below pole volume; flag low above Fib 61.8% of the pole. Buy near the lower line after a 止跌 candle (left side) or on the 放量 break of the upper line (right side). Target: the pole top, at most one pole length.
- **Cup and handle [151]:** U-shaped base (≥5 bars, not a V), cup low ≤61.8% retrace, rim within 3% of the old high, handle ≤61.8% of the cup. Buy the 放量 break of the handle line, or the rim; stop under the handle low. Target = rim + cup depth, in points.
- **Gaps [15]:** must be 放量; only breakaway gaps over a key level are traded; filled within 3–5 days = no trend; every gap zone is support/resistance; only the untraded part of an old gap acts as support [27].

**Relay or bottom (下跌中继 vs 相对底部) [45]:** default to relay; a bottom is only known afterwards.
- Relay signs: big-volume stop day, then a shrinking-volume rally that fails at structure; the range low breaks; the index is in a bear market or bouncing on low volume (then every stock bounce is a relay); weak forward fundamentals with a small-news pop; a bounce that reaches only Fib 23.6%.
- Bottom signs: >1 month of 缩量 sideways above the low; huge volume at the low with little price change (shakeout); 2nd–4th tests met by strong buying; a structure break (61.8%, neckline, downtrend line on volume) that holds a prior high; improving fundamentals.
- Priority: structure first, then time, then the index. A hammer is a stop, not a reversal; a reversal needs a close back above 61.8% [16].

### Step 9 · Left side or right side
- **Left side (左侧, buy as it falls)** is his default for long-term money [223]. It needs a quality growth stock, price in or below the forward value range, and no industry downturn [39, 292]. The 2026 version is "a 止跌 candle on strong support inside the value range" [302].
- **Right side (右侧, buy after a structure breaks)**: range top, downtrend line, neckline. Needs a visible stop underneath and a written plan; otherwise it is chasing [37].
- **Valuation is the switch** [292]: inside or below the range → build the long-term position left side. Back into overvaluation → no long-term adds; only a small right-side swing position.
- A small structure breaking up while still in the value range (mini W, small downtrend line) → a right-side add of 10–20% of the stock's allocation [292].

**Left-side tranches [292, 2026]:**
- 2–4 tranches, usually 3. Default split 2-3-5 or 3-3-4 (tenths of the planned position). Two tranches only when confident, on two consecutive strong supports. Volatile or cyclical stocks at a wide major support that is also the valuation floor: reverse to 4-3-3 or 5-3-2.
- Tranches sit on strong supports inside the forward value range; spacing comes from where the supports are, not from a fixed %. Supports too close together: keep the first tranche light.
- **Buy more as certainty rises, not as price falls.** The last tranche is ballast (压舱石): if the 止跌 candle ranks low, wait, even until it turns right side.
- Stop scaling on a valuation cut or a value trap (check every quarter).
- **If it rebounds before you're filled:** 30–50% filled is fine, 60–70% is great. Small trend improving, big structure unbroken, still in range → add a little from reserve (10–20% of it). Back to overvaluation → no long-term adds. Overvalued for a long time → once the market prices next fiscal year, raise buy points to that year's range.
- **While waiting:** sell puts at the lower planned entry only with cash to take the shares; park cash in T-bills/money funds, not dividend stocks [292].

**2021 version (mechanical, not repeated later) [39]:** total left-side exposure ≤50% of capital; tranches 2-3-5 spaced ≥15% apart; cut the first tranche if the account is down 25%. Swing left side uses only the strongest supports, 1–2 entries ≥5–10% apart, stop when the first support breaks, no averaging down.

**Breakouts and chasing:**
- A breakout counts only on a **close above the upper edge** of the zone. A close inside the zone is not a breakout [272]. It must be 放量; 缩量 new highs are vetoed [301, 302].
- Where to buy, in order: (1) the 缩量 retest of the broken zone, with a 止跌 candle or the first volume-up candle, near the close; (2) on a trendline retest, any shrinking-volume down day that doesn't close back below the line; (3) a neckline retest that holds [302]. If it won't retest, scale in so the average sits near the breakout [272].
- **Chasing new highs (追高)** is allowed as labelled speculation, without valuation, only if: temporary mispricing, little trapped supply above, and someone later to push it (shorts covering, later buyers). Exit plan before entry (fixed target, trailing stop, or topping pattern). He rarely does it himself [223].

### Step 10 · Timing and confirmation
- **Close or opening auction only.** Both clear the most shares, so they show institutions' intent [272]. Pre-market, after-hours and overnight prices never count [272, 301].
- With 2–5 minutes left and price far beyond the level, you may treat it as closed [272]. Patterns can be bought in the last 5–60 minutes once the close is near-certain [24, 28, 49].
- **Support is a zone; don't buy the first touch** of its top. Wait for the 止跌 candle that shows where institutions step in [272].
- **A break is not repaired by a bounce back above the lower edge**; repair needs a close above the upper edge [272].
- **No orders in the first 30 minutes**, even on an opening breakout; an opening break of a key level is a valid signal, but the entry comes after [301]. A gap up through resistance: buy the intraday retest of the old resistance [272]. A gap down through support: sell into the bounce [272].
- Overnight news against the close: judge by the next opening auction, confirm with that day's close; the open often prints ~3% below the after-hours price [272].
- Missed the signal day: never chase the bounce [45].

### Step 11 · Stop and reward:risk at entry
- Stop: zone's lower edge; hammer's shadow low; W bottom just under the neckline; trendline = close back below; Fib setup = close below 61.8% [26, 37, 301, 302]. No technical level (chasing): fixed 3–5%, trailed to breakeven once in profit [223].
- **Reward:risk ≥1:1** for any trade, ≥2:1 for heavy size; about 65% win rate at 1:1; no setup wins 80–90% [37, 302]. Three 3% stops beat one 10% stop [223].
- Right-side trade: max loss 5% of total capital; add to a winner only after +10%, each add no bigger than the existing position, each with its own stop [37].
- Technical (pattern) trades: at most 10–20% of the portfolio, 3–5% stop, no averaging down while the pattern holds, never leveraged [28, 49].
- Abandon the plan if R:R <1:1, the next resistance is too close, or the stop is too wide (wait for a deeper pullback or move on; a pre-set tranche plan relaxes this) [26, 301].

## 3. Indicators: what each one is for

Rule for all: indicators are assisting tools (辅助指标); never decide on one; price patterns outrank them; no indicator justifies a heavy bottom-fish or short; read on the close [22, 30, 31, 52].

| Indicator | Settings | Rule | Role |
|---|---|---|---|
| **RSI** [30, 301] | 6 and 24 (2021: 6/12/24), daily | RSI6 >80 overbought = don't chase, not a short. **RSI6 <20 oversold** = don't dump, not a buy. Divergence = price makes a new closing high/low, RSI6 doesn't, within one segment where RSI6 hasn't crossed RSI24. Repaired when RSI6 crosses RSI24 or makes its own new extreme | **Core veto** (NB15–16) and part of buy point 9 |
| **Moving averages** [22] | 5/10 short, 20/30/60 medium, 120/200/250 long | 200-day = bull/bear line. 20/30/60 aligned up = trend. 5-crossing-20 is his best cross; 5/10 crosses whipsaw. A daily close below = broken; wait 1–2 days on 200-day breaks | Trend filter; level reference once holding |
| **MACD** [31] | 12/26/9, daily and above | Zero axis first: both lines above = attack mindset; below = defence, every stop is only a rebound. Death cross = don't buy; death cross near zero is strongest. Histogram only a reference | Regime filter |
| **Bollinger** [52] | 20, 2 | Middle band = MA20. Bands are never buy/sell points. Bullish only: after a decline, narrowing on low volume, then opening with a 放量 break of the middle band | Confirmation |
| **DeMark 9/13** [127] | 30m–weekly | Act on the 9, don't wait for 13; never enter on the 9 bar itself, wait for a 止跌/滞涨 candle | End-of-trend warning |
| **KDJ** [52] | not given | K/D cross confirms Bollinger opening/narrowing | Confirmation |

- **The buy-point-9 slide ("超卖（RSI 大于 80）") is his slip.** He says it aloud in ep 302, but his own definition [30, 127] is RSI6 <20. Buy point 9 = pullback holds Fib 61.8% on a close + RSI6 <20 + price/RSI6 bottom divergence + a 止跌 candle.
- **Confluence count:** act when most tools agree, about 7–8 of 10; 5:5 or 6:4 means wait [16, 18, 213].
- 5/10-day MA in buy point 5 [302] uses the MA only as a level inside a structural setup (first down-close after a run), consistent with ep 22's "single MA only as a reference".

## 4. Valuation and chart together

- **Valuation decides whether; the chart decides when** [26, 27, 302]. Short-term trades use the chart alone; long-term trades add the value-range condition [302].
- **Cheap but the chart is broken** (gap through support, broken neckline, boxed in): don't buy here, wait for a lower tier. A bad chart inside the value range is itself evidence the valuation may get cut [27].
- **Good chart but expensive:** no long-term adds; only a small swing position [292]. Pure chasing is a separate, labelled speculation [223].
- Strong support below the value range is better than one inside it [26].

## 5. How the method changed over time

| Area | 2020–21 | 2022–24 | 2025–26 |
|---|---|---|---|
| Zones | Broker chip charts, volume quadrants, Fib 38.2/50/61.8 [10–12] | Fib 38.2/61.8 only [113]; zones read straight from candles; "algorithm footprints" [213, 222, 224] | Points > zones, seven principles [283]; institutional cost (VWAP), option collar [270, 282] |
| Candles | Textbook definitions, each pattern its own episode [16–49] | One validity ranking with grades [124] | Only engulfing and hammer survive as standalone buy points, both with a volume pattern [302] |
| Win rate claims | 70–80% "already good"; 8 of 10 indicators = 80% [16, 47] | — | 60–70%, "no 80–90% buy point exists" [302] |
| Left side | Mechanical: 2-3-5 at ≥15% gaps, 50% cap, 25% account stop [39] | — | Support-based tranches, "buy as certainty rises" [292] |
| Left/right labels | A 止跌 candle at support = stage right side [37] | — | A 止跌 candle at support = the left-side entry; right side = a structure break [292, 302] |
| RSI | 6/12/24; >80 alone = don't chase [30] | — | 6 and 24; >90 veto, >80 only with divergence [301] |
| Size floor | $1B [39] | $10–20M daily dollar volume [213, 224] | $10B floor, $20B normal [301, 302] |

Constant throughout: closes decide breaks, broken support becomes resistance, 缩量 moves are unreliable, no single indicator decides.

## 6. Still open
1. What separates 超强 from 强 (only ever a label on long-term zones)?
2. No numeric 放量 threshold anywhere; how much "放量" is enough for the hammer and the breakout?
3. Is a stop triggered by an intraday break or a close? Patterns say "跌破"; the morning star says close; the flag allows a 1–2% buffer and one day's wait.
4. Rule 04 #1 (no buy on a recent-low close) vs the best-grade hammer whose body bottom is below the prior body: does a green hammer pass and a red one fail?
5. Inverted hammer: same-day buy [45] or wait for a close above the body within 5 days [17]?
6. Are the 2021 left-side limits (50% cap, 25% account stop) still in force?
7. How does a trade get classified in advance as swing-left (stop when support breaks) vs long-hold left (keep adding)?
8. Does the 200-day MA or the MACD regime gate the 2026 buy points? Neither appears in 03/04.
9. How often each tool actually appears in his daily calls is not yet measured; the ledger (2024) could answer it.
