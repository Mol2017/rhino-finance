"""Rhino's buy points and no-buy rules as mechanical conditions on daily OHLCV.

Source rules: rhino/skill/rhino-stock-analysis/references/03-buy-points.md (member ep. 302)
and 04-no-buy-checklist.md (member ep. 301). Every flag is computed from data up to and
including the close of day t; the trade is assumed to be entered at that close
("收盘附近买"). Only the rules that can be stated without a human reading the chart are here;
the rest are listed in NOT_TESTED with the reason.

Each definition is one reading of his words. Thresholds marked # choice are our own
picks where he gave none; the backtest report shows them so they can be argued with.
"""
import numpy as np
import pandas as pd

RULES = {
    # buy points
    "BP1": "放量突破60日收盘新高后3-15天内缩量回踩突破位不破，当天放量阳线",
    "BP5": "连涨≥3天后第一次收跌，最低价碰到MA5或MA10，收盘不破",
    "BP6": "下跌/横盘中，前一天缩量阴线，当天放量大实体阳线看涨吞没",
    "BP7": "前一天缩量下跌收在20日收盘新低，当天放量锤子线",
    "BP8": "所在板块(等权)收盘创20日新高当天，个股放量大实体阳线突破20日高点",
    "BP9": "MA200之上、回撤未破斐波那契61.8，RSI6超卖(<20)+底背离+止跌形态",
    # naive versions without his qualifiers (to test whether the qualifiers add anything)
    "BP6_naive": "看涨吞没，不看成交量和位置",
    "BP7_naive": "锤子线，不看成交量和是否新低",
    # no-buy rules
    "NB1": "收盘价是近20日收盘新低",
    "NB3": "近3天内刚收盘跌破120日上行波段的斐波那契61.8",
    "NB4": "缩量反弹：收涨但量比前一天小且量能5日均线拐头向下",
    "NB6": "当天跌幅在所在板块(GICS)排名后10%",
    "NB11": "缩量新高：收盘创60日新高但量低于20日均量",
    "NB12": "悬空新高：3天涨≥10%且收盘创60日新高",
    "NB15": "日线RSI6 > 90",
    "NB16": "RSI6 > 80 且价格创20日新高但RSI6低于前期高点（顶背离）",
}
NOT_TESTED = {
    "BP2/BP3/BP4": "需要画趋势线、旗形、W底/头肩底颈线，自动识别误差大，留给人工标注的案例",
    "NB2/NB13/NB14": "需要他给的支撑/压力强弱区间（每周估值表里有，后面接上）",
    "NB5/NB8/NB9": "关于交易者自己（止损、刚止损、熟不熟），不是行情条件",
    "NB7/NB17": "需要财报日期和盘前新闻",
    "NB10": "小市值规则：样本本身全是大中盘，自动满足",
    "NB18": "开盘30分钟规则：需要分钟数据",
}
UP_RULES = {"NB11", "NB12", "NB15", "NB16"}   # judged against HIGH days; the rest against DIP days
FIB = 0.618
SWING = 120          # choice: window for the "up-structure" swing
MIN_SWING = 0.15     # choice: swing must be ≥15% to count as a structure


def rsi(close, n):
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def fib_level(high, low):
    """61.8% retracement level of the most recent up-swing within SWING days:
    H = highest high in the window, L = lowest low in the SWING days before H."""
    h, lo = high.to_numpy(), low.to_numpy()
    out = np.full(len(h), np.nan)
    for t in range(SWING * 2, len(h)):
        w = h[t - SWING + 1:t + 1]
        ih = t - SWING + 1 + int(np.argmax(w))
        L = lo[ih - SWING:ih + 1].min()
        H = h[ih]
        if H / L - 1 >= MIN_SWING:
            out[t] = H - FIB * (H - L)
    return pd.Series(out, index=high.index)


def features(g):
    """g: one ticker's rows sorted by date with open/high/low/close/volume."""
    g = g.copy()
    o, h, l, c, v = (g[k] for k in ("open", "high", "low", "close", "volume"))
    g["ret1"] = c.pct_change()
    g["vma5"] = v.rolling(5).mean()
    g["vma20"] = v.rolling(20).mean()
    for n in (5, 10, 20, 50, 200):
        g[f"ma{n}"] = c.rolling(n).mean()
    g["rsi6"], g["rsi24"] = rsi(c, 6), rsi(c, 24)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    g["atr14"] = tr.rolling(14).mean()
    body = (c - o).abs()
    rng = (h - l).replace(0, np.nan)
    g["body_frac"] = body / rng
    g["lower_sh"] = np.minimum(o, c) - l
    g["upper_sh"] = h - np.maximum(o, c)
    g["hammer"] = (g["lower_sh"] >= 2 * body) & (g["upper_sh"] <= 0.5 * body.clip(lower=0.001 * c)) & (body > 0)
    g["low20c"] = c <= c.shift(1).rolling(19).min()            # close is the lowest of the last 20 closes
    g["high60c"] = c >= c.shift(1).rolling(59).max()
    g["high20h"] = c > h.shift(1).rolling(20).max()
    g["high20c"] = c >= c.shift(1).rolling(19).max()            # close is the highest of the last 20 closes
    g["fib"] = fib_level(h, l)
    g["dd20"] = c / h.rolling(20).max() - 1                    # drawdown from 20-day high
    return g


def signals(g):
    o, h, l, c, v = (g[k] for k in ("open", "high", "low", "close", "volume"))
    up, dn = c > o, c < o
    s = pd.DataFrame(index=g.index)
    vol_up = v > v.shift(1)

    # BP1: breakout on volume, then low-volume pullback that holds, then first volume up-candle
    lvl = c.shift(1).rolling(60).max()
    bo = (c > lvl) & (v > 1.5 * g["vma20"])
    bo_lvl = lvl.where(bo)
    bo_day = pd.Series(np.where(bo, np.arange(len(g)), np.nan), index=g.index).ffill()
    since = np.arange(len(g)) - bo_day
    lvl_ff = bo_lvl.ffill()
    s["BP1"] = (since.between(3, 15) & (l <= lvl_ff * 1.03) & (c >= lvl_ff * 0.99)
                & up & vol_up & (v.shift(1) < g["vma20"]))
    # BP5
    ups = (c.diff() > 0)
    s["BP5"] = (ups.shift(1) & ups.shift(2) & ups.shift(3) & (c.diff() < 0)
                & (((l <= g["ma5"]) & (c >= g["ma5"])) | ((l <= g["ma10"]) & (c >= g["ma10"]))))
    # BP6
    engulf = up & dn.shift(1) & (c > o.shift(1)) & (o < c.shift(1)) & (g["body_frac"] >= 0.6)
    s["BP6_naive"] = engulf
    s["BP6"] = (engulf & (v.shift(1) < v.shift(2)) & vol_up
                & ((c < g["ma50"]) | (c.pct_change(20) < 0)))
    # BP7
    s["BP7_naive"] = g["hammer"]
    s["BP7"] = (g["hammer"] & (c.diff().shift(1) < 0) & g["low20c"].shift(1).astype(bool)
                & (v.shift(1) < v.shift(2)) & vol_up)
    # BP8 needs the sector flag; filled in by add_cross_section()
    s["BP8_stock"] = up & (g["body_frac"] >= 0.7) & (v >= 1.5 * g["vma20"]) & g["high20h"]
    # BP9
    oversold = g["rsi6"].rolling(4).min() < 20
    div = ((l.rolling(4).min() < l.shift(4).rolling(17).min())
           & (g["rsi6"].rolling(4).min() > g["rsi6"].shift(4).rolling(17).min()))
    s["BP9"] = ((c > g["ma200"]) & (c >= g["fib"]) & oversold & div & (g["hammer"] | engulf | (up & vol_up)))

    # no-buy
    s["NB1"] = g["low20c"]
    s["NB3"] = (c < g["fib"]) & (c.shift(1).rolling(3).max() >= g["fib"].shift(1))
    s["NB4"] = (c.diff() > 0) & (v < v.shift(1)) & (g["vma5"] < g["vma5"].shift(1))
    s["NB11"] = g["high60c"] & (v < g["vma20"])
    s["NB12"] = g["high60c"] & (c.pct_change(3) >= 0.10)
    s["NB15"] = g["rsi6"] > 90
    s["NB16"] = ((g["rsi6"] > 80) & (c >= c.shift(1).rolling(19).max())
                 & (g["rsi6"] < g["rsi6"].shift(1).rolling(19).max()))
    return s.fillna(False).astype(bool)


def add_cross_section(df):
    """NB6 (sector laggard) and BP8 (sector breakout) need all stocks on the same day."""
    st = df[df["sector"].isin(["ETF", "INDEX"]) == False]  # noqa: E712
    pct = st.groupby(["date", "sector"])["ret1"].rank(pct=True)
    df["NB6"] = False
    df.loc[st.index, "NB6"] = (pct <= 0.10).to_numpy()
    sec = st.groupby(["sector", "date"])["ret1"].mean().rename("sec_ret").reset_index()
    sec = sec.sort_values(["sector", "date"])
    sec["sec_idx"] = sec.groupby("sector")["sec_ret"].transform(lambda r: (1 + r.fillna(0)).cumprod())
    sec["sec_bo"] = sec.groupby("sector")["sec_idx"].transform(lambda x: x > x.shift(1).rolling(20).max())
    df = df.merge(sec[["sector", "date", "sec_bo"]], on=["sector", "date"], how="left")
    df["BP8"] = df["BP8_stock"] & df["sec_bo"].fillna(False).astype(bool)
    return df
