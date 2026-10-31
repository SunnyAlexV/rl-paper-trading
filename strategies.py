"""Signal layer v0 and the benchmark strategies (all decide at the close, trade next open)."""
import numpy as np, pandas as pd


class RidgeSignal:
    """Walk-forward cross-sectional ridge: next open-to-open return on momentum, reversal, volatility.

    Features at close t (cross-sectionally z-scored): 12-1 month momentum, 1-month reversal,
    60-day volatility. Target for day t: total-return open(t+1) -> open(t+2), demeaned across stocks.
    Refit on the first trading day of each month using a trailing 504-day window of rows whose
    target was already known (s <= t-2). Prediction = standardised score per stock.
    """
    def __init__(self, market, window=504, alpha=0.1):
        m = market
        la = np.log(m.adj)
        mom = la.shift(21) - la.shift(252)
        rev = la - la.shift(21)
        vol = la.diff().rolling(60, min_periods=40).std()
        z = lambda x: x.sub(x.mean(1), axis=0).div(x.std(1), axis=0)
        self.F = np.stack([z(mom).values, z(rev).values, z(vol).values], axis=-1)   # T x N x 3
        topen = np.log(m.open * m.adj_factor)
        y = topen.shift(-2) - topen.shift(-1)                                       # open t+1 -> t+2
        self.y = y.sub(y.mean(1), axis=0).values
        self.dates = m.dates
        self.window, self.alpha = window, alpha
        self.beta = None
        self.score = np.full((len(m.dates), m.n), np.nan)
        self.betas = {}
        self._fit_all()

    def _fit_all(self):
        month = self.dates.to_period("M")
        last_fit = None
        for t in range(len(self.dates)):
            if last_fit is None or month[t] != month[t - 1]:
                lo, hi = max(0, t - 2 - self.window), t - 2
                if hi - lo >= 250:
                    X = self.F[lo:hi].reshape(-1, 3); Y = self.y[lo:hi].reshape(-1)
                    ok = np.isfinite(X).all(1) & np.isfinite(Y)
                    X, Y = X[ok], Y[ok]
                    if len(Y) < 250 * 10:          # need ~a year of full cross-sections
                        continue
                    self.beta = np.linalg.solve(X.T @ X + self.alpha * len(Y) * np.eye(3), X.T @ Y)
                    self.betas[self.dates[t]] = self.beta
                    last_fit = t
            if self.beta is not None:
                self.score[t] = np.nan_to_num(self.F[t]) @ self.beta

    def ic(self, start=None, end=None):
        """Mean daily rank IC between score at t and realised target, over a period."""
        idx = (self.dates >= (start or self.dates[0])) & (self.dates <= (end or self.dates[-1]))
        s = pd.DataFrame(self.score[idx]).rank(1); y = pd.DataFrame(self.y[idx]).rank(1)
        return float(s.corrwith(y, axis=1).mean())


class Strategy:
    def reset(self, m): self.m = m; self.started = False
    def decide(self, t, state): raise NotImplementedError


class EqualWeightBuyHold(Strategy):
    def decide(self, t, state):
        if not self.started:
            self.started = True
            return np.full(self.m.n, 1.0 / self.m.n)
        return None


class EqualWeightMonthly(Strategy):
    def decide(self, t, state):
        d = self.m.dates
        last_of_month = t + 1 >= len(d) or d[t + 1].month != d[t].month
        if not self.started or last_of_month:
            self.started = True
            return np.full(self.m.n, 1.0 / self.m.n)
        return None


class TopKDaily(Strategy):
    """Naive signal rebalance: hold the top-k forecasts equally, re-targeted every day."""
    def __init__(self, signal, k=5): self.sig, self.k = signal, k
    def decide(self, t, state):
        s = self.sig.score[t]
        if not np.isfinite(s).any():
            return None
        w = np.zeros(len(s)); w[np.argsort(-s)[:self.k]] = 1.0 / self.k
        return w


class TopKBand(Strategy):
    """No-trade band: hold k names; replace a name only when it drops out of the top `band`.
    New names get the weight freed by the names sold; untouched names are not re-weighted."""
    def __init__(self, signal, k=5, band=10): self.sig, self.k, self.band = signal, k, band
    def reset(self, m): super().reset(m); self.hold = set()
    def decide(self, t, state):
        s = self.sig.score[t]
        if not np.isfinite(s).any():
            return None
        order = list(np.argsort(-s))
        keep = {i for i in self.hold if order.index(i) < self.band}
        if len(keep) == len(self.hold) == self.k:
            return None                                 # inside the band: no trade
        new = [i for i in order if i not in keep][: self.k - len(keep)]
        w = np.array(state["weights"], dtype=float)
        freed = 1.0 - w[list(keep)].sum() if keep else 1.0     # sold names' weight + idle cash
        out = np.zeros(len(s))
        for i in keep: out[i] = w[i]
        for i in new: out[i] = max(freed, 0) / len(new) if new else 0
        if not keep:
            out[new] = 1.0 / self.k
        self.hold = keep | set(new)
        return out
