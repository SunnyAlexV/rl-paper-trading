"""Is the 20-day lower-wick share new information? Correlations with known signals and IC alone vs combined."""
import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
from alpha.scoring import zrank
P = CouncilPanel(); D = P.dates; Mk = P.mask
F = lambda k: pd.DataFrame(P.feat[k], index=D)
o, h, l, c = F("open"), F("high"), F("low"), F("close").ffill()
rng = (h - l).where(h > l)
lw = ((np.minimum(o, c) - l) / rng).rolling(20, min_periods=12).mean()
uw = ((h - np.maximum(o, c)) / rng).rolling(20, min_periods=12).mean()
r = c.pct_change()
X = {"lower wick 20d": lw, "lower minus upper 20d": lw - uw, "momentum 12-1": c.shift(21) / c.shift(252) - 1,
     "delivery share 20d": F("deliv_pct").rolling(20, min_periods=12).mean(), "volatility 20d": r.rolling(20).std(),
     "20-day return": c / c.shift(20) - 1, "5-day return": c / c.shift(5) - 1}
Z = {k: zrank(v.values, Mk) for k, v in X.items()}
Z["mom + delivery"] = (Z["momentum 12-1"] + Z["delivery share 20d"]) / 2
Z["mom + delivery + lower wick"] = (Z["momentum 12-1"] + Z["delivery share 20d"] + Z["lower wick 20d"]) / 3
to = np.log(F("open").ffill())
samp = np.arange(260, len(D) - 62, 20)
def ic(a, b, t):          # Spearman: rank both sides over the universe
    m = Mk[t] & np.isfinite(b[t]); return pd.Series(a[t][m]).rank().corr(pd.Series(b[t][m]).rank())
print("average cross-sectional correlation with 'lower wick 20d':")
for k in X:
    if k != "lower wick 20d": print(f"  {k:24s} {np.nanmean([ic(Z['lower wick 20d'], Z[k], t) for t in samp]):+.2f}")
for hz in (20, 60):
    tgt = (to.shift(-1 - hz) - to.shift(-1)).values; s = np.arange(260, len(D) - hz - 2, hz)
    print(f"\nIC vs {hz}-day forward return (non-overlapping, 2012-2026):")
    for k in ["lower wick 20d", "momentum 12-1", "delivery share 20d", "mom + delivery", "mom + delivery + lower wick"]:
        a = np.array([ic(Z[k], tgt, t) for t in s]); print(f"  {k:28s} IC {a.mean():+.4f}  t {a.mean()/a.std()*np.sqrt(len(a)):+.2f}")
