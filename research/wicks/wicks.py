"""Do candle wicks predict returns? Rank IC of wick measures vs forward returns (from the next open).
Diagnostic only (Stage 1: no costs). Run from the history working copy."""
import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
from alpha.bhav_panel import BhavPanel, build
from alpha.scoring import zrank
P = BhavPanel(); D = P.dates; Mk = P.mask
o, h, l, c = (pd.DataFrame(P.feat[k], index=D) for k in ("open", "high", "low", "close"))
rng = (h - l).where(h > l)
up = (h - np.maximum(o, c)) / rng; lo = (np.minimum(o, c) - l) / rng
W = {"upper wick % (day)": up, "lower wick % (day)": lo, "lower minus upper (day)": lo - up,
     "lower minus upper (20-day mean)": (lo - up).rolling(20, min_periods=12).mean(),
     "upper wick % (20-day mean)": up.rolling(20, min_periods=12).mean(),
     "lower wick % (20-day mean)": lo.rolling(20, min_periods=12).mean()}
to = np.log(pd.DataFrame(P.feat["open"], index=D).ffill())
tv = build()["tv"].reindex(index=D, columns=P.names).rolling(60, min_periods=40).median()
rows = []
for hz in (5, 20, 60):
    tgt = (to.shift(-1 - hz) - to.shift(-1)).values
    samp = np.arange(260, len(D) - hz - 2, hz)                  # non-overlapping
    for name, x in W.items():
        for bucket in ("all", "large third", "small third"):
            ics = []
            for t in samp:
                m = Mk[t] & np.isfinite(tgt[t]) & np.isfinite(x.values[t])
                if bucket != "all":
                    q = tv.values[t]; qq = np.nanpercentile(np.where(Mk[t], q, np.nan), [33, 67])
                    m &= (q >= qq[1]) if bucket == "large third" else (q <= qq[0])
                if m.sum() < 30: continue
                ics.append(pd.Series(x.values[t][m]).rank().corr(pd.Series(tgt[t][m]).rank()))
            a = np.array(ics)
            rows.append(dict(measure=name, horizon=hz, bucket=bucket, IC=round(a.mean(), 4), t=round(a.mean() / a.std() * np.sqrt(len(a)), 2), n=len(a),
                             IC_2012_19=round(a[: len(a) // 2].mean(), 4), IC_2019_26=round(a[len(a) // 2:].mean(), 4)))
R = pd.DataFrame(rows); R.to_csv("research/wicks/wick_ic.csv", index=False)
print(R.to_string(index=False))
