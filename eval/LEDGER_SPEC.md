# Decision ledger: spec (ledger-2)

One file per daily video: `data/ledger/<video_id>.json`. It records **what Rhino decided or planned that day**, in a form a script can check against later prices. It is not a summary: anything without a ticker, a price or a stated action stays out.

Inputs to read: `data/raw/<id>/metadata.json` (title, upload_date), `transcript.json` (segments with start time `t`), `frames.json` (OCR of on-screen charts and his orange holdings cards). The cards usually carry the exact numbers (cost, weight, zones, add plan); the speech carries the reasoning and the conditions. Where they disagree, trust the card for numbers and the speech for intent, and say so in `note`.

## File shape

```json
{
  "video_id": "…", "upload_date": "2026-11-21", "market_date": "2026-11-20",
  "spec": "ledger-2",
  "market": [ MarketCall … ],
  "stocks":  [ StockCall … ]
}
```

`market_date` = the last trading session the video discusses (usually the session before the upload date; US time). All prices refer to that close unless stated.

### StockCall (one per ticker he gives a view or plan on)

| field | type | meaning |
|---|---|---|
| ticker | str | US ticker as traded (GOOG not 谷歌) |
| holder | "rhino" \| "audience" \| "none" | "rhino" = he says he holds it / shows his card; "audience" = advice to viewers with no own position stated |
| position | {cost, weight_pct, last_change} \| null | from his card: average cost, % of portfolio, last add/trim with date and price if shown |
| stance | "bull" \| "neutral" \| "bear" | his medium-term view of the stock |
| action_today | "buy" \| "add" \| "hold" \| "trim" \| "sell" \| "wait" \| "avoid" | what he did/said to do at this close. "wait" = wants to buy but conditions not met; "avoid" = don't touch |
| size_pct | number \| null | % of portfolio for action_today, if stated |
| valuation | {pe_low, pe_high, pe_mid, fy, eps, value_low, value_high, value_mid, label} \| null | his PE band × EPS for the main fiscal year shown; label = "under" \| "fair" \| "over" as he says it. Add a second object in `valuation_next` for the next year if shown |
| supports | [{low, high, strength, use}] | strength ∈ 小 中 强 超强; use = his tag (止跌长线 / 突破右侧 / 减仓 …) |
| resistances | same shape | |
| plans | [Plan] | his conditional orders, see below |
| invalidation | {price, basis, action} \| null | the level that kills the thesis or triggers defence. basis = "close" \| "open_or_close" \| "intraday" |
| rules_cited | [str] | ids from the rule book when he uses one: NB1…NB18 (04-no-buy-checklist), BP1…BP9 (03-buy-points), or a short Chinese label if none fits |
| reason | str | one sentence, his reasoning |
| quote | str | ≤ 40 characters verbatim from the transcript |
| t | int | seconds into the video |
| note | str | anything uncertain (ASR garble, card unreadable, number guessed) |

### Plan (conditional order)

| field | meaning |
|---|---|
| side | "buy" \| "sell" |
| zone_low, zone_high | price zone (a single level: both equal) |
| size_pct | % of portfolio, or null |
| confirm | "none" (limit order ok) \| "reversal_pattern" (止跌形态) \| "volume_up_candle" (放量阳线) \| "close_above" \| "close_below" \| "other" |
| confirm_text | his words for the condition |
| status | "new" \| "unchanged" \| "filled_today" \| "cancelled" |

### MarketCall (SPY, QQQ, SOXX, SPX, NDX … one per index he gives levels for)

| field | meaning |
|---|---|
| ticker | prefer the ETF he quotes (SPY/QQQ/SOXX); keep SPX if that is what he quotes |
| regime | "up" \| "range" \| "rebound" (反弹结构) \| "down" \| "bear", as he labels the current structure |
| stance | "risk_on" \| "neutral" \| "defensive" |
| key_levels | [{low, high, kind: "support"\|"resistance"\|"pivot", strength, note}] (a single level: low = high) |
| scenarios | [{if: "close_above"\|"close_below"\|"hold_zone", level_low, level_high, then_regime, target_low, target_high, action}] |
| exposure_advice | his advice on overall exposure, short text (加仓/减仓/持现金 …) |
| quote, t | as above |

## Rules for the extractor
- Numbers only from the card or explicit speech. Never compute, never guess; leave null and add a `note`.
- One StockCall per ticker per video. If he revisits a ticker, merge.
- Skip tickers he only mentions in passing (news recap with no view).
- Sizes: "加 2%" → 2; "一半仓位" → write null and put "half of planned position" in note.
- Keep his zones exactly as shown, low < high. List **every** zone on the card, including ones price has already broken through; note "已跌穿" in `use`.
- stance: "bull" only if he says he likes/keeps adding; "holds but won't add" = "neutral". Don't infer from his holdings alone.
- invalidation: only a level he explicitly ties to defence (跌破X减仓 / 破位 / 重回震荡 / 转熊); otherwise null.
- Index levels: prefer SPY over SPX when he gives both; record SPX only if he gives no SPY level.
- Index ETFs and indexes (SPY, QQQ, SOXX, SMH, IWM, DIA, SPX, NDX) always go in `market`, never in `stocks`. Record every index he gives levels or scenarios for (typically QQQ, SPY and SOXX).
- Plan status: a zone price has already fallen through without the required confirmation, which he says he will no longer buy there = "cancelled". A buy he says he made today = "filled_today".
- Chinese names → tickers (谷歌→GOOG, 台积电→TSM, 微软→MSFT, 英伟达→NVDA, 博通→AVGO, 特斯拉→TSLA, 超微→AMD, 奈飞→NFLX, 亚马逊→AMZN, 苹果→AAPL, 脸书/Meta→META).
