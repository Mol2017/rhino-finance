# How Rhino values a stock (part 1 of the model, draft 2026-11-24)

Source: 17 member teaching episodes on valuation, each turned into a clean transcript (`data/clean/<id>.md`) and an extract (`data/extract/<id>.json`). Episode numbers in brackets, e.g. [58]. Ep 79 is the January 2022 weekly episode where he builds the yearly value table for 26 stocks.

| Ep | Topic | Ep | Topic |
|---|---|---|---|
| 02 | Reading reports, TSLA upper bound | 88 | DCF |
| 26, 27 | Valuation + chart, worked cases | 116 | ERP |
| 56 | Analyst ratings | 177 | EPS consensus |
| 57 | What valuation is | 237 | Analyst revisions, S&P range |
| 58 | PE and trailing PE method | 261 | CAPM, supply/demand |
| 59 | PEG | 305 | Tracking EPS revisions (free data) |
| 60 | PB and ROE | 61 | Review of his own holdings |
| 69 | Sector PE/EPS/PEG/ROE table | 87 | Rates, yields, inflation |

## 1. The idea in one paragraph

**Price = PE × EPS.** EPS is the rational part: it can be forecast, and analysts' consensus is good enough. PE is the emotional part: it can't be forecast, so he never predicts it. He measures the range it normally moves in [61, 58]. Multiplying the two gives a **value range**, not a target. Below the range is cheap, inside is fair, above is expensive. Valuation decides **whether** a stock is worth buying and **roughly where**. The chart then picks the exact price [61: "基本面先行，技术面确认", fundamentals first, the chart confirms].

## 2. The steps

### Step 1 · Should valuation be used at all?
- Not for day trading. Yes for anyone buying on value or holding for a while [57].
- Only in an efficient market (the US) [57].
- Only where consensus can be trusted: many analysts covering it. Skip new IPOs, small caps and companies whose business keeps changing [177]. Ratings with fewer than ~10 analysts are ignored [56].
- Only stocks in the S&P, Nasdaq or Nasdaq Composite. If daily dollar volume is tiny, every chart pattern is void ("you can get in but not out") [27].

### Step 2 · What kind of company is it? This picks the tool.
| Company type | Main tool | Source |
|---|---|---|
| Steadily profitable | PE | [61, 88] |
| Asset-heavy or cyclical: banks, insurers, REITs, steel, energy | PB, then ROE to decide | [60, 61] |
| Unprofitable but revenue growing fast | PS against close peers | [88] |
| Negative cash flow, early stage | Can't be valued. Size it small and think in risk/reward | [88] |
| Next year's EPS below this year's ("recession type") | Excluded. PEG, ERP and CAPM all fail here | [59, 116, 261] |
| Commodities, biotech, small pharma | Outside his circle. Chart only, or skip | [69] |

Tie-breaker: use the method that gives the **narrowest** range. A PE range of 80–300 is useless; a PB range of 90–120 is usable [60].

### Step 3 · Get EPS: level, then direction
- **Source:** consensus from Yahoo's Analysis page, FactSet, or his own multi-source database. Drop the extreme forecasts ("like judges dropping the top and bottom score") [305]. Free data within ~15% of paid data is fine [177].
- **Discount the sell side.** For healthcare 2024 he used 20.1% growth where FactSet said 34.5% [177].
- **GAAP or adjusted:** in 2021 he said GAAP and never mix the two [58]. By 2026 he always uses adjusted ("Normalized") EPS [305], and so do the weekly tables. Current practice is adjusted.
- **"Growth" means EPS growth.** Revenue matters only for growth or unprofitable companies [305].
- **Direction beats level.** He compares the estimate with 7, 30, 60 and 90 days ago, and counts analysts raising vs cutting [177, 305]. He weighs the size of a cut, not the number of cuts: the S&P 2025 estimate falling by under $1 is not a real cut [237]. A guidance change outside earnings season means bad news is being released early [177].
- **Red flags:**
  - growth that only looks high because last year was low [69];
  - a one-off income line that turns a loss into a profit, e.g. TSLA regulatory credits in 2020 [02];
  - liabilities above 130–150% of assets, or negative ROE [69].

### Step 4 · Set the PE band (the open question)
He has used three versions over time.

1. **2021: trailing-PE statistics [58].**
   - Every trading day, take close ÷ trailing-12-month EPS. Keep 90 days (180 also works).
   - Band = mean ± 1 standard deviation.
   - Band × trailing EPS = current value range. Band × next year's EPS = forward range.
   - Recompute after every quarterly report [26: "the range is based on last quarter's report"]. The value ranges in his 2021 cases (FICO 436–512, LIN 230–253, PPG 134–146) come from this.
2. **Anchoring to the stock's own history [61].**
   - Compare current PE, forward PE and PEG with the company's past years (Morningstar's Valuation tab).
   - **Drop 2020.** Treat 2019 as the normal year.
   - **Compare with years that had the same interest rates.** For zero rates use 2014; for 2% rates use 2018 (AAPL had PE 13 then, so "AAPL at 2% rates is worth 80–100").
   - In high-inflation years, ~3% above the historical average is acceptable. Anything more is liquidity froth.
   - The history is only useful if the company's growth rate is similar to then.
3. **Since 2022: the yearly "value trading range" table [79, then 183, 311].**
   - **PE low and high:** the stock's 2018–2019 range, on adjusted (non-GAAP) earnings. The median PE is their average.
     - **Why 2018–19:** he expected 2022–24 to have a similar economy and monetary policy. 2020 is never used.
     - By 2026 the column header reads "historical range".
   - **Ranges:** both PEs × consensus adjusted EPS for this fiscal year and next.
     - **Median PE × this year's EPS = the fair price at fiscal year-end.**
     - Next year's median minus this year's is the theoretical profit if you buy near this year's median.
   - **Horizon:** trade one fiscal year at a time. The year after is reference only and changes every quarter. Mind fiscal year-ends (PG and EL end in June).
   - **He overrides the history-based PE in four cases [79]:**
     - **Temporarily depressed earnings that will recover** (airlines after Covid): use **next** year's range. DAL's 2022 median was 26, its 2023 median 63.
     - **This year's EPS falls, next year's recovers** (banks in 2022): buy into this year's weakness, target next year's median, don't chase.
     - **A former hyper-growth stock that has matured** (NFLX: its 2018–19 PE of 92–263 would give prices in the thousands): use a "normal PE that matches growth". About 20% growth maps to **25–30×**.
     - **Cheap only on paper** (C: median 90 vs price 58): unstable results and spending not yet in the EPS forecast. Not treated as cheap; re-check after each report.
   - **EPS in a growth phase:** don't expect the bottom of a wide band. ASML's band is 406–864, but with EPS growing, 406 "makes no sense".
   - **The top of the band is not a target.** For a stock without hype (banks), the high-PE price is short-lived.
   - **Recompute every quarter,** in the month reports come out.
   - **In 2024–26** growth names get round tiers (20–30, 30–40, 40–60), and he moves a stock's tier when its status or growth changes [183, 311].

Cross-checks on the PE level:
- **Industry norms:** traditional autos 10–20, mega-cap tech 30–40, hyper-growth ~150 [02].
- **S&P 500:** normal forward PE 18–22 [69, 237].
- **Fast growers:** a high current PE with a much lower forward PE is "expensive this year, fair next year", provided growth holds [61].

### Step 5 · Compute and label
- Range = low PE × EPS to high PE × EPS, for this fiscal year and next.
- Below the range = under, inside = fair, above = over.
- **Ceiling test** [02]: plug every optimistic assumption into EPS and use the highest plausible PE. If the price is still above that, it has priced in years of future growth.
  - In that case, buying is speculation, and he insists on keeping speculation and value investing apart. Never call a losing speculative trade a long-term hold.
- **Index** [237]:
  - S&P EPS × 18 and × 22 for this year and next.
  - The market trades 6–12 months ahead, so by year-end the index "shouldn't be below next year's lower bound" unless next year's EPS is cut hard. Anything below it is an opportunity.

### Step 6 · Second opinions. Each one has a narrow job.
| Tool | What he uses it for | When it doesn't apply |
|---|---|---|
| PEG [59, 69] | Ranking close peers (AMD vs INTC, not AMD vs NVDA). For sectors: first EPS growth above the S&P's, then PEG below the S&P's | Never a price for one stock. He rejects the "PEG < 1" rule. Needs positive and rising EPS |
| PB + ROE [60] | Asset-heavy peers. The higher ROE wins even if the other looks cheaper (BAC over WFC) | Tech companies |
| ERP [116] | Will institutions buy here? Earnings yield − 10-year yield; below 3% is unattractive. Price where it becomes attractive = EPS ÷ (10-year yield + 3%) | Negative EPS; EPS trending down ("that's not cheap, it can get cheaper") |
| CAPM [261] | Expected return for the year vs what the stock has already done; the "red line" where quant funds sell (TSLA at ~470 in Oct 2025) | EPS falling, revenue not growing, or beta below 1 |
| DCF [88, 56] | Understanding why higher rates cut every valuation; a conservative check that value is above market cap | **He says he does not use DCF for buy/sell decisions**: "I use the trailing-PE method" [56]. Analyst targets are DCF-based, so treat them as reference only |
| Analyst ratings [56] | Treat ratings as a bit too high. A big bank moving to Hold and cutting its target is a hidden sell. Downgrade drops are short and can be bought if your own work disagrees | Fewer than ~10 analysts |

Rates [87, 88, 61]:
- A rising 10-year yield lowers every valuation, unprofitable growth stocks most.
- A premium built on zero rates will revert once hikes are certain. The market starts moving about 6 months before the first hike.
- A rising forward operating margin turning down is a warning about a year ahead [305].

### Step 7 · From value to action (hands over to parts 2 and 3)
- **Where to buy:** first ask how far valuation allows the price to fall (e.g. back to the 2019 PE means AAPL −10%). Then find chart support inside that allowance. Put orders where the two overlap [61].
- **Best case:** inside the value range, on a support zone, with a bottoming candle. Buy a starter position, and add near the bottom of the support. Strong support **below** the value range is even better [26, 27].
- **The buy point is where the median price meets the nearest strong support** [79]. For TSM: median 120, strong support 112–124.
  - When support covers the median, wait about 10% below it (BAC: median 43, buy at 40, 39 and 38).
  - Never buy above the top of the range.
  - The closer to the bottom of the range, the closer to a "golden pit".
  - Only strong supports count, and you wait for signs that buyers are stepping in.
  - If all that's left is a small dividend, keep the cash and sell options instead.
  - "Risk comes from rises, opportunity from falls" applies only to stocks that have real value [79].
- **Chart beats valuation when structure breaks:**
  - PPG gapped down through support into its value range. He read that as "something we can't see; the valuation may get cut", so he waited for lower tiers: a small buy at 126–133 and a confident buy at 110–118 [27].
  - ITW gapped below its 20- and 60-day averages a week before earnings, with EPS estimates falling. He skipped it [26].
- **Expensive but strong:**
  - No starter position: don't chase.
  - A low-cost position already held: add at support, or trim high and buy back lower [61].
- **Size follows the valuation gap** [61]:
  - First buy in an expensive stock is small; expect another −30%.
  - Below value, ladder orders, larger the lower they sit (APD 268 / 246–249 / 237–239; MA 2% / 2% / 4%).
  - His average cost should be one that survives −30% with PE still at a historically normal level.
- **Keep it current:**
  - Redo ranges after every quarterly report.
  - Move buy levels up as earnings rise [237].
  - Check each report against the reason you bought [59].
  - "Last year's strategy is not this year's strategy" [237].

## 3. What this answers from the open questions
- **Q1, how he picks the PE band: answered.**
  - **2021:** statistics on his own trailing PE (90-day mean ± 1 SD).
  - **From 2022:** the stock's 2018–19 PE low and high on adjusted earnings, chosen because he expected a similar rate environment.
  - **Overrides:**
    - next year's range for earnings that are recovering;
    - a growth-matched "normal PE" for former hyper-growth stocks;
    - distrust when EPS doesn't yet reflect coming costs.
  - **Moving a band:** he moves it by hand when a company's status or growth changes, e.g. NVDA 30–40 → 20–30 in 2026 [311].
  - **Still not explained:** the exact rule for moving a band.
- **Q4, valuation vs chart:**
  - Valuation gives permission and a floor.
  - The chart gives the price.
  - A break in structure overrides "cheap" (wait for a lower tier).
  - Falling EPS estimates also override "cheap": "not cheap, it can get cheaper".
  - When a stock is expensive but strong, what you already own decides it.
- **New fact:** DCF, CAPM and ERP are explanations and second opinions, not his decision tool. The decision tool is the PE band × EPS.

## 4. How the method changed over time
| | 2021 (ep 26–61) | 2022 onward (weekly tables, ep 79, 183, 311, 305) |
|---|---|---|
| EPS | Trailing 12 months, GAAP | Consensus for this and next fiscal year, adjusted |
| PE band | 90-day mean ± 1 SD of trailing PE | 2018–19 PE low/high (median = fair price at year-end); round tiers for growth names; moved by hand |
| Revisions | Mentioned | Central: EPS Trend, Yardeni forward EPS line, FactSet weekly |
| Rates | Same-rate-year comparisons; zero-rate premium | ERP vs 10-year yield; CAPM uses the 10-year as risk-free rate |
