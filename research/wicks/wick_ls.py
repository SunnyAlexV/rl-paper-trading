"""Wick long-short (rules in SPEC_LS.md). Reuses research/pods/ls_bt.py's engine with a separate short score.
Run from the history working copy."""
import sys; sys.path.insert(0, ".")
src = open("research/pods/ls_bt.py").read().split("PER = [")[0]
src = src.replace('def sim(sig, kL=20, kS=15, longw=0.8, shortw=0.8, mode="ls", mult=1.0, cap=2e7, start="2016-02-01"):',
                  'def sim(sig, kL=20, kS=15, longw=0.8, shortw=0.8, mode="ls", mult=1.0, cap=2e7, start="2016-02-01", sigS=None):')
src = src.replace("                fo = ok & HASFUT[t]\n                ford = np.argsort(np.where(fo, s, np.inf));",
                  "                s = sigS[t] if sigS is not None else s; ok = np.isfinite(s)\n                fo = ok & HASFUT[t]\n                ford = np.argsort(np.where(fo, s, np.inf));")
assert src.count("sigS[t]") == 1
exec(src)
from backtest import metrics
F = lambda k: pd.DataFrame(P.feat[k], index=D)
o, h, l, cl = F("open"), F("high"), F("low"), F("close")
rg = (h - l).where(h > l)
LW = np.where(MASK, ((np.minimum(o, cl) - l) / rg).rolling(20, min_periods=12).mean().values, np.nan)
UW = np.where(MASK, ((h - np.maximum(o, cl)) / rg).rolling(20, min_periods=12).mean().values, np.nan)
S0 = "2012-07-02"
runs = {"wick long-short": sim(LW, sigS=-UW, start=S0),          # shorts = lowest of -UW = highest upper wick
        "wick long-short, costs x2": sim(LW, sigS=-UW, start=S0, mult=2.0),
        "wick long-only": sim(LW, mode="long", longw=1.0, start=S0),
        "equal-weight universe": sim(None, mode="ew", longw=1.0, start=S0)}
nif = NIFTY.loc[S0:]
rows = []
for name, r in list(runs.items()) + [("Nifty 50", dict(nav=nif, shortpl=None, events=0, turnover=0))]:
    nav = r["nav"]; dr = nav.pct_change()
    y = nav.resample("YE").last(); y = y.pct_change().fillna(y.iloc[0] / nav.iloc[0] - 1)
    for pn, a, b in [("all", S0, None), ("2022-26", "2022-01-01", None)]:
        m = metrics(nav, a, b)
        rows.append(dict(book=name, period=pn, **{k: round(float(v), 4) for k, v in m.items()},
                         corr_nifty=round(dr.corr(nif.reindex(nav.index).pct_change()), 3), positive_years=f"{(y > 0).sum()}/{len(y)}",
                         short_leg_pl_pct_of_cap=round(r["shortpl"].sum() / 2e7 * 100, 1) if r.get("shortpl") is not None and name.startswith("wick long-short") else None,
                         margin_events=r["events"], turnover=round(r["turnover"], 2)))
R = pd.DataFrame(rows); R.to_csv("research/wicks/wick_ls_metrics.csv", index=False); print(R.to_string(index=False))
sp = runs["wick long-short"]["shortpl"]; nav = runs["wick long-short"]["nav"]
print("short leg P&L by year, % of average NAV:", (sp.groupby(sp.index.year).sum() / nav.groupby(nav.index.year).mean() * 100).round(1).to_dict())
