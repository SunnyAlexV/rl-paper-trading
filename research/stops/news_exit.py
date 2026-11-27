"""Bad-news exit (rules in SPEC_NEWS.md). Run from the history working copy."""
import sys, time; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/stops/climb.py").read().split("class Climb")[0])
C_ = M.close.values
DRET = (pd.DataFrame(C_, index=D) / pd.DataFrame(C_, index=D).shift(1) - 1).values
MRET = np.nanmean(np.where(P.mask, DRET, np.nan), axis=1)


class NewsExit(Strategy):
    def __init__(s, sc, x, k=20, band=100): s.sc, s.x, s.k, s.band = sc, x, k, band
    def reset(s, mk): super().reset(mk); s.hold, s.cool, s.n, s.entry, s.worst = set(), {}, 0, {}, 0.0
    def decide(s, t, st):
        sc = s.sc[t]
        if not np.isfinite(sc).any(): return None
        px = np.nan_to_num(C_[t])
        hit = set()
        if s.x is not None and MRET[t] > -0.01:
            hit = {i for i in s.hold if np.isfinite(DRET[t, i]) and DRET[t, i] <= -s.x}
        for i in hit: s.cool[i] = t + 63
        s.n += len(hit)
        w = np.array(st["weights"], float)
        order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf))); rank = {i: j for j, i in enumerate(order)}
        keep = {i for i in s.hold if i not in hit and np.isfinite(sc[i]) and rank[i] < s.band}
        for i in s.hold - keep:
            if s.entry.get(i, 0) > 0: s.worst = min(s.worst, px[i] / s.entry[i] - 1)
        if len(keep) == len(s.hold) == s.k: return None
        slot = st["nav"] / s.k
        new = [i for i in order if i not in keep and np.isfinite(sc[i]) and s.cool.get(i, -1) < t and 0 < px[i] <= slot][: s.k - len(keep)]
        out = np.zeros(len(sc))
        for i in keep: out[i] = w[i]
        rest = 1 - out.sum()
        for i in new: out[i] = max(rest, 0) / len(new); s.entry[i] = px[i]
        s.hold = keep | set(new); return out


rows = []
for x in (None, 0.10, 0.15, 0.20):
    strat = NewsExit(MD, x)
    res = run(M, strat, Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01))
    a = metrics(res.nav_post_tax, START, None); b = metrics(res.nav_post_tax, "2022-01-01", None)
    rows.append(dict(book="base (no exit rule)" if x is None else f"bad-news exit {int(x*100)}%", CAGR=round(float(a["CAGR"]), 4), Sharpe=round(float(a["Sharpe"]), 3),
                     MaxDD=round(float(a["MaxDD"]), 3), CAGR_2022_26=round(float(b["CAGR"]), 4), turnover=round(res.turnover, 2), exits=strat.n,
                     worst_holding_loss_at_exit=round(strat.worst, 3)))
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("research/stops/news_exit_metrics.csv", index=False)
