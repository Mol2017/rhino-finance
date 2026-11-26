"""Daily OHLCV for the test universe -> data/market/prices.parquet, universe.csv.

Universe: today's S&P 500 + Nasdaq-100 (Wikipedia) + the tickers Rhino covers most that are in
neither (e.g. TSM, ASML). NOTE: today's members only -> survivorship bias (stocks that
dropped out are missing), which flatters long-only results; compare signals with each other
and with each stock's own base rate, not with zero.
usage: .venvs/quant/bin/python eval/fetch_prices.py [--start 2008-01-01]
"""
import argparse
import io
import urllib.request
from pathlib import Path

import pandas as pd
import yfinance as yf

OUT = Path(__file__).resolve().parent.parent / "data/market"
EXTRA = {"TSM": "Information Technology", "ASML": "Information Technology", "ARM": "Information Technology",
         "SHOP": "Information Technology", "NIO": "Consumer Discretionary", "BABA": "Consumer Discretionary",
         "SNOW": "Information Technology", "NET": "Information Technology", "MU": "Information Technology",
         "SPY": "ETF", "QQQ": "ETF", "SOXX": "ETF", "SMH": "ETF", "^VIX": "INDEX", "^TNX": "INDEX"}


def wiki(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research script)"})
    return pd.read_html(io.StringIO(urllib.request.urlopen(req, timeout=30).read().decode()))


def universe():
    sp = wiki("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]
    u = dict(zip(sp["Symbol"], sp["GICS Sector"]))
    for t in wiki("https://en.wikipedia.org/wiki/Nasdaq-100"):
        if "Ticker" in t.columns and len(t) > 90:
            sec = "GICS Sector" if "GICS Sector" in t.columns else None
            for _, r in t.iterrows():
                u.setdefault(r["Ticker"], r[sec] if sec else "Unknown")
            break
    for k, v in EXTRA.items():
        u.setdefault(k, v)
    df = pd.DataFrame({"ticker": [k.replace(".", "-") for k in u], "sector": list(u.values())})
    return df.drop_duplicates("ticker")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2008-01-01")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    uni = universe()
    uni.to_csv(OUT / "universe.csv", index=False)
    print("universe", len(uni))
    frames = []
    tick = list(uni["ticker"])
    for i in range(0, len(tick), 100):
        d = yf.download(tick[i:i + 100], start=a.start, auto_adjust=True, progress=False,
                        group_by="ticker", threads=True)
        for t in tick[i:i + 100]:
            if t not in d.columns.get_level_values(0):
                continue
            x = d[t].dropna(subset=["Close"])
            if len(x):
                x = x.assign(ticker=t)
                frames.append(x)
        print("batch", i, flush=True)
    p = pd.concat(frames).reset_index().rename(columns=str.lower)
    p = p[["date", "ticker", "open", "high", "low", "close", "volume"]]
    p.to_parquet(OUT / "prices.parquet", index=False)
    print(p.groupby("ticker").size().describe(), p["date"].min(), p["date"].max())


if __name__ == "__main__":
    main()
