"""Multi-asset menu (rules in SPEC.md). Run from the history working copy."""
import sys, itertools; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/stress/stress.py").read().split("def score(mask)")[0])        # P, M, c, dp, zrank, BandM, run, metrics, Config
mom = (c.shift(21) / c.shift(252) - 1).values; dlv = dp.rolling(60, min_periods=36).mean().values
sc = np.where(P.mask, (zrank(mom, P.mask) + zrank(dlv, P.mask)) / 2, np.nan)
E = run(M, BandM(sc, 20, 100), Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01)).nav     # pre-tax, all fees
A = pd.read_pickle("data/etf_adj.pkl")
idx = E.index
R = pd.DataFrame({"E": E.pct_change(), "G": A["GOLDBEES"].reindex(idx).ffill().pct_change(),
                  "US": A["MON100"].reindex(idx).ffill().pct_change()}).fillna(0.0)
R["C"] = (1.065 ** (1 / 252)) - 1
GILT = A["SETF10GILT"].reindex(idx).ffill()
me = R.index.to_series().groupby(R.index.to_period("M")).max().values


def mix(w):
    w = np.array(w, float); val = 1.0; hold = w.copy(); out = []
    X = R[["E", "G", "US", "C"]].values; is_me = np.isin(R.index.values, me)
    for k in range(len(X)):
        hold = hold * (1 + X[k]); v = hold.sum(); out.append(v)
        if is_me[k]:
            tgt = w * v; cost = 0.0015 * np.abs(tgt - hold).sum(); hold = tgt * (1 - cost / v)
    return pd.Series(out, index=R.index)


def stats(nav, a, b):
    m = metrics(nav, a, b); s = nav.loc[a:b] if b else nav.loc[a:]
    y = s.resample("YE").last().pct_change().dropna()
    return dict(CAGR=round(float(m["CAGR"]), 4), Sharpe=round(float(m["Sharpe"]), 3), MaxDD=round(float(m["MaxDD"]), 3),
                worst_year=round(float(y.min()), 3) if len(y) else np.nan)


grid = [(e, g, u, round(1 - e - g - u, 2)) for e in np.arange(0, 1.01, .1) for g in np.arange(0, .41, .1) for u in np.arange(0, .31, .1) if e + g + u <= 1.0001]
rows = []
for w in grid:
    nav = mix(w)
    d = stats(nav, "2012-07-02", "2019-12-31"); t = stats(nav, "2020-01-01", None); f = stats(nav, "2012-07-02", None)
    rows.append(dict(E=round(w[0], 1), G=round(w[1], 1), US=round(w[2], 1), C=round(max(w[3], 0), 1), **{f"design_{k}": v for k, v in d.items()},
                     **{f"test_{k}": v for k, v in t.items()}, **{f"full_{k}": v for k, v in f.items()}))
T = pd.DataFrame(rows); T.to_csv("research/multiasset/menu_all_mixes.csv", index=False)
menu = []
for lim in (0.10, 0.15, 0.20, 0.25, None):
    ok = T if lim is None else T[T.design_MaxDD >= -lim]
    b = ok.sort_values("design_CAGR", ascending=False).iloc[0]
    hs = (T if lim is None else T[T.full_MaxDD >= -lim]).sort_values("full_CAGR", ascending=False).iloc[0]
    menu.append(dict(limit="none" if lim is None else f"{int(lim*100)}%", mix=f"E {b.E:.0%} / G {b.G:.0%} / US {b.US:.0%} / C {b.C:.0%}",
                     design_CAGR=b.design_CAGR, design_MaxDD=b.design_MaxDD, test_CAGR=b.test_CAGR, test_Sharpe=b.test_Sharpe,
                     test_MaxDD=b.test_MaxDD, test_worst_year=b.test_worst_year,
                     test_within_limit=(True if lim is None else bool(b.test_MaxDD >= -lim)),
                     hindsight_full_mix=f"E {hs.E:.0%} / G {hs.G:.0%} / US {hs.US:.0%} / C {hs.C:.0%}", hindsight_full_CAGR=hs.full_CAGR, hindsight_full_MaxDD=hs.full_MaxDD))
MN = pd.DataFrame(menu); MN.to_csv("research/multiasset/menu.csv", index=False); print(MN.to_string(index=False))
print("\nsingle assets, full period:"); 
for k, w in {"E only": (1, 0, 0, 0), "gold only": (0, 1, 0, 0), "US only": (0, 0, 1, 0), "cash only": (0, 0, 0, 1)}.items():
    print(k, stats(mix(w), "2012-07-02", None))
g = GILT.dropna(); print("SETF10GILT since Jun 2016:", stats(g / g.iloc[0], str(g.index[0].date()), None))
print("daily return correlations (2012-2026):"); print(R[["E", "G", "US"]].corr().round(2).to_string())
