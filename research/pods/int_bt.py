"""Integrated long-only score (rules fixed in SPEC_INT.md before this was run). Research only.

Run from the history working copy:  python3 -W ignore research/pods/int_bt.py
"""
import sys, time
sys.path.insert(0, ".")
import numpy as np, pandas as pd
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
from alpha.bhav_panel import BhavMarket
from alpha.signal import pool_score
from alpha.scoring import zrank
from strategies import Strategy
from backtest import run, metrics, Config

t0 = time.time()
P = CouncilPanel(); M = BhavMarket(P); D = P.dates
c = pd.DataFrame(P.feat["close"], index=D).ffill(); r = c.pct_change()
dp = pd.DataFrame(P.feat["deliv_pct"], index=D)
CAP, START, OUT = 1_000_000, "2016-02-01", "research/pods/"
month_end = np.r_[D[1:].month != D[:-1].month, True]


def ingredients(lm=1.0):
    L = lambda n: int(round(n * lm))
    mom = (c.shift(21) / c.shift(L(252)) - 1).values
    lowv = -r.rolling(L(250), min_periods=int(L(250) * 0.8)).std().values
    deliv = dp.rolling(L(60), min_periods=int(L(60) * 0.6)).mean().values
    return {"mom": zrank(mom, P.mask), "lowvol": zrank(lowv, P.mask), "deliv": zrank(deliv, P.mask)}


def score(z, keys):
    return np.where(P.mask, sum(z[k] for k in keys) / len(keys), np.nan)


class Band(Strategy):          # same rule as round 1 / the primary
    def __init__(s, sc, k, band): s.sc, s.k, s.band = sc, k, band
    def reset(s, m): super().reset(m); s.hold = set()
    def decide(s, t, st):
        sc = s.sc[t]
        if not np.isfinite(sc).any(): return None
        w = np.array(st["weights"], float)
        order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf))); rank = {i: j for j, i in enumerate(order)}
        keep = {i for i in s.hold if rank[i] < s.band and np.isfinite(sc[i])}
        if len(keep) == len(s.hold) == s.k: return None
        slot = st["nav"] / s.k; px = np.nan_to_num(M.close.values[t])
        new = [i for i in order if i not in keep and np.isfinite(sc[i]) and 0 < px[i] <= slot][: s.k - len(keep)]
        out = np.zeros(len(sc))
        for i in keep: out[i] = w[i]
        rest = 1 - out.sum()
        for i in new: out[i] = max(rest, 0) / len(new)
        s.hold = keep | set(new); return out


class EW(Strategy):
    def decide(s, t, st):
        if not month_end[t] and getattr(s, "started", False): return None
        m = P.mask[t] & (np.nan_to_num(M.close.values[t]) > 0)
        if not m.any(): return None
        s.started = True; out = np.zeros(len(m)); out[m] = 1 / m.sum(); return out


def bt(strat, stress=False):
    return run(M, strat, Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01,
                                implicit_mult=2.0 if stress else 1.0))


PER = [("2016-19", "2016-02-01", "2019-12-31"), ("2020-21", "2020-01-01", "2021-12-31"),
       ("2022-26", "2022-01-01", None), ("all", START, None)]
rows, navs = [], {}
def rec(name, res, **kw):
    navs[name] = res.nav_post_tax
    for pn, a, b in PER:
        m = metrics(res.nav_post_tax, a, b)
        rows.append(dict(run=name, period=pn, **kw, **{k: round(v, 4) for k, v in m.items()}))
    m = metrics(res.nav_post_tax, START, None)
    print(f"{name}: CAGR {m['CAGR']:.3f} Sharpe {m['Sharpe']:.2f} MaxDD {m['MaxDD']:.3f}", round(time.time() - t0), "s", flush=True)

rec("equal-weight universe", bt(EW()), kind="bench")
rec("council (frozen)", bt(Band(np.where(P.mask, pool_score(P, "c_council_real"), np.nan), 20, 100)), kind="bench")
Z = {lm: ingredients(lm) for lm in (0.75, 1.0, 1.25)}
rec("trend pod", bt(Band(np.where(P.mask & np.isfinite((c.shift(21) / c.shift(252) - 1).values), (c.shift(21) / c.shift(252) - 1).values, np.nan), 20, 100)), kind="bench")
ALL = ("mom", "lowvol", "deliv")
for lm in (0.75, 1.0, 1.25):
    sc = score(Z[lm], ALL)
    for k in (15, 20, 25):
        rec(f"integrated k{k} L{lm}", bt(Band(sc, k, 5 * k)), kind="integrated", k=k, lmult=lm)
rec("integrated k20 L1.0 stress", bt(Band(score(Z[1.0], ALL), 20, 100), stress=True), kind="stress")
for keys in (("mom", "lowvol"), ("mom", "deliv"), ("lowvol", "deliv")):
    rec("diag " + "+".join(keys), bt(Band(score(Z[1.0], keys), 20, 100)), kind="diagnostic")

R = pd.DataFrame(rows); R.to_csv(OUT + "int_metrics.csv", index=False)
N = pd.DataFrame(navs); N.resample("ME").last().to_csv(OUT + "int_navs_monthly.csv")
Y = N.resample("YE").last(); Y = Y.pct_change().fillna(Y.iloc[0] / CAP - 1); Y.to_csv(OUT + "int_years.csv")
N.to_pickle("/tmp/int_navs.pkl"); print("done", round(time.time() - t0), "s")
