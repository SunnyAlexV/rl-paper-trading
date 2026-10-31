"""RL decision agent (Stage 3): a learned gatekeeper between the discovered signal and the market.

Each day, for every candidate stock (current holdings plus the top 40 by signal), a small
policy network scores how much it wants to own that stock, given:
   1 signal z-score            2 signal rank (1 = best)       3 held now (0/1)
   4 unrealised gain %         5 days until long-term (if short-term), /365
   6 one-way cost % to trade it (statutory + half spread + DP as % of position)
   7 tax due if sold now, as % of position                    8 20-day volatility
   9 portfolio fill (holdings / K)
Decision rule: sell a holding whose score is below 0; buy non-held names with score above 0,
best first, into free slots (max K = 20, each slot = NAV / K). Everything else: no trade.

Training: evolution strategies (ES; Salimans et al. 2017), a policy-search RL method that needs no
gradient through the market, which suits fixed fees, whole decisions and tax. The objective is the
phase 1 goal: annualised Sharpe of the post-tax NAV over 2013-19 in a fast simulator with Stage 0
costs (statutory, spread, DP) and capital gains tax. The checkpoint is chosen on 2020-21.
The fast simulator uses fractional rupee positions; the exact engine (whole shares, impact,
participation cap, FIFO lots, dividends) is the final judge.
"""
import numpy as np
from .netproxy import BUY_PROP, SELL_PROP, DP
from tax import TaxBook, fy_of

N_FEAT, HIDDEN, K, M = 9, 16, 20, 40


def n_params():
    return N_FEAT * HIDDEN + HIDDEN + HIDDEN + 1


def policy(theta, X):
    a = N_FEAT * HIDDEN
    W1 = theta[:a].reshape(N_FEAT, HIDDEN); b1 = theta[a:a + HIDDEN]
    W2 = theta[a + HIDDEN:a + 2 * HIDDEN]; b2 = theta[-1]
    return np.tanh(X @ W1 + b1) @ W2 + b2


def features(score_row, rank_row, cand, held, gain, days_held, cost_row, vol_row, nav, n_held):
    X = np.zeros((len(cand), N_FEAT))
    X[:, 0] = np.clip(score_row[cand], -4, 4)
    X[:, 1] = rank_row[cand]
    X[:, 2] = held
    X[:, 3] = np.clip(gain * 10, -5, 5)                       # gain fraction x10
    st = held * (days_held <= 365)
    X[:, 4] = st * np.clip((366 - days_held) / 365, 0, 1)
    X[:, 5] = cost_row * 100                                   # percent
    tax_rate = np.where(days_held <= 365, 0.208, 0.13)
    X[:, 6] = held * np.maximum(gain, 0) * tax_rate * 100      # percent of position
    X[:, 7] = np.nan_to_num(vol_row[cand]) * 50
    X[:, 8] = n_held / K
    return X


class FastSim:
    """Daily simulation of the agent on one split (rows of the panel), Rs 1,00,000 start."""
    def __init__(self, P, score, rows, capital=1e5, date_rows=None, whole_shares=False, hyst=0.0):
        """date_rows: dates to use for the tax calendar when `rows` is a resampled (bootstrapped)
        history; defaults to the dates of `rows` themselves."""
        self.rows, self.capital = rows, capital
        self.dates = P.dates[rows if date_rows is None else date_rows]
        self.R = np.nan_to_num(np.exp(P.targets[1][rows]), nan=1.0)   # open t+1 -> t+2 gross return
        self.score = score[rows]
        self.mask = P.mask[rows] & np.isfinite(self.score)
        sc = np.where(self.mask, self.score, np.nan)
        self.rank = (np.argsort(np.argsort(-np.nan_to_num(sc, nan=-1e9), 1), 1)).astype(float)
        nvalid = self.mask.sum(1, keepdims=True)
        self.rank = np.where(self.mask, 1 - self.rank / np.maximum(nvalid - 1, 1), 0.0)
        self.half_spread = P.spread[rows] / 2
        import bottleneck as bn
        self.vol = bn.move_std(P.feat["ret"], 20, 10, axis=0)[rows]
        self.tradable_next = np.isfinite(P.targets[1][rows])
        # Stage 5: whole shares at the next open (back-adjusted price, as in the exact engine)
        # and a hysteresis band: sell only if score < -hyst, buy only if score > +hyst.
        self.whole_shares, self.hyst = whole_shares, hyst
        nxt = np.minimum(np.asarray(rows) + 1, len(P.dates) - 1)
        self.next_open = P.feat["open"][nxt]

    def run(self, theta=None, rule=None, record=False):
        """theta: policy params, or rule(cand_info) for a fixed benchmark rule. Returns daily NAV."""
        T, N = self.score.shape
        pos = np.zeros(N); basis = np.zeros(N); entry = np.full(N, -1)
        cash = self.capital
        st_g = lt_g = 0.0; cf_st, cf_lt = [], []
        book = TaxBook(1)
        cur_fy = fy_of(self.dates[0])
        navs = np.empty(T); trades = 0; costs = 0.0; taxes = 0.0
        for t in range(T):
            fy = fy_of(self.dates[t])
            if fy != cur_fy:
                tax, cf_st, cf_lt = book._settle(cur_fy, st_g, lt_g, cf_st, cf_lt)
                cash -= tax; taxes += tax; st_g = lt_g = 0.0; cur_fy = fy
            nav = cash + pos.sum()
            held_idx = np.where(pos > 0)[0]
            top = np.where(self.mask[t])[0]
            if len(top):
                top = top[np.argsort(-self.score[t, top])[:M]]
            cand = np.unique(np.concatenate([held_idx, top])).astype(int)
            if len(cand):
                held = (pos[cand] > 0).astype(float)
                gain = np.where(held > 0, pos[cand] / np.maximum(basis[cand], 1e-9) - 1, 0.0)
                days = np.where(held > 0, t - entry[cand], 0) * 365 / 252
                slot = nav / K
                cost = np.where(held > 0,
                                SELL_PROP + self.half_spread[t, cand] + DP / np.maximum(pos[cand], 1.0),
                                BUY_PROP + self.half_spread[t, cand])
                n_held = len(held_idx)
                if rule is not None:
                    u = rule(self, t, cand, held)
                else:
                    X = features(self.score[t], self.rank[t], cand, held, gain, days, cost, self.vol[t], nav, n_held)
                    u = policy(theta, X)
                can = self.tradable_next[t, cand]
                # sells
                for j in np.where((held > 0) & (u < -self.hyst) & can)[0]:
                    i = cand[j]; v = pos[i]
                    c = v * (SELL_PROP + self.half_spread[t, i]) + DP
                    g = v - basis[i]
                    if days[j] > 365: lt_g += g
                    else: st_g += g
                    cash += v - c; costs += c; trades += 1
                    pos[i] = 0; basis[i] = 0; entry[i] = -1
                    n_held -= 1
                # buys
                order = np.argsort(-u)
                for j in order:
                    if n_held >= K or u[j] <= self.hyst: break
                    i = cand[j]
                    if pos[i] > 0 or not can[j] or not self.mask[t, i]: continue
                    v = min(slot, cash / (1 + BUY_PROP + self.half_spread[t, i]))
                    if v < slot * 0.5: break
                    if self.whole_shares:
                        px = self.next_open[t, i]
                        if not np.isfinite(px) or px <= 0: continue
                        q = np.floor(v / px)
                        if q < 1: continue                      # one share costs more than the slot
                        v = q * px
                    c = v * (BUY_PROP + self.half_spread[t, i])
                    cash -= v + c; costs += c; trades += 1
                    pos[i] = v; basis[i] = v; entry[i] = t
                    n_held += 1
            # accrued tax for post-tax NAV
            acc = book._settle(cur_fy, st_g, lt_g, cf_st, cf_lt)[0]
            navs[t] = cash + pos.sum() - acc
            pos *= self.R[t]
        if record:
            return navs, dict(trades=trades, costs=costs, taxes=taxes)
        return navs


def sharpe(navs):
    r = np.diff(navs) / navs[:-1]
    return float(r.mean() / (r.std() + 1e-12) * np.sqrt(252))


def topk_rule(sim, t, cand, held):
    """Benchmark: always hold the current top-K by signal (sell anything else)."""
    r = sim.rank[t, cand]
    thr = np.sort(sim.rank[t][sim.mask[t]])[-K] if sim.mask[t].sum() >= K else 1.0
    return np.where(r >= thr, 1.0, -1.0)


def band_rule(band=60):
    def rule(sim, t, cand, held):
        nvalid = sim.mask[t].sum()
        r = sim.rank[t, cand]
        keep = r >= 1 - band / max(nvalid, 1)
        enter = r >= 1 - K / max(nvalid, 1)
        return np.where(held > 0, np.where(keep, 1.0, -1.0), np.where(enter, r, -1.0))
    return rule


def init_theta(rng):
    """Start from a sensible prior instead of 'never trade': one hidden unit roughly computes
    0.3*signal + 0.6*held - 0.3*cost, scaled so strong signals buy and holdings are sticky.
    The rest are small random weights the search can grow."""
    d = n_params(); th = rng.normal(0, 0.05, d)
    W1 = th[:N_FEAT * HIDDEN].reshape(N_FEAT, HIDDEN)
    W1[:, 0] = 0.0; W1[0, 0] = 0.3; W1[2, 0] = 0.6; W1[5, 0] = -0.3
    th[:N_FEAT * HIDDEN] = W1.ravel()
    th[N_FEAT * HIDDEN + HIDDEN] = 3.0          # W2 for unit 0
    th[-1] = -1.0                               # bias: need a strong signal to buy
    return th


def train_es(sim_tr, sim_va, gens=40, pop=24, sigma=0.1, lr=0.03, seed=0, log=print):
    rng = np.random.default_rng(seed)
    d = n_params()
    theta = init_theta(rng)
    m = np.zeros(d); v = np.zeros(d); b1, b2, eps = 0.9, 0.999, 1e-8
    best = (-1e9, theta.copy(), -1)
    hist = []
    for g in range(gens):
        noise = rng.normal(size=(pop // 2, d))
        rewards = []
        for e in noise:
            rewards.append(sharpe(sim_tr.run(theta + sigma * e)))
            rewards.append(sharpe(sim_tr.run(theta - sigma * e)))
        rw = np.array(rewards).reshape(-1, 2)
        ranks = np.argsort(np.argsort(rw.ravel())).reshape(-1, 2) / (rw.size - 1) - 0.5   # centred ranks
        grad = ((ranks[:, 0] - ranks[:, 1])[:, None] * noise).sum(0) / (pop * sigma)
        m = b1 * m + (1 - b1) * grad; v = b2 * v + (1 - b2) * grad ** 2
        theta = theta + lr * (m / (1 - b1 ** (g + 1))) / (np.sqrt(v / (1 - b2 ** (g + 1))) + eps)
        s_tr = sharpe(sim_tr.run(theta)); s_va = sharpe(sim_va.run(theta))
        hist.append((g, float(rw.mean()), s_tr, s_va))
        if s_va > best[0]:
            best = (s_va, theta.copy(), g)
        log(f"gen {g + 1}: pop mean Sharpe {rw.mean():.3f}, train {s_tr:.3f}, valid {s_va:.3f}")
    return best, hist
