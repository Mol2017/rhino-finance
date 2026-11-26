"""Collect the numbers a Rhino-style analysis needs for one US stock, from Yahoo Finance (yfinance).

  python rhino_data.py TICKER [--peers GH,NTRA] [--pe-band 20 30] [--json out.json]

Prints a markdown fact sheet: market structure (QQQ/SPY/SOXX), liquidity gates, EPS/revenue estimates and
revisions, valuation helpers (PE band x EPS, P/S history, peer table), sector ranking for no-buy rule 6, and the
chart: swing legs with Fibonacci levels, dense trading zones, volume candles, wick clusters, unfilled gaps,
RSI(6,24) with divergence state, MAs, MACD, 5-day rolling VWAP, candle patterns on the last bars.
It computes facts only. Judging them (strength tiers, vetoes, buy points) is the analyst's job, using the
reference notes. Thresholds marked DEFAULT are this script's choices, not Rhino's words.
"""
import argparse
import json
import math
import sys
import warnings

warnings.filterwarnings("ignore")
import logging  # noqa: E402
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
try:
    import numpy as np
    import pandas as pd
    import yfinance as yf
except ImportError:
    sys.exit("needs yfinance, pandas, numpy: pip install yfinance  (or use /home/wentao/rhino-finance/.venvs/quant/bin/python)")

SECTOR_ETF = {"technology": "XLK", "healthcare": "XLV", "financial-services": "XLF", "consumer-cyclical": "XLY",
              "consumer-defensive": "XLP", "energy": "XLE", "industrials": "XLI", "basic-materials": "XLB",
              "real-estate": "XLRE", "utilities": "XLU", "communication-services": "XLC"}
OUT = {}


def p(x, d=2):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if isinstance(x, (int, np.integer)) and abs(x) >= 1e6 or isinstance(x, float) and abs(x) >= 1e6:
        for div, s in ((1e12, "T"), (1e9, "B"), (1e6, "M")):
            if abs(x) >= div:
                return f"{x / div:.{d}f}{s}"
    return f"{x:.{d}f}" if isinstance(x, (float, np.floating)) else str(x)


def hist(sym, period="3y"):
    h = yf.Ticker(sym).history(period=period, auto_adjust=False)
    h.index = pd.to_datetime(h.index, utc=True).tz_convert(None).normalize()
    return h[["Open", "High", "Low", "Close", "Volume"]].dropna()


def rsi(s, n):
    d = s.diff()
    a = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    b = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + a / b)


def add_ind(h):
    c = h.Close
    h["R6"], h["R24"] = rsi(c, 6), rsi(c, 24)
    for n in (5, 10, 20, 60, 200):
        h[f"MA{n}"] = c.rolling(n).mean()
    h["DIF"] = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    h["DEA"] = h.DIF.ewm(span=9, adjust=False).mean()
    h["V20"] = h.Volume.rolling(20).mean()
    tp = (h.High + h.Low + h.Close) / 3
    h["RVWAP5"] = (tp * h.Volume).rolling(5).sum() / h.Volume.rolling(5).sum()
    return h


def pivots(h, thr):
    """Zigzag on daily highs/lows: a swing flips when price reverses by thr (fraction) from the running extreme.
    The last point is the running extreme, not yet confirmed."""
    H, L, ix = h.High.values, h.Low.values, h.index
    hi = lo = 0
    trend, pts = 0, []
    for i in range(1, len(H)):
        if trend >= 0 and H[i] > H[hi]:
            hi = i
        if trend <= 0 and L[i] < L[lo]:
            lo = i
        if trend >= 0 and i > hi and L[i] <= H[hi] * (1 - thr):
            if trend == 0 and lo < hi:
                pts.append((ix[lo], "L", L[lo]))
            pts.append((ix[hi], "H", H[hi]))
            trend, lo = -1, i
        elif trend <= 0 and i > lo and H[i] >= L[lo] * (1 + thr):
            if trend == 0 and hi < lo:
                pts.append((ix[hi], "H", H[hi]))
            pts.append((ix[lo], "L", L[lo]))
            trend, hi = 1, i
    pts.append((ix[hi], "H", H[hi]) if trend == 1 else (ix[lo], "L", L[lo]))
    return pts


def fib_line(a, b, close, closes_since):
    """a -> b leg. Returns levels and the close-based status of 61.8%."""
    up = b[2] > a[2]
    rng = b[2] - a[2]
    lv = {k: b[2] - k * rng for k in (0.382, 0.5, 0.618, 1.0)}
    l618 = lv[0.618]
    broke = (closes_since < l618).any() if up else (closes_since > l618).any()
    first = None
    if broke:
        m = closes_since < l618 if up else closes_since > l618
        first = closes_since[m].index[0].date()
    return up, lv, broke, first


def section(t):
    print(f"\n## {t}")


def market():
    section("1. 大盘结构（日线收盘；DEFAULT：用 52 周高低点粗算斐波那契，距 61.8% 在 ±1% 内标“争夺中”，正式判断请按 06 选结构）")
    print("| 指数 | 收盘 | 相对 MA200 | 1 月 | 52 周低→高 | 38.2 / 50 / 61.8 | 最近 5 个收盘相对 61.8 | 判断 |")
    print("|---|---|---|---|---|---|---|---|")
    rows = {}
    for s in ("QQQ", "SPY", "DIA", "IWM", "SOXX"):
        try:
            h = hist(s, "1y")
        except Exception as e:  # noqa: BLE001
            print(f"| {s} | 缺数据 {e} |")
            continue
        c = h.Close
        ma200 = c.rolling(200).mean().iloc[-1]
        lo_i, hi_i = h.Low.idxmin(), h.High.idxmax()
        lo, hi = h.Low.min(), h.High.max()
        up = lo_i < hi_i
        lv = [hi - k * (hi - lo) for k in (0.382, 0.5, 0.618)] if up else [lo + k * (hi - lo) for k in (0.382, 0.5, 0.618)]
        l618 = lv[2]
        seq = "".join("上" if x >= l618 else "下" for x in c.tail(5))
        dist = (c.iloc[-1] / l618 - 1) * 100
        if abs(dist) <= 1:
            st = f"争夺中（{dist:+.1f}%）"
        elif up:
            st = "上行结构仍在" if dist > 0 else "**收盘跌破（破位）**"
        else:
            st = "**收盘站上（反转）**" if dist > 0 else "反弹结构"
        if up and dist > 0 and c.iloc[-1] < ma200:
            st += "；但在 200 日线下方，结构和均线冲突"
        m1 = (c.iloc[-1] / c.iloc[-22] - 1) * 100
        print(f"| {s} | {c.iloc[-1]:.2f} | {(c.iloc[-1] / ma200 - 1) * 100:+.1f}% | {m1:+.1f}% | {lo:.2f} ({lo_i.date()}) → {hi:.2f} ({hi_i.date()}) | "
              f"{' / '.join(f'{x:.1f}' for x in lv)} | {seq}（旧→新） | {st} |")
        rows[s] = {"close": float(c.iloc[-1]), "ma200": float(ma200), "fib": lv}
    extra = []
    for s, name in (("^VIX", "VIX"), ("^TNX", "美 10 年期收益率")):
        try:
            v = hist(s, "1mo").Close
            extra.append(f"{name} {v.iloc[-1]:.2f}（5 日前 {v.iloc[-6]:.2f}）")
            rows[s] = float(v.iloc[-1])
        except Exception:  # noqa: BLE001
            extra.append(f"{name} 缺数据")
    print(f"\n- {'；'.join(extra)}。VIX 25 以上算恐慌。")
    try:
        etfs = list(SECTOR_ETF.values())
        d = yf.download(etfs, period="1mo", auto_adjust=False, progress=False)["Close"]
        r1 = (d.iloc[-1] / d.iloc[-2] - 1) * 100
        r5 = (d.iloc[-1] / d.iloc[-6] - 1) * 100
        order = r5.sort_values(ascending=False)
        print("- 11 个板块 ETF（5 日 / 1 日）：" + "，".join(f"{k} {r5[k]:+.1f}% / {r1[k]:+.1f}%" for k in order.index))
    except Exception:  # noqa: BLE001
        print("- 板块 ETF 缺数据")
    OUT["market"] = rows


def basics(t, info, h):
    section("2. 基本信息与门槛")
    price = h.Close.iloc[-1]
    dv = (h.Close * h.Volume).tail(20).mean()
    mc = info.get("marketCap")
    mc2 = (info.get("sharesOutstanding") or 0) * price
    gates = []
    if mc:
        gates.append("市值 < 50 亿：不碰" if mc < 5e9 else "市值 50-100 亿：低于他的 100 亿底线（见 03 前提）" if mc < 10e9
                     else "市值 100-200 亿：底线附近" if mc < 20e9 else "市值 ≥ 200 亿：OK")
    gates.append("日均成交额 < 1000 万：直接删" if dv < 10e6 else "日均成交额 1000-2000 万：勉强" if dv < 20e6
                 else "日均成交额 OK")
    ed = info.get("earningsTimestamp")
    nxt = None
    try:
        cal = t.calendar
        nxt = cal.get("Earnings Date", [None])[0] if isinstance(cal, dict) else None
    except Exception:  # noqa: BLE001
        pass
    print(f"- {info.get('longName')} · {info.get('sector')} / {info.get('industry')} · 交易所 {info.get('exchange')}")
    print(f"- 收盘 {price:.2f}（{h.index[-1].date()}）· 市值 {p(mc)} · 20 日均成交额 {p(dv)} · 做空占流通 {p((info.get('shortPercentOfFloat') or 0) * 100, 1)}%")
    if mc and mc2 and (mc < 10e9) != (mc2 < 10e9):
        gates.append(f"两种口径跨过 100 亿线：Yahoo marketCap {p(mc)}，股本×价 {p(mc2)}")
    gap = (h.Open.iloc[-1] / h.Close.iloc[-2] - 1) * 100
    print(f"- 门槛：{'；'.join(gates)}")
    print(f"- 最近一日开盘相对前收 {gap:+.1f}%（不买第 17 条要配合新闻判断：非财报消息引起的盘前盘后大涨大跌）")
    print(f"- 下次财报：{nxt or '—'}；上次财报时间戳：{pd.to_datetime(ed, unit='s').date() if ed else '—'}")
    OUT["basics"] = {"price": float(price), "mcap": mc, "dollar_vol20": float(dv), "next_earnings": str(nxt)}


def estimates(t, info):
    section("3. EPS / 营收预期与修正（Yahoo，normalized）")
    try:
        ee, tr, rv, re_ = t.earnings_estimate, t.eps_trend, t.eps_revisions, t.revenue_estimate
    except Exception as e:  # noqa: BLE001
        print(f"缺数据：{e}")
        return
    print("| 期间 | EPS 均值 | 低 | 高 | 分析师 | 90 天前 | 30 天前 | 7 天前 | 30 天上调/下调 | 营收均值 | 营收增速 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    lab = {"0q": "本季", "+1q": "下季", "0y": "本财年", "+1y": "下财年"}
    est = {}
    for k in ("0q", "+1q", "0y", "+1y"):
        if k not in ee.index:
            continue
        e = ee.loc[k]
        trk = tr.loc[k] if k in tr.index else {}
        r = rv.loc[k] if k in rv.index else {}
        v = re_.loc[k] if k in re_.index else {}
        up, dn = r.get("upLast30days"), r.get("downLast30days")
        print(f"| {lab[k]} | {p(e.get('avg'))} | {p(e.get('low'))} | {p(e.get('high'))} | {p(e.get('numberOfAnalysts'), 0)} | "
              f"{p(trk.get('90daysAgo'))} | {p(trk.get('30daysAgo'))} | {p(trk.get('7daysAgo'))} | {p(up, 0)}/{p(dn, 0)} | "
              f"{p(v.get('avg'))} | {p((v.get('growth') or float('nan')) * 100, 1)}% |")
        est[k] = {"eps": e.get("avg"), "eps_90d": trk.get("90daysAgo"), "rev": v.get("avg"), "rev_growth": v.get("growth")}
    OUT["estimates"] = {k: {a: (float(b) if b is not None and not pd.isna(b) else None) for a, b in v.items()} for k, v in est.items()}
    e0, e1 = est.get("0y", {}).get("eps"), est.get("+1y", {}).get("eps")
    flags = []
    if e0 is not None and e1 is not None:
        if e1 < e0:
            flags.append("**衰退型**：下财年 EPS < 本财年")
        if e0 <= 0 or e1 <= 0:
            flags.append("**EPS 为负或接近 0**：不套 PE 估值，用 PS 比同行和自身历史（01）")
    fy_end = info.get("lastFiscalYearEnd")
    if fy_end:
        nfy = pd.to_datetime(info.get("nextFiscalYearEnd") or fy_end + 365 * 86400, unit="s")
        left = (nfy - pd.Timestamp.now()).days
        flags.append(f"本财年结束于 {nfy.date()}，剩约 {left} 天" + ("（已过 3/4：主区间看下一财年）" if left < 92 else ""))
    for f in flags:
        print(f"- {f}")


def valuation(t, info, h, pe_band):
    section("4. 估值辅助")
    price = h.Close.iloc[-1]
    ev = info.get("enterpriseValue")
    fpe = info.get("forwardPE")
    fpe_s = "不适用（EPS ≤ 0）" if fpe is None or fpe <= 0 else p(fpe)
    tpe = info.get("trailingPE")
    tpe_s = "不适用（EPS ≤ 0）" if tpe is None or tpe <= 0 else p(tpe)
    print(f"- 滚动 PE {tpe_s} · 前瞻 PE {fpe_s} · P/S(ttm) {p(info.get('priceToSalesTrailing12Months'))} · "
          f"EV/营收(ttm) {p(info.get('enterpriseToRevenue'))} · 毛利率 {p((info.get('grossMargins') or 0) * 100, 1)}%")
    # cash flow from the statements, not the info field
    try:
        cf = t.quarterly_cashflow
        ocf = cf.loc["Operating Cash Flow"].dropna().sort_index().tail(4)
        cap = cf.loc["Capital Expenditure"].dropna().sort_index().tail(4) if "Capital Expenditure" in cf.index else None
        if len(ocf) == 4:
            fcf = ocf.sum() + (cap.sum() if cap is not None and len(cap) == 4 else 0)
            kind = "**负现金流**（01：负现金流早期成长股没法估值，按风险回报小仓位）" if fcf < 0 else "正现金流"
            print(f"- 近 4 季经营现金流 {p(float(ocf.sum()))}，自由现金流（经营 + 资本开支）{p(float(fcf))}：{kind}")
            if info.get("freeCashflow") and (info["freeCashflow"] > 0) != (fcf > 0):
                print(f"  - 注意：Yahoo 汇总字段 freeCashflow = {p(info['freeCashflow'])}，和报表算出的符号相反，以报表为准")
    except Exception:  # noqa: BLE001
        pass
    est = OUT.get("estimates", {})
    r1 = est.get("+1y", {}).get("rev")
    if ev and r1:
        print(f"- EV / 下财年营收 ≈ {ev / r1:.2f}×")
    if pe_band and est:
        lo, hi = pe_band
        mid = (lo + hi) / 2
        print(f"- PE 区间 {lo}-{hi}（中位 {mid}）：")
        for k, lab in (("0y", "本财年"), ("+1y", "下财年")):
            e = est.get(k, {}).get("eps")
            if e and e > 0:
                print(f"  - {lab} EPS {e:.2f} → 区间 {lo * e:.2f}-{hi * e:.2f}，中位价 {mid * e:.2f}（现价 {price:.2f}）")
    ps_history(t, info, h)


def ps_history(t, info, h):
    """Own P/S(ttm) over time: annual revenue for older years, quarterly TTM for recent; share count at each date."""
    pts = {}
    try:
        a = t.income_stmt.loc["Total Revenue"].dropna()
        for d, r in a.items():
            pts[pd.Timestamp(d)] = float(r)
    except Exception:  # noqa: BLE001
        pass
    try:
        q = t.quarterly_income_stmt.loc["Total Revenue"].dropna().sort_index()
        ttm = q.rolling(4).sum().dropna()
        for d, r in ttm.items():
            pts[pd.Timestamp(d)] = float(r)
    except Exception:  # noqa: BLE001
        pass
    if not pts:
        print("- 自身 P/S 历史：缺数据")
        return
    try:
        sh = t.get_shares_full(start=(min(pts) - pd.Timedelta(days=40)).strftime("%Y-%m-%d"))
        sh.index = pd.to_datetime(sh.index, utc=True).tz_convert(None)
        sh = sh[~sh.index.duplicated()].sort_index()
    except Exception:  # noqa: BLE001
        sh = None
    try:
        lh = t.history(period="10y", auto_adjust=False)
        lh.index = pd.to_datetime(lh.index, utc=True).tz_convert(None).normalize()
        h = lh if len(lh) > len(h) else h
    except Exception:  # noqa: BLE001
        pass
    rows, vals = [], []
    for d in sorted(pts):
        px = h.Close[h.index <= d]
        if not len(px):
            continue
        n = None
        if sh is not None and len(sh[sh.index <= d + pd.Timedelta(days=45)]):
            n = float(sh[sh.index <= d + pd.Timedelta(days=45)].iloc[-1])
        n = n or info.get("sharesOutstanding")
        v = px.iloc[-1] * n / pts[d]
        vals.append(v)
        rows.append(f"{d.date()}: {v:.1f}×")
    cur = info.get("priceToSalesTrailing12Months")
    first = info.get("firstTradeDateMilliseconds")
    yrs = (pd.Timestamp.now() - pd.to_datetime(first, unit="ms")).days / 365 if first else (h.index[-1] - h.index[0]).days / 365
    print(f"- 自身 P/S(ttm) 历史（每个时点用当时股本；年度点用财年营收）：{'；'.join(rows)}")
    if vals and cur:
        print(f"  - 历史均值 {np.mean(vals):.1f}×，范围 {min(vals):.1f}-{max(vals):.1f}×，现在 {cur:.1f}×"
              + (f"；**上市只有约 {yrs:.1f} 年，不足 01 要求的 5 年**" if yrs < 5 else "")
              + f"。Yahoo 只给约 4 个财年的营收，{len(vals)} 个点不够看 5 年平均，需要时用 WebSearch 补")


def peers(info, symbols):
    section("5. 同行对比（DEFAULT：Yahoo 同细分行业市值前列；业务不像的请用 --peers 指定）")
    if not symbols:
        try:
            tc = yf.Industry(info["industryKey"]).top_companies
            symbols = [s for s in tc.index[:10]]
        except Exception as e:  # noqa: BLE001
            print(f"缺数据：{e}")
            return
    print("| 代码 | 市值 | P/S(ttm) | EV/营收 | 营收增速 | 毛利率 | 前瞻 PE |")
    print("|---|---|---|---|---|---|---|")
    for s in symbols:
        try:
            i = yf.Ticker(s).info
        except Exception:  # noqa: BLE001
            i = {}
        if not i.get("marketCap"):
            print(f"| {s} | 缺数据（可能已退市或被收购） | | | | | |")
            continue
        print(f"| {s} | {p(i.get('marketCap'))} | {p(i.get('priceToSalesTrailing12Months'))} | {p(i.get('enterpriseToRevenue'))} | "
              f"{p((i.get('revenueGrowth') or float('nan')) * 100, 1)}% | {p((i.get('grossMargins') or float('nan')) * 100, 1)}% | {p(i.get('forwardPE')) if (i.get('forwardPE') or 0) > 0 else '不适用'} |")


def sector_rank(sym, info, h):
    section("6. 板块排名（不买第 6 条：前一交易日跌幅排前 10%）")
    key = info.get("sectorKey")
    etf = SECTOR_ETF.get(key)
    try:
        comp = list(yf.Sector(key).top_companies.index)
    except Exception as e:  # noqa: BLE001
        print(f"缺数据：{e}")
        return
    if sym not in comp:
        comp.append(sym)
    data = yf.download(comp + ([etf] if etf else []), period="10d", auto_adjust=False, progress=False)["Close"]
    ret = data.pct_change().iloc[-1].dropna() * 100
    stocks = ret.drop(labels=[etf], errors="ignore").sort_values()
    n = len(stocks)
    rank = list(stocks.index).index(sym) + 1 if sym in stocks.index else None
    print(f"- 样本：Yahoo 板块 {key} 市值前 {n} 只（DEFAULT 代替板块 ETF 全部成分股）；ETF {etf} 当日 {ret.get(etf, float('nan')):+.2f}%")
    if rank:
        hit = rank <= max(1, round(n * 0.10))
        print(f"- {sym} 最近交易日 {stocks[sym]:+.2f}%，跌幅排第 {rank}/{n}" + ("，**命中不买第 6 条**" if hit else "，未命中"))
    worst = ", ".join(f"{s} {v:+.1f}%" for s, v in stocks.head(5).items())
    print(f"- 跌幅前 5：{worst}")
    try:
        ih = yf.download(list(yf.Industry(info["industryKey"]).top_companies.index[:15]) + [sym], period="10d",
                         auto_adjust=False, progress=False)["Close"].pct_change().iloc[-1].dropna().sort_values() * 100
        print(f"- 细分行业（{info.get('industry')}）里排第 {list(ih.index).index(sym) + 1}/{len(ih)}（{ih[sym]:+.2f}%）")
    except Exception:  # noqa: BLE001
        pass


def candles(h):
    """Classify the last 3 bars with the grading rules in references/03 (simplified)."""
    out = []
    for k in range(-3, 0):
        r, q = h.iloc[k], h.iloc[k - 1]
        body = abs(r.Close - r.Open)
        rng = r.High - r.Low
        lo_sh = min(r.Open, r.Close) - r.Low
        up_sh = r.High - max(r.Open, r.Close)
        qb_lo, qb_hi = min(q.Open, q.Close), max(q.Open, q.Close)
        tags = []
        b = max(body, rng * 0.02)
        if lo_sh >= 2 * b and up_sh <= 0.5 * b:
            grade = "1档" if min(r.Open, r.Close) < qb_lo and qb_lo < max(r.Open, r.Close) <= qb_hi else (
                "非锤子线（开收盘都在前一日实体上方）" if min(r.Open, r.Close) > qb_hi else "2档或跳空档")
            tags.append(f"锤子线形({grade})")
        if up_sh >= 2 * b and lo_sh <= 0.5 * b:
            tags.append("倒锤子线/流星线形")
        if r.Close > r.Open and r.Close > q.High and r.Open <= q.Low * 1.005:
            tags.append("看涨抱线（含影线）")
        elif r.Close > r.Open and q.Close < q.Open and r.Close >= q.Open and r.Open <= q.Close:
            tags.append("看涨吞没（实体）")
        if q.Close < q.Open and qb_lo <= min(r.Open, r.Close) and max(r.Open, r.Close) <= qb_hi:
            tags.append("看涨孕线（实体在内）")
        vr_prev = r.Volume / q.Volume
        vr20 = r.Volume / r.V20
        out.append(f"{h.index[k].date()} 开{r.Open:.2f} 高{r.High:.2f} 低{r.Low:.2f} 收{r.Close:.2f} · 下影/实体 {lo_sh / b:.1f}× 上影/实体 {up_sh / b:.1f}× · "
                   f"量/前日 {vr_prev:.2f} 量/20日均 {vr20:.2f} · {('、'.join(tags) or '无形态')}")
    # morning star on last 3
    a, s, c = h.iloc[-3], h.iloc[-2], h.iloc[-1]
    if a.Close < a.Open and abs(s.Close - s.Open) < (s.High - s.Low) * 0.35 and c.Close > c.Open and c.Close > max(a.Open, a.High * 0.999):
        out.append("最后三根像启明星（第三根过第一根实体上沿和上影线）；量：第三根 / max(前两根) = "
                   f"{c.Volume / max(a.Volume, s.Volume):.2f}（≥0.67 合格，<0.5 无效）")
    return out


def divergence(h):
    """Current RSI6/RSI24 segment (since their last cross) and whether price vs RSI6 diverges in it."""
    d = np.sign(h.R6 - h.R24)
    cross = d.ne(d.shift()).cumsum()
    seg = h[cross == cross.iloc[-1]]
    side = "RSI6 < RSI24（下行段）" if d.iloc[-1] < 0 else "RSI6 > RSI24（上行段）"
    msg = f"当前段始于 {seg.index[0].date()}，{side}，共 {len(seg)} 天"
    if len(seg) >= 3:
        if d.iloc[-1] < 0:
            i_min = seg.Close.idxmin()
            last = seg.iloc[-1]
            if seg.index[-1] == i_min:
                prior = seg.iloc[:-1]
                j = prior.Close.idxmin()
                if last.R6 > prior.at[j, "R6"]:
                    msg += f"；**底背离**：收盘新低 {last.Close:.2f} < {prior.at[j, 'Close']:.2f}（{j.date()}），RSI6 {last.R6:.1f} > {prior.at[j, 'R6']:.1f}"
                else:
                    msg += "；收盘创段内新低，RSI6 也新低，无背离"
            else:
                msg += f"；段内最低收盘 {seg.Close.min():.2f}（{i_min.date()}，RSI6 {seg.at[i_min, 'R6']:.1f}），今天不是新低，背离待定"
        else:
            i_max = seg.Close.idxmax()
            last = seg.iloc[-1]
            if seg.index[-1] == i_max:
                prior = seg.iloc[:-1]
                j = prior.Close.idxmax()
                if last.R6 < prior.at[j, "R6"]:
                    msg += f"；**顶背离**：收盘新高 {last.Close:.2f}，RSI6 {last.R6:.1f} < {prior.at[j, 'R6']:.1f}（{j.date()}）"
    return msg


def td9(h):
    """DeMark setup count: consecutive closes below (buy setup) or above (sell setup) the close 4 bars earlier."""
    c = h.Close.values
    buy = sell = 0
    hist_ = []
    for i in range(4, len(c)):
        buy = buy + 1 if c[i] < c[i - 4] else 0
        sell = sell + 1 if c[i] > c[i - 4] else 0
        hist_.append((h.index[i], buy, sell))
    d, b, s_ = hist_[-1]
    last9 = [x for x in hist_[-15:] if x[1] == 9 or x[2] == 9]
    txt = f"今天下跌计数 {b}、上涨计数 {s_}"
    if last9:
        x = last9[-1]
        txt += f"；最近一次 9 出现在 {x[0].date()}（{'下跌九转，看止跌' if x[1] == 9 else '上涨九转，看滞涨'}）"
    return txt + "。07：出现 9 就看，不在第 9 根当天进场，等止跌/滞涨形态"


def chart(h):
    section("7. 日线指标（收盘）")
    r = h.iloc[-1]
    c = r.Close
    low20 = h.Close.iloc[-21:-1].min()
    print(f"- RSI6 {r.R6:.1f} · RSI24 {r.R24:.1f}"
          + (" · **RSI6 > 90（不买第 15 条）**" if r.R6 > 90 else " · RSI6 > 80 超买" if r.R6 > 80 else " · **RSI6 < 20 超卖**" if r.R6 < 20 else ""))
    print(f"- 背离：{divergence(h)}")
    print(f"- MA5 {r.MA5:.2f} · MA10 {r.MA10:.2f} · MA20 {r.MA20:.2f} · MA60 {r.MA60:.2f} · MA200 {r.MA200:.2f}（收盘在 200 日线{'上' if c > r.MA200 else '下'}方）"
          + (" · 20/30/60 多头排列" if r.MA20 > h.Close.rolling(30).mean().iloc[-1] > r.MA60 else ""))
    zone = "都在零轴上（进攻思维）" if r.DIF > 0 and r.DEA > 0 else "都在零轴下（防御思维）" if r.DIF < 0 and r.DEA < 0 else "一上一下（不判断）"
    print(f"- MACD DIF {r.DIF:.2f} / DEA {r.DEA:.2f}：{zone}，{'金叉状态' if r.DIF > r.DEA else '死叉状态'}")
    print(f"- 5 日滚动 VWAP {r.RVWAP5:.2f}（收盘在其{'上' if c > r.RVWAP5 else '下'}方）")
    print(f"- 近期新低（DEFAULT：低于前 20 个交易日最低收盘 {low20:.2f}）：{'**是，命中不买第 1 条**' if c < low20 else '否'}")
    v5 = h.Volume.rolling(5).mean()
    print(f"- 5 日均量 {v5.iloc[-1] / 1e6:.2f}M，较前一日{'上升' if v5.iloc[-1] > v5.iloc[-2] else '**拐头向下**'}（不买第 4 条：缩量反弹）")
    print(f"- 九转（DeMark 9）：{td9(h)}")
    print("- 最近 3 根 K 线：")
    for line in candles(h):
        print(f"  - {line}")
    print("\n最近 10 个交易日：")
    print("| 日期 | 开 | 高 | 低 | 收 | 量(M) | 量/前日 | 量/20日 | 5日均量(M) | RSI6 | RSI24 |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    h = h.assign(V5=h.Volume.rolling(5).mean())
    t = h.tail(11)
    for i in range(1, len(t)):
        x, y = t.iloc[i], t.iloc[i - 1]
        print(f"| {t.index[i].date()} | {x.Open:.2f} | {x.High:.2f} | {x.Low:.2f} | {x.Close:.2f} | {x.Volume / 1e6:.2f} | "
              f"{x.Volume / y.Volume:.2f} | {x.Volume / x.V20:.2f} | {x.V5 / 1e6:.2f} | {x.R6:.1f} | {x.R24:.1f} |")
    OUT["indicators"] = {"rsi6": float(r.R6), "rsi24": float(r.R24), "ma200": float(r.MA200), "dif": float(r.DIF), "dea": float(r.DEA)}


def clean_legs(pts, min_bars, idx):
    """Drop legs shorter than min_bars trading days by removing an inner pair, keeping the outer extremes."""
    pts = list(pts)
    pos = {d: i for i, d in enumerate(idx)}
    changed = True
    while changed and len(pts) > 3:
        changed = False
        for i in range(1, len(pts) - 2):
            if pos[pts[i + 1][0]] - pos[pts[i][0]] < min_bars:
                a, b, c, d = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
                # remove (b, c) if d is at least as extreme as b, else remove (c, d)
                if (b[1] == "H" and d[2] >= b[2]) or (b[1] == "L" and d[2] <= b[2]):
                    del pts[i:i + 2]
                elif i + 3 <= len(pts) - 1:
                    del pts[i + 1:i + 3]
                else:
                    continue
                changed = True
                break
    return pts


def structure(h):
    rng = ((h.High - h.Low) / h.Close).tail(60).median()
    thr = max(0.10, 2.5 * rng)
    section(f"8. 结构：波段与斐波那契（DEFAULT：日线 zigzag，反转阈值 {thr * 100:.0f}% = max(10%, 2.5×近 60 日中位振幅)，"
            "少于 5 个交易日的段并掉；最后一个点是未确认的极值）")
    c = h.Close.iloc[-1]
    hh = h.tail(400)
    pts = clean_legs(pivots(hh, thr), 5, list(hh.index))
    legs = list(zip(pts[:-1], pts[1:]))[-4:]
    y = h.tail(252)
    lo_i, hi_i = y.Low.idxmin(), y.High.idxmax()
    big = ((lo_i, "L", y.Low.min()), (hi_i, "H", y.High.max())) if lo_i < hi_i else ((hi_i, "H", y.High.max()), (lo_i, "L", y.Low.min()))
    extra = [(big, "52 周大结构")]
    if lo_i < hi_i:  # after the 52-week high, the decline so far (its 61.8% = the reversal-confirmation level)
        after = h[h.index > hi_i]
        if len(after) >= 5:
            j = after.Low.idxmin()
            extra.append((((hi_i, "H", y.High.max()), (j, "L", after.Low.min())), "52 周高点以来的回落，倒过来画"))
    rows = [(l, "") for l in legs] + [e for e in extra if e[0] not in legs]
    print("| 段 | 起点 → 终点 | 涨跌 | 38.2 / 50 / 61.8 / 100 | 61.8 收盘状态 | 现价到 61.8 |")
    print("|---|---|---|---|---|---|")
    out = []
    for (a, b), tag in rows:
        since = h.Close[h.index > b[0]]
        up, lv, broke, first = fib_line(a, b, c, since)
        st = (f"**{first} 收盘跌破**" if broke else "守住") if up else (f"**{first} 收盘站上（反转）**" if broke else "未站上（反弹结构）")
        print(f"| {'上行' if up else '下行'}{('（' + tag + '）') if tag else ''} | {a[2]:.2f}（{a[0].date()}）→ {b[2]:.2f}（{b[0].date()}） | "
              f"{(b[2] / a[2] - 1) * 100:+.0f}% | {' / '.join(f'{lv[k]:.2f}' for k in (0.382, 0.5, 0.618, 1.0))} | {st} | "
              f"{(lv[0.618] / c - 1) * 100:+.1f}% |")
        out.append({"from": [str(a[0].date()), a[2]], "to": [str(b[0].date()), b[2]], "levels": lv, "broke618": bool(broke), "tag": tag})
    r = h.iloc[-1]
    print(f"\n- 现价 {c:.2f}；到 MA200 {r.MA200:.2f} 的距离 {(r.MA200 / c - 1) * 100:+.1f}%；"
          f"数据内最高 {h.High.max():.2f}（{h.High.idxmax().date()}），最低 {h.Low.min():.2f}（{h.Low.idxmin().date()}）")
    print("- 盈亏比要自己定止损和目标后算：(目标 − 买入) ÷ (买入 − 止损) ≥ 1（重仓 ≥ 2）。不买第 2 条的“很近”DEFAULT = 盈亏比 < 1:1")
    OUT["legs"] = out


def zones(h):
    section("9. 区间候选（只给事实，强弱按 02 的七原则自己评）")
    c = h.Close.iloc[-1]
    x = h.loc[h.index >= h.index[-1] - pd.Timedelta(days=365)]
    step = max(0.5, round(c * 0.02, 1))
    lo, hi = x.Low.min(), x.High.max()
    edges = np.arange(math.floor(lo / step) * step, hi + step, step)
    bl, bh = np.minimum(x.Open, x.Close), np.maximum(x.Open, x.Close)
    rows = []
    for e in edges:
        m = (bh >= e) & (bl <= e + step)
        rows.append((e, int(m.sum()), x.Volume[m].sum()))
    df = pd.DataFrame(rows, columns=["lo", "days", "vol"])
    thr = df.days.quantile(0.7)
    df["dense"] = df.days >= thr
    print(f"**密集交易区**（近 1 年，按 {step} 美元一档数实体覆盖天数，DEFAULT：天数前 30% 的连续档合并）：")
    grp = (df.dense != df.dense.shift()).cumsum()
    for _, g in df[df.dense].groupby(grp[df.dense]):
        a, b = g.lo.min(), g.lo.max() + step
        print(f"- {a:.2f}-{b:.2f}：{int(g.days.max())} 天/档，成交 {p(float(g.vol.sum()))}，{'现价在内' if a <= c <= b else '在现价上方（压力）' if a > c else '在现价下方（支撑）'}")
    print("\n**增量 K 线**（近 6 个月，DEFAULT：量 ≥ 1.8×20 日均量、实体 ≥ 全长 55%）：")
    y = h.iloc[-130:]
    big = y[(y.Volume >= 1.8 * y.V20) & ((y.Close - y.Open).abs() >= 0.55 * (y.High - y.Low))]
    for d, r in big.iterrows():
        top, bot = max(r.Open, r.Close), min(r.Open, r.Close)
        pos = "现价在实体上方" if c > top else "现价在实体下方" if c < bot else "现价在实体内"
        print(f"- {d.date()} {'阳' if r.Close > r.Open else '阴'}线 量 {r.Volume / r.V20:.1f}× · 上沿 {top:.2f} / 中 {(top + bot) / 2:.2f} / 下沿 {bot:.2f} · {pos}")
    if big.empty:
        print("- 无")
    def clusters(series, tol, fn, win):
        loc = series[(series == series.rolling(2 * win + 1, center=True).apply(fn, raw=True))].dropna().sort_values()
        out, cur = [], []
        for d, v in loc.items():
            if cur and (v > cur[-1][1] * (1 + tol) or v > cur[0][1] * (1 + 2 * tol)):
                out.append(cur)
                cur = []
            cur.append((d, v))
        if cur:
            out.append(cur)
        return [cl for cl in out if len(cl) >= 2]

    y12 = h.loc[h.index >= h.index[-1] - pd.Timedelta(days=365)]
    print("\n**有效高低点**（224：近 1 年日线，局部极值 = 左右各 3 根里最低/最高，相邻相差 ≤ 1% 记为同一价位（整档宽度 ≤ 2%），≥ 3 次才算有效）：")
    for col, name, fn in (("Low", "低点", np.min), ("High", "高点", np.max)):
        cl = clusters(y12[col], 0.01, fn, 3)
        txt = "；".join(f"{min(v for _, v in c_):.2f}-{max(v for _, v in c_):.2f} × {len(c_)} 次{'（有效）' if len(c_) >= 3 else ''}" for c_ in cl)
        print(f"- {name}：{txt or '没有 2 次以上的聚集'}")
    y24 = h.loc[h.index >= h.index[-1] - pd.Timedelta(days=730)]
    print("\n**箱体边缘 / 多次测试的低点和高点**（近 2 年，局部极值左右各 5 根，DEFAULT：相邻相差 ≤ 3% 归为一档（整档宽度 ≤ 6%），列 ≥ 3 次的）：")
    for col, name, fn in (("Low", "低点", np.min), ("High", "高点", np.max)):
        cl = [c_ for c_ in clusters(y24[col], 0.03, fn, 5) if len(c_) >= 3]
        for c_ in cl:
            ds = "、".join(d.strftime("%Y-%m") for d, _ in sorted(c_))
            print(f"- {name} {min(v for _, v in c_):.2f}-{max(v for _, v in c_):.2f} × {len(c_)} 次（{ds}）")
        if not cl:
            print(f"- {name}：无")
    print("\n**未回补缺口**（近 6 个月）：")
    gaps = []
    for i in range(1, len(y)):
        a, b = y.iloc[i - 1], y.iloc[i]
        later = y.iloc[i:]
        if b.Low > a.High and later.Low.min() > a.High:
            gaps.append(f"向上缺口 {a.High:.2f}-{min(b.Low, later.Low.min()):.2f}（{y.index[i].date()}）")
        if b.High < a.Low and later.High.max() < a.Low:
            gaps.append(f"向下缺口 {max(b.High, later.High.max()):.2f}-{a.Low:.2f}（{y.index[i].date()}）")
    print("- " + ("\n- ".join(gaps) if gaps else "无"))


def weekly(h):
    section("10. 周线（最近 12 周）")
    w = h.resample("W-FRI").agg({"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}).dropna().tail(12)
    print("| 周 | 开 | 高 | 低 | 收 | 量(M) |")
    print("|---|---|---|---|---|---|")
    last_day = h.index[-1]
    for d, r in w.iterrows():
        note = f"（本周未完成，截至 {last_day.date()}）" if d == w.index[-1] and last_day.weekday() < 4 else ""
        print(f"| {d.date()}{note} | {r.Open:.2f} | {r.High:.2f} | {r.Low:.2f} | {r.Close:.2f} | {r.Volume / 1e6:.1f} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ticker")
    ap.add_argument("--peers", help="comma-separated close peers for the P/S table")
    ap.add_argument("--pe-band", nargs=2, type=float, metavar=("LO", "HI"))
    ap.add_argument("--json")
    ap.add_argument("--no-market", action="store_true")
    a = ap.parse_args()
    sym = a.ticker.upper()
    t = yf.Ticker(sym)
    info = t.info
    h = add_ind(hist(sym, "3y"))
    if h.empty:
        sys.exit(f"no price data for {sym}")
    print(f"# {sym} 数据单 · 截至 {h.index[-1].date()} 收盘 · 来源 Yahoo Finance（yfinance）")
    print("所有价位按日线收盘计算；DEFAULT 标注的阈值是脚本的默认值，不是 Rhino 原话。")
    if not a.no_market:
        market()
    basics(t, info, h)
    estimates(t, info)
    valuation(t, info, h, a.pe_band)
    peers(info, a.peers.split(",") if a.peers else None)
    sector_rank(sym, info, h)
    chart(h)
    structure(h)
    zones(h)
    weekly(h)
    if a.json:
        json.dump(OUT, open(a.json, "w"), default=str, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
