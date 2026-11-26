"""Backtest Rhino's mechanical rules on daily prices. Writes eval/results/rules_<date>.md + .csv.

What is measured for every stock-day that a rule fires (entry at that day's close):
  - fwd5/20/60: return over the next 5/20/60 trading days, minus SPY over the same days ("excess")
  - RR1 win rate: stop = 2 x ATR14 below entry, target = same distance above; within 20 days,
    which is hit first (same-day both = stop, conservative). This is his "1:1 R:R, ~65% win rate" claim.
  - RR1p (buy points only): stop under the signal day's low (pattern stop), target 1:1.
Comparisons: every rule vs ALL stock-days and vs DIP days (down >=8% from 20-day high: the
situations where no-buy rules are supposed to filter). Samples overlap and stocks move
together, so t-stats use one mean per date (still optimistic because 20-day windows overlap).

usage: .venvs/quant/bin/python eval/backtest.py
"""
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

import rules

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "eval/results"
H = 20
PERIODS = [("2008-2012", "2008", "2012"), ("2013-2019", "2013", "2019"), ("2020-2026", "2020", "2026")]


def outcomes(g):
    c, h, l = g["close"].to_numpy(), g["high"].to_numpy(), g["low"].to_numpy()
    n = len(c)
    for k in (5, 20, 60):
        g[f"fwd{k}"] = pd.Series(c).shift(-k).to_numpy() / c - 1
    idx = np.arange(n)[:, None] + np.arange(1, H + 1)[None, :]
    valid = idx < n
    idx = np.minimum(idx, n - 1)
    fh, fl = np.where(valid, h[idx], np.nan), np.where(valid, l[idx], np.nan)

    def rr(stop_dist):
        tgt, stp = c + stop_dist, c - stop_dist
        hit_t = fh >= tgt[:, None]
        hit_s = fl <= stp[:, None]
        ft = np.where(hit_t.any(1), hit_t.argmax(1), H + 1)
        fs = np.where(hit_s.any(1), hit_s.argmax(1), H + 1)
        res = np.where(fs <= ft, np.where(fs <= H, -1.0, 0.0), 1.0)   # 1 win, -1 loss, 0 neither
        res[~valid[:, -1]] = np.nan
        return res
    g["rr_atr"] = rr(2 * g["atr14"].to_numpy())
    pstop = np.maximum(c - np.minimum(l, pd.Series(l).shift(1).to_numpy()), 0.005 * c)
    g["rr_pat"] = rr(pstop)
    g["pat_risk"] = pstop / c
    return g


def load():
    p = pd.read_parquet(ROOT / "data/market/prices.parquet")
    u = pd.read_csv(ROOT / "data/market/universe.csv")
    p = p.merge(u, on="ticker").sort_values(["ticker", "date"])
    spy = p[p.ticker == "SPY"].set_index("date")["close"]
    parts = []
    for t, g in p.groupby("ticker", sort=False):
        if g["sector"].iat[0] in ("ETF", "INDEX") or len(g) < 300:
            continue
        g = rules.features(g.reset_index(drop=True))
        g = pd.concat([g, rules.signals(g)], axis=1)
        parts.append(outcomes(g))
    df = pd.concat(parts, ignore_index=True)
    sp = spy.reindex(df["date"]).to_numpy()
    for k in (5, 20, 60):
        sf = (spy.shift(-k) / spy - 1).reindex(df["date"]).to_numpy()
        df[f"x{k}"] = df[f"fwd{k}"] - sf
    df = rules.add_cross_section(df)
    liquid = (df["close"] >= 5) & (df["close"] * df["vma20"] >= 20e6) & df["ma200"].notna()
    return df[liquid & df["x20"].notna()].copy()


def stats(d, name):
    if len(d) == 0:
        return {"rule": name, "n": 0}
    per_date = d.groupby("date")["x20"].mean()
    t = per_date.mean() / (per_date.std(ddof=1) / np.sqrt(len(per_date))) if len(per_date) > 2 else np.nan
    rr = d["rr_atr"].dropna()
    rp = d["rr_pat"].dropna()
    return {
        "rule": name, "n": len(d), "dates": d["date"].nunique(),
        "x5": d["x5"].mean() * 100, "x20": d["x20"].mean() * 100, "x60": d["x60"].mean() * 100,
        "up20": (d["fwd20"] > 0).mean() * 100, "beat20": (d["x20"] > 0).mean() * 100,
        "rr_win": (rr == 1).mean() * 100, "rr_loss": (rr == -1).mean() * 100,
        "rrp_win": (rp == 1).mean() * 100, "rrp_loss": (rp == -1).mean() * 100,
        "pat_risk": d["pat_risk"].median() * 100, "t_x20": t,
    }


def table(rows):
    df = pd.DataFrame(rows)
    cols = ["rule", "n", "dates", "x5", "x20", "x60", "up20", "beat20", "rr_win", "rr_loss",
            "rrp_win", "pat_risk", "t_x20"]
    df = df[[c for c in cols if c in df]]
    return df.round(2)


def md(df):
    return df.to_markdown(index=False) if hasattr(df, "to_markdown") else df.to_string(index=False)


def main():
    OUT.mkdir(exist_ok=True)
    df = load()
    df["DIP"] = df["dd20"] <= -0.08
    nb = [k for k in rules.RULES if k.startswith("NB")]
    bp = [k for k in rules.RULES if k.startswith("BP")]
    df["NB_any"] = df[nb].any(axis=1)
    df["HIGH"] = df["high20c"]
    ctx = {r: ("HIGH" if r in rules.UP_RULES else "DIP") for r in nb}

    sections = []
    base = [stats(df, "ALL stock-days"), stats(df[df.DIP], "DIP (≥8% off 20d high)")]
    sections.append(("Baselines", table(base)))

    rows = base[:]
    for r in bp:
        rows.append(stats(df[df[r]], r))
        if not r.endswith("naive"):
            rows.append(stats(df[df[r] & ~df.NB_any], f"{r} + passes no-buy"))
            rows.append(stats(df[df[r] & df.NB_any], f"{r} but hits a no-buy"))
    sections.append(("Buy points", table(rows)))

    rows = [stats(df[df.DIP], "DIP all"), stats(df[df.DIP & ~df.NB_any], "DIP passes all no-buy"),
            stats(df[df.DIP & df.NB_any], "DIP hits ≥1 no-buy")]
    rows.append(stats(df[df.HIGH], "HIGH all (close at 20d high)"))
    for r in nb:
        c = ctx[r]
        rows.append(stats(df[df[c] & df[r]], f"{r} within {c}"))
        rows.append(stats(df[df[c] & ~df[r]], f"not {r} within {c}"))
    sections.append(("No-buy rules (a rule works if 'NBx within …' is worse than 'not NBx within …')", table(rows)))

    # one line per rule and period: flagged minus not-flagged, same context. Negative x = rule helps.
    rows = []
    for r in nb:
        c = ctx[r]
        for label, a, b in [("all", "2008", "2026")] + PERIODS:
            d = df[(df["date"] >= a) & (df["date"] <= f"{b}-12-31") & df[c]]
            f, nf = d[d[r]], d[~d[r]]
            rows.append({"rule": r, "context": c, "period": label, "n_flag": len(f),
                         "dx5": (f.x5.mean() - nf.x5.mean()) * 100, "dx20": (f.x20.mean() - nf.x20.mean()) * 100,
                         "dx60": (f.x60.mean() - nf.x60.mean()) * 100,
                         "d_up20": ((f.fwd20 > 0).mean() - (nf.fwd20 > 0).mean()) * 100})
    sections.append(("No-buy rules by period: flagged minus not flagged (negative = the rule avoids worse trades)",
                     pd.DataFrame(rows).round(2)))

    for label, a, b in PERIODS:
        m = (df["date"] >= a) & (df["date"] <= f"{b}-12-31")
        d = df[m]
        rows = [stats(d, "ALL"), stats(d[d.DIP], "DIP"), stats(d[d.DIP & ~d.NB_any], "DIP passes no-buy")]
        rows += [stats(d[d[r]], r) for r in bp if not r.endswith("naive")]
        sections.append((f"Period {label}", table(rows)))

    stamp = dt.date.today().isoformat()
    lines = [f"# Rule backtest {stamp}", "",
             f"Universe: {df.ticker.nunique()} stocks (today's S&P 500 + extras; survivorship bias), "
             f"{df.date.min():%Y-%m-%d} to {df.date.max():%Y-%m-%d}, price ≥ $5, $20M+ daily volume.",
             "Columns: x5/x20/x60 = mean excess return vs SPY (%) over 5/20/60 days; up20 = % with positive "
             "20-day return; beat20 = % beating SPY; rr_win/rr_loss = % hitting a 1:1 target/stop first within "
             "20 days with a 2×ATR stop (rest: neither); rrp_win = same with the stop under the signal-day low; "
             "pat_risk = median size of that pattern stop (%); t_x20 = t-stat of x20 using one mean per date.",
             "", "## Rules tested", ""]
    lines += [f"- **{k}**: {v}" for k, v in rules.RULES.items()]
    lines += ["", "Not tested: " + "; ".join(f"{k} ({v})" for k, v in rules.NOT_TESTED.items()), ""]
    all_csv = []
    for title, t in sections:
        lines += [f"## {title}", "", md(t), ""]
        all_csv.append(t.assign(section=title))
    (OUT / f"rules_{stamp}.md").write_text("\n".join(lines))
    pd.concat(all_csv).to_csv(OUT / f"rules_{stamp}.csv", index=False)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
