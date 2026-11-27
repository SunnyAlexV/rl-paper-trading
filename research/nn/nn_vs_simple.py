"""Neural nets vs simple models (rules in SPEC.md). Run from the history working copy."""
import sys, time; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/stress/stress.py").read().split("def score(mask)")[0])          # P, M, c, dp, r, run ...
from alpha.bhav_panel import build
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.neural_network import MLPRegressor
t0 = time.time(); D = P.dates; MK = P.mask
F = lambda k: pd.DataFrame(P.feat[k], index=D)
o, h, l, cl = F("open"), F("high"), F("low"), F("close")
rg = (h - l).where(h > l); vol = F("volume")
tv = build()["tv"].reindex(index=D, columns=P.names).rolling(60, min_periods=40).median()
raw = {"r5": c / c.shift(5) - 1, "r20": c / c.shift(20) - 1, "r60": c / c.shift(60) - 1, "mom": c.shift(21) / c.shift(252) - 1,
       "vol20": r.rolling(20, min_periods=15).std(), "vol250": r.rolling(250, min_periods=200).std(),
       "volsurge": vol.rolling(5).mean() / vol.rolling(60, min_periods=40).mean(), "size": np.log(tv),
       "deliv": dp.rolling(60, min_periods=36).mean(), "delivtrend": dp.rolling(20, min_periods=12).mean() - dp.rolling(120, min_periods=80).mean(),
       "lowwick": ((np.minimum(o, cl) - l) / rg).rolling(20, min_periods=12).mean(), "upwick": ((h - np.maximum(o, cl)) / rg).rolling(20, min_periods=12).mean()}
to = np.log(F("open").ffill()); tgt = (to.shift(-21) - to.shift(-1))
pr = lambda x: x.where(MK).rank(axis=1, pct=True)
R = {k: pr(v.replace([np.inf, -np.inf], np.nan)).values for k, v in raw.items()}; Y = pr(tgt).values
samp = np.arange(260, len(D) - 22, 5); rows = []
for t in samp:
    m = MK[t] & np.isfinite(Y[t])
    X = np.column_stack([R[k][t][m] for k in R]); X = np.where(np.isfinite(X), X, 0.5)
    rows.append((np.full(m.sum(), t), X, Y[t][m]))
T_ = np.concatenate([a for a, _, _ in rows]); X_ = np.vstack([b for _, b, _ in rows]); Y_ = np.concatenate([c_ for _, _, c_ in rows])
dates = D[T_]; tr = (dates >= "2013-01-01") & (dates <= "2019-12-31"); te = dates >= "2020-01-01"
print("samples train", tr.sum(), "test", te.sum(), round(time.time() - t0), "s", flush=True)
def ic(pred, mask):
    out = []
    for t in np.unique(T_[mask]):
        s = mask & (T_ == t); out.append(pd.Series(pred[s]).rank().corr(pd.Series(Y_[s]).rank()))
    a = np.array(out); return round(float(a.mean()), 4), round(float(a.mean() / a.std() * np.sqrt(len(a) / 4)), 2)   # /4: 20-day targets sampled every 5 days
names = list(R)
models = {"momentum + delivery (no training)": None,
          "ridge regression": Ridge(alpha=10.0),
          "gradient-boosted trees (depth 3)": HistGradientBoostingRegressor(max_depth=3, max_iter=300, learning_rate=0.05, random_state=0),
          "neural net, 1 layer (32)": MLPRegressor(hidden_layer_sizes=(32,), early_stopping=True, validation_fraction=0.2, max_iter=200, random_state=0),
          "neural net, 3 layers (64-32-16)": MLPRegressor(hidden_layer_sizes=(64, 32, 16), early_stopping=True, validation_fraction=0.2, max_iter=200, random_state=0),
          "neural net, 5 layers (256-128-64-32-16)": MLPRegressor(hidden_layer_sizes=(256, 128, 64, 32, 16), early_stopping=True, validation_fraction=0.2, max_iter=200, random_state=0)}
out = []
for name, mdl in models.items():
    if mdl is None:
        pred = (X_[:, names.index("mom")] + X_[:, names.index("deliv")]) / 2
    else:
        mdl.fit(X_[tr], Y_[tr]); pred = mdl.predict(X_)
    a, b = ic(pred, tr), ic(pred, te)
    out.append(dict(model=name, train_IC=a[0], train_t=a[1], test_IC=b[0], test_t=b[1], drop_pct=round((1 - b[0] / a[0]) * 100, 0) if a[0] else None))
    print(out[-1], round(time.time() - t0), "s", flush=True)
pd.DataFrame(out).to_csv("research/nn/nn_vs_simple.csv", index=False)
