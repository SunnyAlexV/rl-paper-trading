import sys, json, time
sys.path.insert(0, "."); 
import numpy as np, pandas as pd
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
from alpha.bhav_panel import BhavMarket
from alpha.signal import pool_score
from strategies import Strategy
from backtest import run, metrics, Config
P = CouncilPanel(); M = BhavMarket(P)
print("dates", P.dates[0].date(), P.dates[-1].date(), len(P.dates), flush=True)
SC = {p: np.where(P.mask, pool_score(P, p), np.nan) for p in ("c_council_real", "c_council_null")}
class Band(Strategy):
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
class Daily(Strategy):   # every day: equal weight in today's top k (buyable), no band
    def __init__(s, sc, k): s.sc, s.k = sc, k
    def decide(s, t, st):
        sc = s.sc[t]
        if not np.isfinite(sc).any(): return None
        slot = st["nav"] / s.k; px = np.nan_to_num(M.close.values[t])
        order = [i for i in np.argsort(-np.where(np.isfinite(sc), sc, -np.inf)) if np.isfinite(sc[i]) and 0 < px[i] <= slot][: s.k]
        out = np.zeros(len(sc)); out[order] = 1 / s.k; return out
# warm-up: signals need ~150 days of history
start = str(P.dates[min(160, len(P.dates)-1)].date())
V = [("frozen 20/100", Band(SC["c_council_real"], 20, 100), 0.01),
     ("low-turnover 15/150", Band(SC["c_council_real"], 15, 150), 0.01),
     ("high-turnover 25/60", Band(SC["c_council_real"], 25, 60), 0.01),
     ("daily top-20, no band", Daily(SC["c_council_real"], 20), 0.0),
     ("null control 20/100", Band(SC["c_council_null"], 20, 100), 0.01)]
rows = []
for cap in (100000, 1000000):
    for name, strat, mtf in V:
        t0 = time.time()
        r = run(M, strat, Config(capital=cap, start=start, max_weight=0.25, min_trade_frac=mtf))
        m = metrics(r.nav_post_tax)
        tot = r.nav_post_tax.iloc[-1] / r.nav_post_tax.iloc[0] - 1
        rows.append(dict(variant=name, capital=cap, total_ret=tot, **m, trades=r.trades, costs=sum(r.costs.values()) if isinstance(r.costs, dict) else None))
        print(rows[-1], round(time.time()-t0), "s", flush=True)
pd.DataFrame(rows).to_csv(sys.argv[1], index=False)
print("start", start)
