"""Nifty 500 panel for strategy discovery: features, target and a point-in-time liquidity mask.

All features are known at the close of day t. The target is the total-return open(t+1) -> open(t+2),
the first return a decision taken at t's close can actually earn.
"""
import numpy as np, pandas as pd

SPLITS = {"train": ("2013-01-01", "2019-12-31"),
          "valid": ("2020-01-01", "2021-12-31"),
          "test": ("2022-01-01", "2099-12-31")}


class Panel:
    def __init__(self, path="data/n500/raw.pkl", min_tv_cr=5.0, min_price=20.0, min_history=250):
        raw = pd.read_pickle(path)
        raw = raw.loc[:, ~raw.columns.duplicated()]
        cols = [c for c in raw["Close"].columns if raw["Close"][c].notna().sum() > 300]
        g = lambda k: raw[k][cols].astype(float)
        close, adj = g("Close"), g("Adj Close")
        f = (adj / close)                                       # dividend adjustment factor
        self.dates, self.names = close.index, [c[:-3] for c in cols]
        o, h, l, c = g("Open") * f, g("High") * f, g("Low") * f, adj
        v = g("Volume").where(g("Volume") > 0)
        bad = (g("Open") <= 0) | o.isna() | v.isna()
        o, h, l, c, v = (x.mask(bad) for x in (o, h, l, c, v))
        self.feat = {
            "open": o.values, "high": h.values, "low": l.values, "close": c.values,
            "volume": v.values, "vwap": ((h + l + c) / 3).values,
            "ret": (c / c.shift(1) - 1).values,
        }
        to = np.log(o)
        self.target = (to.shift(-2) - to.shift(-1)).values       # open t+1 -> open t+2
        # multi-day targets: log total return open t+1 -> open t+1+H
        self.targets = {h: (to.shift(-1 - h) - to.shift(-1)).values for h in (1, 5, 20)}
        tv = (g("Close") * v).rolling(60, min_periods=40).median() / 1e7     # Rs crore, known at t
        hist = c.notna().cumsum()
        # full bid-ask spread by 60-day median traded value (Stage 2 assumption, not measured)
        self.spread = np.select([tv.values >= 100, tv.values >= 20, tv.values >= 5],
                                [5e-4, 1e-3, 2e-3], 4e-3)
        self.mask = ((tv >= min_tv_cr) & (g("Close") >= min_price) & (hist >= min_history)
                     & c.notna()).values
        self.raw_close, self.raw_open, self.raw_volume = g("Close"), g("Open"), g("Volume")
        self.adj = adj

    def idx(self, split):
        a, b = SPLITS[split]
        return np.where((self.dates >= a) & (self.dates <= b))[0]

    def report(self):
        m = pd.Series(self.mask.sum(1), index=self.dates)
        return {k: int(m.iloc[self.idx(k)].median()) for k in SPLITS}
