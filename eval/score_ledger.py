"""Score the decision ledger (data/ledger/*.json) against what prices did afterwards.

Writes eval/results/ledger_<date>.md and ledger_calls.csv / ledger_plans.csv.

Per stock call (reference = close on market_date):
  fwd/excess-vs-SPY at 20, 60, 120 trading days; grouped by action_today and stance.
  A useful signal ranks: add/buy > hold > wait > trim/sell/avoid.
  He repeats the same view day after day (NVDA "hold" 20 times in 5 months), so the tables use
  one row per episode: a call is a repeat when the same ticker got the same action (or stance)
  in a ledger at most REPEAT_DAYS calendar days earlier. Raw counts are kept in the CSV.
  Confidence intervals resample tickers, not rows (calls on one ticker move together).

Per buy plan (zone + confirmation), fill searched within WINDOW trading days after market_date:
    confirm == "none"            -> first day low <= zone_high; fill at min(open, zone_high)
    confirm == reversal/volume   -> first day after touch whose close is in [0.97*zone_low, zone_high*1.03]
                                    and close > open and close > prior close; fill at that close
    other                        -> treated like reversal (documented simplification)
    status == "filled_today"     -> filled at the reference close
  "Did waiting for his zone beat buying now?" is judged over the SAME window [ref, ref+k]:
    now  = buy at the reference close, hold to ref+k
    wait = cash until the fill (if it comes by ref+k), then hold to ref+k; no fill = cash throughout
  Cash is scored two ways: earning 0, or parked in SPY. Both are shown as excess vs SPY over the
  window, so wait - now is the value of waiting. Unfilled plans count (as cash), so a zone that
  is never reached costs the rally that was missed. Repeated plans (same ticker + zone within
  REPEAT_DAYS) count once.
Per invalidation: did a close cross it within 60 days, and what happened 20 days after?

usage: .venvs/quant/bin/python eval/score_ledger.py
"""
import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data/ledger"
MKT = ROOT / "data/market"
OUT = ROOT / "eval/results"
HZ = (20, 60, 120)
WINDOW = 60
REPEAT_DAYS = 30
BOOT = 2000
RNG = np.random.default_rng(0)


class Prices:
    def __init__(self):
        self.p = pd.read_parquet(MKT / "prices.parquet")
        self.cache = {t: g.set_index("date").sort_index() for t, g in self.p.groupby("ticker")}
        (MKT / "extra").mkdir(exist_ok=True)

    def get(self, t):
        t = t.upper().replace(".", "-")
        if t in self.cache:
            return self.cache[t]
        f = MKT / "extra" / f"{t}.parquet"
        if f.exists():
            g = pd.read_parquet(f)
        else:
            d = yf.download(t, start="2015-01-01", auto_adjust=True, progress=False)
            if d.empty:
                self.cache[t] = None
                return None
            d.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in d.columns]
            g = d[["open", "high", "low", "close", "volume"]]
            g.index.name = "date"
            g.to_parquet(f)
        self.cache[t] = g.sort_index()
        return self.cache[t]


def spy_ret(spy, d0, d1):
    return spy["close"].asof(d1) / spy["close"].asof(d0) - 1


def fwd(g, i, spy, k):
    if g is None or i + k >= len(g):
        return np.nan, np.nan
    r = g["close"].iat[i + k] / g["close"].iat[i] - 1
    return r, r - spy_ret(spy, g.index[i], g.index[i + k])


def ref_index(g, date):
    """Index of the last session on or before market_date."""
    if g is None:
        return None
    i = g.index.searchsorted(pd.Timestamp(date), side="right") - 1
    return i if i >= 0 else None


def fill_plan(g, i0, plan):
    if plan.get("status") == "filled_today":
        return i0, g["close"].iat[i0], "filled today"
    lo, hi = plan.get("zone_low"), plan.get("zone_high")
    if lo is None or hi is None:
        return None, None, "no zone"
    lo, hi = min(lo, hi), max(lo, hi)
    o, h, l, c = (g[k].to_numpy() for k in ("open", "high", "low", "close"))
    end = min(len(g) - 1, i0 + WINDOW)
    touched = None
    for j in range(i0 + 1, end + 1):
        if l[j] <= hi:
            touched = j
            break
    if touched is None:
        return None, None, "not touched"
    if plan.get("confirm", "none") == "none":
        return touched, min(o[touched], hi), "filled limit"
    for j in range(touched, end + 1):
        if 0.97 * lo <= c[j] <= 1.03 * hi and c[j] > o[j] and c[j] > c[j - 1]:
            return j, c[j], "filled confirmed"
    return None, None, "touched, no confirmation"


def wait_vs_now(g, spy, i0, j, px, k):
    """Excess vs SPY over [i0, i0+k] for: buy now, wait (cash=0), wait (cash in SPY); filled by i0+k?"""
    e = i0 + k
    if e >= len(g):
        return np.nan, np.nan, np.nan, np.nan
    d0, de = g.index[i0], g.index[e]
    s_all = spy_ret(spy, d0, de)
    now = g["close"].iat[e] / g["close"].iat[i0] - 1
    if j is not None and j <= e:
        pos = g["close"].iat[e] / px - 1
        w0 = pos
        ws = (1 + spy_ret(spy, d0, g.index[j])) * (1 + pos) - 1
        filled = 1.0
    else:
        w0, ws, filled = 0.0, s_all, 0.0
    return now - s_all, w0 - s_all, ws - s_all, filled


def mark_repeats(df, key, days=REPEAT_DAYS):
    """True when the same key appeared at most `days` calendar days before (chains through daily repeats)."""
    last, out = {}, []
    for _, r in df.iterrows():
        k = tuple(r[c] for c in key)
        d = pd.Timestamp(r["date"])
        out.append(k in last and (d - last[k]).days <= days)
        last[k] = d
    return pd.Series(out, index=df.index)


def cluster_ci(df, col, by="ticker", q=(5, 95)):
    """Percentile CI of the pooled mean of `col`, resampling whole tickers."""
    d = df[[by, col]].dropna()
    if d[by].nunique() < 3:
        return np.nan, np.nan
    grp = d.groupby(by)[col].agg(["sum", "count"])
    s, c = grp["sum"].to_numpy(), grp["count"].to_numpy()
    idx = RNG.integers(0, len(grp), size=(BOOT, len(grp)))
    means = s[idx].sum(1) / c[idx].sum(1)
    return tuple(np.percentile(means, q))


def fmt_ci(lo, hi):
    return "" if np.isnan(lo) else f"[{lo*100:+.1f}, {hi*100:+.1f}]"


def agg(C, by):
    rows = []
    for name, s in C.groupby(by):
        r = {by: name, "n": len(s), "tickers": s["ticker"].nunique()}
        for k in HZ:
            x = s[f"x{k}"].dropna()
            r[f"n_{k}"] = len(x)
            r[f"x{k}"] = x.mean() * 100 if len(x) else np.nan
            r[f"beat{k}"] = (x > 0).mean() * 100 if len(x) else np.nan
        r["x60 90% CI"] = fmt_ci(*cluster_ci(s, "x60"))
        rows.append(r)
    return pd.DataFrame(rows).round(1)


def main():
    OUT.mkdir(exist_ok=True)
    P = Prices()
    spy = P.get("SPY")
    calls, plans = [], []
    files = sorted(f for f in LEDGER.glob("*.json") if not f.name.startswith("_"))
    for f in files:
        L = json.load(open(f))
        md = L.get("market_date") or L.get("upload_date")
        for s in L.get("stocks", []):
            g = P.get(s["ticker"])
            i0 = ref_index(g, md)
            row = {"video": L["video_id"], "date": md, "ticker": s["ticker"], "holder": s.get("holder"),
                   "stance": s.get("stance"), "action": s.get("action_today"), "size": s.get("size_pct"),
                   "val_label": (s.get("valuation") or {}).get("label"), "rules": ",".join(s.get("rules_cited") or [])}
            if i0 is not None:
                row["ref_close"] = g["close"].iat[i0]
                for k in HZ:
                    row[f"r{k}"], row[f"x{k}"] = fwd(g, i0, spy, k)
                inv = s.get("invalidation") or {}
                if inv.get("price"):
                    seg = g["close"].iloc[i0 + 1:i0 + 1 + WINDOW]
                    below = inv["price"] < row["ref_close"]
                    hit = seg[seg < inv["price"]] if below else seg[seg > inv["price"]]
                    row["inv_hit"] = len(hit) > 0
                    if len(hit):
                        j = g.index.get_loc(hit.index[0])
                        row["inv_r20_after"], row["inv_x20_after"] = fwd(g, j, spy, 20)
            calls.append(row)
            for p in s.get("plans") or []:
                if p.get("side") != "buy" or i0 is None or p.get("status") == "cancelled":
                    continue
                j, px, status = fill_plan(g, i0, p)
                pr = {"video": L["video_id"], "date": md, "ticker": s["ticker"], "zone_low": p.get("zone_low"),
                      "zone_high": p.get("zone_high"), "confirm": p.get("confirm"), "plan_status": p.get("status"),
                      "size": p.get("size_pct"), "status": status, "ref_close": g["close"].iat[i0]}
                if j is not None:
                    pr["fill_date"] = g.index[j].date().isoformat()
                    pr["fill_px"] = px
                    pr["discount"] = px / pr["ref_close"] - 1
                for k in HZ:
                    pr[f"now_x{k}"], pr[f"wait0_x{k}"], pr[f"waitS_x{k}"], pr[f"filled{k}"] = \
                        wait_vs_now(g, spy, i0, j, px, k)
                plans.append(pr)
    C = pd.DataFrame(calls).sort_values("date", kind="stable").reset_index(drop=True)
    Pl = pd.DataFrame(plans).sort_values("date", kind="stable").reset_index(drop=True)
    if len(C):
        C["repeat_action"] = mark_repeats(C, ["ticker", "action"])
        C["repeat_stance"] = mark_repeats(C, ["ticker", "stance"])
    if len(Pl):
        Pl["zk"] = Pl["zone_low"].round(1).astype(str) + "-" + Pl["zone_high"].round(1).astype(str)
        Pl["repeat"] = mark_repeats(Pl, ["ticker", "zk", "confirm"])
        Pl = Pl.drop(columns="zk")
    C.to_csv(OUT / "ledger_calls.csv", index=False)
    Pl.to_csv(OUT / "ledger_plans.csv", index=False)

    stamp = dt.date.today().isoformat()
    lines = [f"# Decision ledger score {stamp}", "",
             f"{len(files)} videos, market dates {C['date'].min()} to {C['date'].max()}. "
             f"{len(C)} stock calls on {C['ticker'].nunique()} tickers, {len(Pl)} buy plans.", "",
             "- x = mean excess return vs SPY (%), beat = % of calls that beat SPY, n_k = calls with a full k-day window.",
             f"- One row per episode: a call repeating the same ticker + action (or stance) within {REPEAT_DAYS} days "
             "is dropped.",
             "- 90% CI resamples whole tickers, so a view repeated on one stock is not counted as independent "
             "evidence.", ""]
    if len(C):
        ca, cs = C[~C["repeat_action"]], C[~C["repeat_stance"]]
        lines += [f"## By action ({len(ca)} episodes of {len(C)} calls)", "",
                  agg(ca, "action").to_markdown(index=False), "",
                  f"## By stance ({len(cs)} episodes of {len(C)} calls)", "",
                  agg(cs, "stance").to_markdown(index=False), ""]
        b, r = cs[cs["stance"] == "bull"], cs[cs["stance"] == "bear"]
        if len(b) and len(r):
            diffs = []
            for _ in range(BOOT):
                tb = RNG.choice(b["ticker"].unique(), b["ticker"].nunique())
                tr = RNG.choice(r["ticker"].unique(), r["ticker"].nunique())
                xb = pd.concat([b.loc[b["ticker"] == t, "x60"] for t in tb]).mean()
                xr = pd.concat([r.loc[r["ticker"] == t, "x60"] for t in tr]).mean()
                diffs.append(xb - xr)
            lo, hi = np.nanpercentile(diffs, [5, 95])
            lines += [f"Bull minus bear, 60-day excess: {(b['x60'].mean() - r['x60'].mean())*100:+.1f} points, "
                      f"90% CI [{lo*100:+.1f}, {hi*100:+.1f}].", ""]
        if "inv_hit" in C:
            iv = C[C["inv_hit"].notna() & ~C["repeat_stance"]]
            lines += ["## Invalidation levels", "",
                      f"{len(iv)} episodes had one; crossed within {WINDOW} days: {iv['inv_hit'].mean()*100:.0f}%; "
                      f"mean excess 20d after crossing: {iv['inv_x20_after'].mean()*100:.2f}%", ""]
    if len(Pl):
        U = Pl[~Pl["repeat"]]
        st = U.groupby("status").size().rename("n").reset_index()
        lines += [f"## Buy plans ({len(U)} distinct of {len(Pl)})", "",
                  f"Fill searched within {WINDOW} trading days.", "", st.to_markdown(index=False), ""]
        rows = []
        for k in HZ:
            d = U[U[f"now_x{k}"].notna()].copy()
            if not len(d):
                continue
            d["d0"] = d[f"wait0_x{k}"] - d[f"now_x{k}"]
            d["dS"] = d[f"waitS_x{k}"] - d[f"now_x{k}"]
            rows.append({"horizon": k, "plans": len(d), "tickers": d["ticker"].nunique(),
                         "filled by then %": d[f"filled{k}"].mean() * 100,
                         "buy now": d[f"now_x{k}"].mean() * 100,
                         "wait, cash 0": d[f"wait0_x{k}"].mean() * 100,
                         "wait, cash in SPY": d[f"waitS_x{k}"].mean() * 100,
                         "wait - now (cash 0)": d["d0"].mean() * 100,
                         "90% CI": fmt_ci(*cluster_ci(d, "d0")),
                         "wait - now (cash in SPY)": d["dS"].mean() * 100,
                         "90% CI ": fmt_ci(*cluster_ci(d, "dS"))})
        lines += ["### Waiting for his zone vs buying at the reference close",
                  "Same window for both: from the reference close to k trading days later. Excess vs SPY, %. "
                  "Unfilled plans sit in cash.", "",
                  pd.DataFrame(rows).round(2).to_markdown(index=False), ""]
        f_ = U[U["fill_px"].notna()] if "fill_px" in U else U.iloc[0:0]
        if len(f_):
            lines += [f"Median fill price vs reference close: {f_['discount'].median()*100:+.1f}%", ""]
            by = []
            for s_, d in U.groupby(U["confirm"].fillna("none")):
                d = d[d["now_x60"].notna()]
                if len(d):
                    by.append({"confirm": s_, "plans": len(d), "filled %": d["filled60"].mean() * 100,
                               "wait - now 60d (cash 0)": (d["wait0_x60"] - d["now_x60"]).mean() * 100})
            lines += ["By confirmation type (60 days):", "", pd.DataFrame(by).round(2).to_markdown(index=False), ""]
    (OUT / f"ledger_{stamp}.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
