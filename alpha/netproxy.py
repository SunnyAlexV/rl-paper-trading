"""Fast net-of-cost reward for strategy discovery (Stage 3).

A formula is judged by the portfolio a Rs 1,00,000 retail account could actually run on it:
every H days, hold the top K stocks by the signal, equal weight, long only. Its return over each
H-day holding period is compared with the equal-weight average of all tradable stocks (so market
beta earns nothing), after these costs on every name swapped:
  buy  side: STT 0.1% + stamp 0.015% + exchange/SEBI/GST ~0.0037% + half spread
  sell side: STT 0.1% + exchange/SEBI/GST ~0.0037% + half spread + Rs 15.34 DP per scrip
The reward is the annualised information ratio (IR) of these net active returns, averaged over
four start offsets so the result does not hinge on which day the cycle begins.
Taxes are left to the exact engine; this proxy only has to rank formulas sensibly.
"""
import numpy as np

BUY_PROP = 0.001 + 0.00015 + 0.000037
SELL_PROP = 0.001 + 0.000037
DP = 15.34


class NetProxy:
    def __init__(self, target_h, mask, spread, rows, H, K=20, capital=1e5, permute_seed=None):
        self.H, self.K, self.capital = H, K, capital
        t = np.expm1(target_h[rows])                         # simple H-day return
        m = mask[rows] & np.isfinite(t)
        if permute_seed is not None:                         # null market: shuffle across stocks daily
            rng = np.random.default_rng(permute_seed)
            t = t.copy()
            for i in range(len(t)):
                v = np.where(m[i])[0]
                t[i, v] = t[i, rng.permutation(v)]
        self.t, self.m = t, m
        self.spread = spread[rows]
        self.offsets = sorted({0, H // 4, H // 2, (3 * H) // 4})
        self.bench = {o: np.array([np.nanmean(np.where(m[r], t[r], np.nan)) for r in range(o, len(t), H)])
                      for o in self.offsets}

    def ir(self, z, return_detail=False):
        """z: T x N signal panel (rows aligned to self). Higher z = more attractive."""
        irs, turns = [], []
        pos_value = self.capital / self.K
        for o in self.offsets:
            prev = set()
            act = []
            nswap = 0
            for k, r in enumerate(range(o, len(self.t), self.H)):
                ok = np.where(self.m[r])[0]
                if len(ok) < self.K * 2:
                    act.append(0.0); continue
                s = np.where(np.isfinite(z[r, ok]), z[r, ok], -np.inf)
                pick = ok[np.argpartition(-s, self.K)[:self.K]]
                cur = set(pick.tolist())
                new = cur - prev
                old = prev - cur
                cost = 0.0
                for i in new:
                    cost += (BUY_PROP + self.spread[r, i] / 2) / self.K
                for i in old:
                    cost += (SELL_PROP + self.spread[r, i] / 2) / self.K + DP / self.capital
                nswap += len(new)
                gross = float(np.mean(self.t[r, pick]))
                act.append(gross - self.bench[o][k] - cost)
                prev = cur
            a = np.array(act)
            irs.append(a.mean() / (a.std() + 1e-12) * np.sqrt(252 / self.H))
            turns.append(nswap / self.K / (len(self.t) / 252))
        if return_detail:
            return float(np.mean(irs)), float(np.mean(turns))
        return float(np.mean(irs))
