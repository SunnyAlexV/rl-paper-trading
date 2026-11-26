"""Round 1 of the philosophy pods (rules fixed in SPEC.md before this was run).

Run from the history working copy (see README.md):  python3 -W ignore research/pods/pods_bt.py
Writes research/pods/round1_*.csv. Research only.
"""
import sys, time
sys.path.insert(0, ".")
import numpy as np, pandas as pd
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
from alpha.bhav_panel import BhavMarket, build
from alpha.signal import pool_score
from strategies import Strategy
from backtest import run, metrics, Config

t0 = time.time()
P = CouncilPanel(); M = BhavMarket(P); B = build()
dates = P.dates
c = pd.DataFrame(P.feat["close"], index=dates).ffill()
r = c.pct_change()
tv = B["tv"].reindex(index=dates, columns=P.names).rolling(60, min_periods=40).median().values
CAP, START = 1_000_000, "2016-02-01"
OUT = "research/pods/"


def masked(x): return np.where(P.mask & np.isfinite(x), x, np.nan)


def trend(L=252):           # 12-1 momentum; L scales the long lookback
    return masked((c.shift(21) / c.shift(L) - 1).values)


def contrarian(L=21, top=200):   # lowest L-day return among the `top` most liquid
    liq = np.where(P.mask, tv, np.nan)
    rk = pd.DataFrame(liq).rank(axis=1, ascending=False).values
    return np.where(rk <= top, masked(-(c / c.shift(L) - 1).values), np.nan)


def defensive(L=250):       # lowest L-day volatility
    return masked(-r.rolling(L, min_periods=int(L * 0.8)).std().values)


week_end = np.r_[dates[1:].isocalendar().week.values != dates[:-1].isocalendar().week.values, True]
month_end = np.r_[dates[1:].month != dates[:-1].month, True]


class Band(Strategy):
    """Hold k; sell when a holding leaves the top `band`; new names share freed weight equally,
    capped at max weight by the engine. Decides only on `when` days (None = daily)."""
    def __init__(s, sc, k, band, when=None): s.sc, s.k, s.band, s.when = sc, k, band, when
    def reset(s, m): super().reset(m); s.hold = set()
    def decide(s, t, st):
        if s.when is not None and not s.when[t] and s.hold: return None
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


PER = [("2016-19", "2016-02-01", "2019-12-31"), ("2020-21", "2020-01-01", "2021-12-31"),
       ("2022-26", "2022-01-01", None), ("all", START, None)]
POD = {  # name: (signal fn, default lookback, band multiple of k, decision days)
    "trend": (trend, 252, 5, None),
    "contrarian": (contrarian, 21, 3, week_end),
    "defensive": (defensive, 250, 5, month_end),
}


def bt(strat, stress=False):
    return run(M, strat, Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01,
                                implicit_mult=2.0 if stress else 1.0))


rows, navs = [], {}
def record(name, res, extra):
    navs[name] = res.nav_post_tax
    for pn, a, b in PER:
        m = metrics(res.nav_post_tax, a, b)
        rows.append(dict(run=name, period=pn, **extra, **{k: round(v, 4) for k, v in m.items()}))

record("equal-weight universe", bt(EW()), dict(pod="benchmark", k=None, lmult=None, stress=False))
record("null control", bt(Band(np.where(P.mask, pool_score(P, "c_council_null"), np.nan), 20, 100)),
       dict(pod="benchmark", k=None, lmult=None, stress=False))
record("council (frozen)", bt(Band(np.where(P.mask, pool_score(P, "c_council_real"), np.nan), 20, 100)),
       dict(pod="benchmark", k=None, lmult=None, stress=False))
print("benchmarks", round(time.time() - t0), "s", flush=True)
for pod, (fn, L, bm, when) in POD.items():
    for lm in (0.75, 1.0, 1.25):
        sc = fn(int(round(L * lm)))
        for k in (15, 20, 25):
            name = f"{pod} k{k} L{lm}"
            record(name, bt(Band(sc, k, bm * k, when)), dict(pod=pod, k=k, lmult=lm, stress=False))
            if k == 20 and lm == 1.0:
                record(f"{pod} k20 L1.0 stress", bt(Band(sc, k, bm * k, when), stress=True),
                       dict(pod=pod, k=k, lmult=lm, stress=True))
    print(pod, "done", round(time.time() - t0), "s", flush=True)

R = pd.DataFrame(rows); R.to_csv(OUT + "round1_metrics.csv", index=False)
N = pd.DataFrame(navs); N.resample("ME").last().to_csv(OUT + "round1_navs_monthly.csv")
Y = N.resample("YE").last(); Y = Y.pct_change().fillna(Y.iloc[0] / CAP - 1)
Y.to_csv(OUT + "round1_years.csv")
D = N.pct_change().dropna(); D.to_pickle("/tmp/pods_daily.pkl")
print("done", round(time.time() - t0), "s")
