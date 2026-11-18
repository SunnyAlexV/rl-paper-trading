"""Frozen band rule (council signal) vs plain 12-1 momentum, same universe, same band rule, same
cost/tax engine. NSE 2015-2026 data rebuilt from NSE archives (research copy, not the trading repo).
Council weights were fitted on 2013-19, so 2016-19 is in-sample for the council; 2020-21 is its
validation period and 2022-26 its test period."""
import sys, time, json
sys.path.insert(0, ".")
import numpy as np, pandas as pd
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
from alpha.bhav_panel import BhavMarket
from alpha.signal import pool_score
from strategies import Strategy
from backtest import run, metrics, Config

t0 = time.time()
P = CouncilPanel(); M = BhavMarket(P)
print("panel", P.dates[0].date(), P.dates[-1].date(), len(P.dates), len(P.names), round(time.time() - t0), "s", flush=True)
c = pd.DataFrame(P.feat["close"], index=P.dates).ffill()
mom = (c.shift(21) / c.shift(252) - 1).values
SC = {"council (frozen)": np.where(P.mask, pool_score(P, "c_council_real"), np.nan),
      "null control": np.where(P.mask, pool_score(P, "c_council_null"), np.nan),
      "momentum 12-1": np.where(P.mask & np.isfinite(mom), mom, np.nan)}
print("signals", round(time.time() - t0), "s", flush=True)


class Band(Strategy):          # copied from research/fleet/fleet_bt.py (same rule as the primary)
    def __init__(s, sc, k, band): s.sc, s.k, s.band = sc, k, band
    def reset(s, m): super().reset(m); s.hold = set()
    def decide(s, t, st):
        sc = s.sc[t]
        if not np.isfinite(sc).any(): return None
        w = np.array(st["weights"], float)
        order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf))); rank = {i: j for j, i in enumerate(order)}
        keep = {i for i in s.hold if rank[i] < s.band}
        if len(keep) == len(s.hold) == s.k: return None
        slot = st["nav"] / s.k; px = np.nan_to_num(M.close.values[t])
        new = [i for i in order if i not in keep and np.isfinite(sc[i]) and 0 < px[i] <= slot][: s.k - len(keep)]
        out = np.zeros(len(sc))
        for i in keep: out[i] = w[i]
        rest = 1 - out.sum()
        for i in new: out[i] = max(rest, 0) / len(new)
        s.hold = keep | set(new); return out


class EqualWeightUniverse(Strategy):   # monthly equal weight in every tradable universe member
    def decide(s, t, st):
        if t > 0 and P.dates[t].month == P.dates[t - 1].month and getattr(s, "started", False): return None
        m = P.mask[t] & (np.nan_to_num(M.close.values[t]) > 0)
        if not m.any(): return None
        s.started = True; out = np.zeros(len(m)); out[m] = 1 / m.sum(); return out


START = "2016-02-01"
PER = [("2016-19", "2016-02-01", "2019-12-31"), ("2020-21", "2020-01-01", "2021-12-31"),
       ("2022-26", "2022-01-01", None), ("all", START, None)]
runs = [(k, Band(v, 20, 100), 0.01) for k, v in SC.items()] + [("equal-weight universe", EqualWeightUniverse(), 0.01)]
navs, rows = {}, []
for cap in (100000,):
    for name, strat, mtf in runs:
        t1 = time.time()
        r = run(M, strat, Config(capital=cap, start=START, max_weight=0.25, min_trade_frac=mtf))
        navs[name] = r.nav_post_tax
        for pn, a, b in PER:
            m = metrics(r.nav_post_tax, a, b)
            rows.append(dict(strategy=name, period=pn, **{k: round(v, 3) for k, v in m.items()}))
        cst = sum(r.costs.values()) if isinstance(r.costs, dict) else np.nan
        print(name, "done", round(time.time() - t1), "s; costs Rs", round(cst), "trades", r.trades, "turnover", round(r.turnover, 2), flush=True)
pd.DataFrame(navs).to_csv("navs.csv")
R = pd.DataFrame(rows); R.to_csv("compare.csv", index=False)
print(R.pivot_table(index="strategy", columns="period", values=["CAGR", "Sharpe", "MaxDD"]).round(3).to_string())
# Year-by-year
Y = pd.DataFrame(navs).resample("YE").last().pct_change()
Y.iloc[0] = pd.DataFrame(navs).resample("YE").last().iloc[0] / 100000 - 1
print((Y * 100).round(1).to_string())
