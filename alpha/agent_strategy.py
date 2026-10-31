"""The trained decision agent wrapped as a Strategy for the exact Stage 1 engine.

The engine supplies holdings each day; the strategy tracks its own entry day and cost basis
per stock (from the open price on the day a position first fills) to compute the gain, holding
period and tax features the policy was trained on.
"""
import numpy as np
import bottleneck as bn
from strategies import Strategy
from .agent import policy, features, K, M
from .netproxy import BUY_PROP, SELL_PROP, DP


class AgentStrategy(Strategy):
    def __init__(self, P, score, theta, hyst=0.0):
        self.P, self.theta, self.hyst = P, np.asarray(theta), hyst
        self.score = score
        self.mask = P.mask & np.isfinite(score)
        sc = np.where(self.mask, score, np.nan)
        order = np.argsort(np.argsort(-np.nan_to_num(sc, nan=-1e9), 1), 1).astype(float)
        nvalid = self.mask.sum(1, keepdims=True)
        self.rank = np.where(self.mask, 1 - order / np.maximum(nvalid - 1, 1), 0.0)
        self.half_spread = P.spread / 2
        self.vol = bn.move_std(P.feat["ret"], 20, 10, axis=0)
        self.open_px = P.raw_open.values
        self.close_px = np.nan_to_num(P.raw_close.values)

    def reset(self, m):
        super().reset(m)
        self.entry_t = {}; self.basis = {}; self.prev_shares = None

    def decide(self, t, state):
        sh = state["shares"]
        if self.prev_shares is not None:                       # record fills that happened today
            for i in np.where((sh > 0) & (self.prev_shares == 0))[0]:
                self.entry_t[i] = t; self.basis[i] = sh[i] * self.open_px[t, i]
            for i in np.where((sh == 0) & (self.prev_shares > 0))[0]:
                self.entry_t.pop(i, None); self.basis.pop(i, None)
        self.prev_shares = sh.copy()
        nav = state["nav"]
        held_idx = np.where(sh > 0)[0]
        top = np.where(self.mask[t])[0]
        if len(top):
            top = top[np.argsort(-self.score[t, top])[:M]]
        cand = np.unique(np.concatenate([held_idx, top])).astype(int)
        if not len(cand):
            return None
        val = sh[cand] * self.close_px[t, cand]
        held = (sh[cand] > 0).astype(float)
        bas = np.array([self.basis.get(i, v) for i, v in zip(cand, val)])
        gain = np.where(held > 0, val / np.maximum(bas, 1e-9) - 1, 0.0)
        days = np.array([(t - self.entry_t.get(i, t)) * 365 / 252 for i in cand]) * held
        cost = np.where(held > 0, SELL_PROP + self.half_spread[t, cand] + DP / np.maximum(val, 1.0),
                        BUY_PROP + self.half_spread[t, cand])
        X = features(self.score[t], self.rank[t], cand, held, gain, days, cost, self.vol[t], nav, len(held_idx))
        u = policy(self.theta, X)
        w = np.array(state["weights"], dtype=float)
        target = w.copy()
        n_held = len(held_idx)
        changed = False
        for j in np.where((held > 0) & (u < -self.hyst))[0]:
            target[cand[j]] = 0.0; n_held -= 1; changed = True
        for j in np.argsort(-u):
            if n_held >= K or u[j] <= self.hyst:
                break
            i = cand[j]
            if held[j] > 0 or not self.mask[t, i]:
                continue
            if self.close_px[t, i] > nav / K:          # one share costs more than a slot: unbuyable
                continue
            target[i] = 1.0 / K; n_held += 1; changed = True
        return target if changed else None
