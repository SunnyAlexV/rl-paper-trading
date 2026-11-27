"""Universe choice for momentum + delivery (rules in SPEC.md). Run from the history working copy."""
import sys, time; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/stress/stress.py").read().split("def score(mask)")[0])      # P, M, c, dp, BandM, EWM, run, metrics, Config
mom = (c.shift(21) / c.shift(252) - 1).values; dlv = dp.rolling(60, min_periods=36).mean().values
tv = B["tv"].reindex(index=D, columns=P.names).rolling(60, min_periods=40).median() if "B" in dir() else None
from alpha.bhav_panel import build
tv = build()["tv"].reindex(index=D, columns=P.names).rolling(60, min_periods=40).median()
liq_rank = tv.where(P.mask).rank(axis=1, ascending=False).values
vol250 = r.rolling(250, min_periods=200).std().where(P.mask).rank(axis=1, pct=True).values
basis = np.isfinite(P.feat["basis"])
U = {"current (top 500)": P.mask, "top 300": P.mask & (liq_rank <= 300), "top 200": P.mask & (liq_rank <= 200),
     "top 100": P.mask & (liq_rank <= 100), "current minus most volatile third": P.mask & (vol250 <= 2 / 3),
     "F&O stocks only": P.mask & basis}
rows = []
for name, mk in U.items():
    n_med = int(np.median(mk.sum(1)[mk.sum(1) > 0])); band = 100 if n_med >= 200 else max(n_med // 2, 40)
    sc = np.where(mk, (zrank(mom, mk) + zrank(dlv, mk)) / 2, np.nan)
    for kind, strat in (("rule", BandM(sc, 20, band)), ("equal weight", EWM(mk))):
        nav = run(M, strat, Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01)).nav_post_tax
        a = metrics(nav, START, None); b = metrics(nav, "2022-01-01", None)
        rows.append(dict(universe=name, book=kind, median_stocks=n_med, band=band if kind == "rule" else None, CAGR=round(float(a["CAGR"]), 4),
                         Sharpe=round(float(a["Sharpe"]), 3), MaxDD=round(float(a["MaxDD"]), 3), CAGR_2022_26=round(float(b["CAGR"]), 4)))
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("research/universe/universe_metrics.csv", index=False)
