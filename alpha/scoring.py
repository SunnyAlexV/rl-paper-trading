"""Scoring formulas: cross-sectional rank IC, rank autocorrelation (turnover proxy), pool combination.

Every alpha is turned into a daily cross-sectional z-scored rank over the tradable mask; a missing
value becomes 0 (neutral). The pool's combined signal is a linear blend of member z-scores with
weights from a pooled least-squares fit to the z-scored target rank (AlphaGen-style).
"""
import numpy as np
import bottleneck as bn


def zrank(x, mask):
    x = np.where(mask & np.isfinite(x), x, np.nan)
    r = bn.nanrankdata(x, axis=1)
    mu = np.nanmean(r, axis=1, keepdims=True)
    sd = np.nanstd(r, axis=1, keepdims=True)
    with np.errstate(all="ignore"):
        z = (r - mu) / sd
    return np.nan_to_num(z)


def daily_ic(z, zt, valid):
    """Per-day Pearson correlation of two z-score panels over valid cells."""
    a = np.where(valid, z, np.nan); b = np.where(valid, zt, np.nan)
    a = a - np.nanmean(a, 1, keepdims=True); b = b - np.nanmean(b, 1, keepdims=True)
    with np.errstate(all="ignore"):
        num = np.nansum(a * b, 1)
        den = np.sqrt(np.nansum(a * a, 1) * np.nansum(b * b, 1))
        ic = num / den
    return ic[np.isfinite(ic)]


def autocorr(z, valid):
    ic = daily_ic(z[1:], z[:-1], valid[1:] & valid[:-1])
    return float(np.mean(ic)) if len(ic) else 0.0


class Scorer:
    def __init__(self, target, mask, rows, permute_seed=None):
        """rows: integer index of the dates used (one split). permute_seed: shuffle the target
        across stocks within each day -> a market with no cross-sectional predictability."""
        self.rows = rows
        t = target[rows].copy()
        m = mask[rows] & np.isfinite(t)
        if permute_seed is not None:
            rng = np.random.default_rng(permute_seed)
            for i in range(len(t)):
                v = np.where(m[i])[0]
                t[i, v] = t[i, rng.permutation(v)]
        self.mask = mask[rows]
        self.valid = m
        self.zt = zrank(t, m)

    def alpha_z(self, raw):
        return zrank(raw[self.rows], self.mask)

    def ic(self, z):
        d = daily_ic(z, self.zt, self.valid)
        return float(d.mean()) if len(d) > 50 else 0.0, d

    def combine(self, zs, ridge=1e-3):
        """Least-squares blend weights and the blended signal's mean daily IC."""
        if not zs:
            return np.array([]), 0.0
        k = len(zs)
        G = np.empty((k, k)); b = np.empty(k)
        v = self.valid
        for i in range(k):
            b[i] = np.mean(zs[i][v] * self.zt[v])
            for j in range(i, k):
                G[i, j] = G[j, i] = np.mean(zs[i][v] * zs[j][v])
        w = np.linalg.solve(G + ridge * np.eye(k), b)
        comb = sum(wi * zi for wi, zi in zip(w, zs))
        return w, self.ic(comb)[0]

    def blend(self, zs, w):
        return sum(wi * zi for wi, zi in zip(w, zs))

    def corr(self, za, zb):
        v = self.valid
        return float(np.corrcoef(za[v], zb[v])[0, 1])
