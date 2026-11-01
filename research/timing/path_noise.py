"""How much does the band-rule backtest depend on small rule details? (path noise)

Same council signal, dividends, costs and tax; vary k (names held) and the band, each with and
without the trend filter (100% invested when the equal-weight universe is above its 200-day
average, else 50%; idle cash earns 5.5% a year before tax). The slot rule of the paper trader
(skip names whose one share costs more than a slot) is always on, as in paper trading.
  python -m alpha.path_noise PART NPARTS   -> results/path_noise_PART.csv
"""
import sys
import numpy as np, pandas as pd
sys.argv, part, nparts = [sys.argv[0], "none"], int(sys.argv[1]), int(sys.argv[2])
import alpha.timing as T
from alpha.bhav_panel import BhavMarket
from alpha.signal import pool_score
from strategies import Strategy
from backtest import run, metrics, Config

M = BhavMarket(T.P, dividends=True)
score = np.where(T.P.mask, pool_score(T.P, "c_council_real"), np.nan)
ma = (T.ew / T.ew.rolling(200).mean() - 1).values
TREND = np.where(np.nan_to_num(ma, nan=1) > 0, 1.0, 0.5)
ONES = np.ones(len(T.dates))


class TB(Strategy):          # same logic as alpha.timing's TimedBand, with k and band as inputs
    def __init__(self, E, k, band): self.E, self.k, self.band = E, k, band
    def reset(self, m): super().reset(m); self.hold = set(); self.e = None
    def decide(self, t, state):
        sc = score[t]
        if not np.isfinite(sc).any():
            return None
        e = self.E[t]; w = np.array(state["weights"], dtype=float)
        order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf)))
        rank = {i: j for j, i in enumerate(order)}
        keep = {i for i in self.hold if rank[i] < self.band}
        if len(keep) == len(self.hold) == self.k and e == self.e:
            return None
        slot = state["nav"] * e / self.k; px = np.nan_to_num(M.close.values[t])
        new = [i for i in order if i not in keep and np.isfinite(sc[i]) and 0 < px[i] <= slot][: self.k - len(keep)]
        out = np.zeros(len(sc))
        for i in keep: out[i] = w[i] * (e / self.e) if (self.e and e != self.e) else w[i]
        rest = e - out.sum()
        for i in new: out[i] = max(rest, 0) / len(new)
        self.hold, self.e = keep | set(new), e
        return out


jobs = [(k, b, tf) for k in (15, 20, 25) for b in (60, 100, 150) for tf in (False, True)]
rows = []
for j, (k, b, tf) in enumerate(jobs):
    if j % nparts != part:
        continue
    r = run(M, TB(TREND if tf else ONES, k, b), Config(max_weight=0.25, min_trade_frac=0.01, cash_rate=0.055))
    for p, (a, z) in {"2013-19": ("2013-01-01", "2019-12-31"), "2022-26": ("2022-01-01", None), "Full": ("2013-01-01", None)}.items():
        rows.append(dict(k=k, band=b, trend_filter=tf, period=p, **metrics(r.nav_post_tax, a, z), trades=r.trades))
    print(k, b, tf, "done", flush=True)
    pd.DataFrame(rows).to_csv(f"results/path_noise_{part}.csv", index=False)
