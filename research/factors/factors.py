"""Factor attribution (rules in SPEC.md). Run from the history working copy."""
import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd, statsmodels.api as sm
exec(open("research/stress/stress.py").read().split("def score(mask)")[0])          # P, M, c, dp, r, zrank, BandM, run, metrics, Config
from alpha.bhav_panel import build
from alpha.signal import pool_score
D = P.dates; MK = P.mask
tv = build()["tv"].reindex(index=D, columns=P.names).rolling(60, min_periods=40).median().values
mom = (c.shift(21) / c.shift(252) - 1).values; dlv = dp.rolling(60, min_periods=36).mean().values
vol = r.rolling(250, min_periods=200).std().values
ret = (c.shift(-1) / c - 1).values                      # next-day return, so a sort at t earns t -> t+1
me_idx = np.where(np.r_[D[1:].month != D[:-1].month, True])[0]


def ls_factor(x, low_is_long=False):
    """Equal-weight top third minus bottom third, sorted at each month-end, held for the month (daily returns)."""
    out = np.full(len(D), np.nan)
    for a, b in zip(me_idx[:-1], me_idx[1:]):
        m = MK[a] & np.isfinite(x[a])
        if m.sum() < 30: continue
        q1, q2 = np.nanpercentile(x[a][m], [100 / 3, 200 / 3])
        hi = m & (x[a] >= q2); lo = m & (x[a] <= q1)
        L, S = (lo, hi) if low_is_long else (hi, lo)
        out[a:b] = np.nanmean(np.where(L, ret[a:b], np.nan), axis=1) - np.nanmean(np.where(S, ret[a:b], np.nan), axis=1)
    return pd.Series(out, index=D).shift(1)            # return realised on day t+1, dated t+1


ew = pd.Series(np.nanmean(np.where(MK, ret, np.nan), axis=1), index=D).shift(1)
cash_d = 1.065 ** (1 / 252) - 1
F = pd.DataFrame({"MKT": ew - cash_d, "SIZE": ls_factor(tv, low_is_long=True), "MOM": ls_factor(mom),
                  "LOWVOL": ls_factor(vol, low_is_long=True), "DELIV": ls_factor(dlv)}).loc["2012-07-02":]
cfg = Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01)
books = {"momentum + delivery (primary)": BandM(np.where(MK, (zrank(mom, MK) + zrank(dlv, MK)) / 2, np.nan), 20, 100),
         "momentum only": BandM(np.where(MK, mom, np.nan), 20, 100),
         "council (frozen)": BandM(np.where(MK, pool_score(P, "c_council_real"), np.nan), 20, 100)}
Fm = (1 + F.fillna(0)).resample("ME").prod() - 1
cash_m = 1.065 ** (1 / 12) - 1
print("factor returns, % a year (monthly compounding):", ((1 + Fm.mean()) ** 12 - 1).mul(100).round(1).to_dict())
rows = []
for name, strat in books.items():
    nav = run(M, strat, cfg).nav
    y = nav.resample("ME").last().pct_change().dropna() - cash_m
    for spec in (["MKT", "SIZE", "MOM", "LOWVOL"], ["MKT", "SIZE", "MOM", "LOWVOL", "DELIV"]):
        X = sm.add_constant(Fm.loc[y.index, spec]); fit = sm.OLS(y, X, missing="drop").fit(cov_type="HAC", cov_kwds={"maxlags": 3})
        rows.append(dict(book=name, factors="+".join(spec), months=int(fit.nobs), alpha_pct_yr=round(((1 + fit.params["const"]) ** 12 - 1) * 100, 1),
                         alpha_t=round(fit.tvalues["const"], 2), R2=round(fit.rsquared, 2),
                         **{f"beta_{k}": round(fit.params[k], 2) for k in spec}, **{f"t_{k}": round(fit.tvalues[k], 1) for k in spec}))
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("research/factors/attribution.csv", index=False)
print("factor correlations (monthly):"); print(Fm.corr().round(2).to_string())
