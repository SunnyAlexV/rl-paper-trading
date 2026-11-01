"""Narrow timing agent on top of the frozen band rule.

The band rule still chooses WHICH 20 stocks to hold. The agent chooses only HOW MUCH of NAV to
have invested: exposure e_t in {0, 0.5, 1}; the rest sits in a liquid fund (cash_rate a year,
taxed at slab rate). A deliberately small policy (8 numbers) so that it cannot memorise 2013-19:

  u_t = theta . [1, x_t]          x_t = 7 market-state features known at the close of day t
  e_t = 1 if u_t > +h,  0 if u_t < -h-1,  0.5 in between; changes only when u crosses a level by h

Features (standardised with 2013-19 means and sds):
  ew63, ew252   equal-weight universe return over 63 / 252 days
  ew_ma200      equal-weight index / its 200-day average - 1
  vol_ratio     log(20-day EW volatility / its 252-day median)
  breadth       share of universe stocks above their 200-day average, minus 0.5
  health63      the fully invested band rule's 63-day return minus EW's (is the signal working?)
  dd252         the fully invested band rule's drawdown from its 252-day high

Training uses a fast proxy: the exact engine's daily post-tax return series of the fully invested
band rule (with dividends) r_t, and
  R_{t+2} = e_t r_{t+2} + (1 - e_t) c - kappa |e_t - e_{t-1}|        (kappa = 0.4% per unit traded)
(decided at close t, filled at open t+1, so the first full day exposed is t+2: conservative).
Fitness = mean Sharpe over block-bootstrapped (63-day blocks) 2013-19 paths; ES with antithetic
noise; the generation kept is the best on 2020-21; 2022-26 is untouched until the end.
Every policy is then run in the exact engine. Controls: always invested; a classic trend filter
(invested 100% when EW > its 200-day average, else 50%); and the same agent trained on features
shuffled in time by 63-day blocks (a timing signal that cannot exist).

  python -m alpha.timing train      -> results/timing_agents.json
  python -m alpha.timing eval       -> results/timing_eval.csv
"""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar

grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
CASH = 0.055                     # liquid-fund yield, a year, before tax
NET_CASH = CASH * (1 - 0.312) / 252
KAPPA = 0.004
H = 0.25
P = CouncilPanel()
dates = P.dates
navs = pd.read_csv("results/div_eval_navs.csv", index_col=0, parse_dates=True)
base = navs["Council (real) | div=True"].reindex(dates)
r = base.pct_change().fillna(0).values

# ---- features (known at close t)
C = P.raw_close.ffill()
dr = (C / C.shift(1) - 1).where(P.mask)
ew_r = dr.mean(1).fillna(0)
ew = (1 + ew_r).cumprod()
ma200 = C.rolling(200, min_periods=150).mean()
vol20 = ew_r.rolling(20).std()
strat = base.ffill().bfill()
X = pd.DataFrame({
    "ew63": ew / ew.shift(63) - 1,
    "ew252": ew / ew.shift(252) - 1,
    "ew_ma200": ew / ew.rolling(200).mean() - 1,
    "vol_ratio": np.log(vol20 / vol20.rolling(252).median()),
    "breadth": (C > ma200).where(P.mask).mean(1) - 0.5,
    "health63": (strat / strat.shift(63) - 1) - (ew / ew.shift(63) - 1),
    "dd252": strat / strat.rolling(252, min_periods=20).max() - 1,
}, index=dates)
TR = (dates >= "2013-01-01") & (dates <= "2019-12-31")
VA = (dates >= "2020-01-01") & (dates <= "2021-12-31")
mu, sd = X[TR].mean(), X[TR].std()
Z = ((X - mu) / sd).fillna(0).clip(-4, 4).values
FEATS = list(X.columns)


def exposure(theta, Z):
    u = Z @ theta[1:] + theta[0]
    e = np.empty(len(u)); cur = 1.0
    for t, v in enumerate(u):
        if cur == 1.0 and v < -H: cur = 0.5
        if cur == 0.5 and v > H: cur = 1.0
        if cur == 0.5 and v < -1 - H: cur = 0.0
        if cur == 0.0 and v > -1 + H: cur = 0.5
        e[t] = cur
    return e


def proxy(e, rows):
    """Daily proxy returns on `rows` (positions), exposure decided two days earlier."""
    ee = e[rows - 2]; prev = e[rows - 3]
    return ee * r[rows] + (1 - ee) * NET_CASH - KAPPA * np.abs(ee - prev)


def sharpe(x):
    return x.mean() / (x.std() + 1e-12) * np.sqrt(252)


def boot(rows, rng, block=63):
    out = []
    while len(out) < len(rows):
        s = rng.integers(0, len(rows) - block); out.extend(rows[s:s + block])
    return np.array(out[:len(rows)])


def train(Zf, seed=0, gens=60, pop=24, B=4, sigma=0.3, lr=0.05, log=print):
    rng = np.random.default_rng(seed)
    tr_rows, va_rows = np.where(TR)[0], np.where(VA)[0]
    theta = np.zeros(len(FEATS) + 1); theta[0] = 2.0          # start fully invested
    m = np.zeros_like(theta); v = np.zeros_like(theta)
    best = (-np.inf, theta.copy(), -1); hist = []

    def fit(th, paths):
        e = exposure(th, Zf)
        # bootstrap rows index the same day's features and returns jointly (features enter via e)
        return np.mean([sharpe(proxy(e, p)) for p in paths])

    for g in range(gens):
        paths = [boot(tr_rows, rng) for _ in range(B)]
        eps = rng.normal(size=(pop // 2, len(theta)))
        f = np.array([[fit(theta + sigma * e_, paths), fit(theta - sigma * e_, paths)] for e_ in eps])
        A = (f[:, 0] - f[:, 1]); A = A / (A.std() + 1e-12)
        grad = (A[:, None] * eps).mean(0) / sigma
        m = 0.9 * m + 0.1 * grad; v = 0.999 * v + 0.001 * grad ** 2
        theta = theta + lr * (m / (1 - 0.9 ** (g + 1))) / (np.sqrt(v / (1 - 0.999 ** (g + 1))) + 1e-8)
        e = exposure(theta, Zf)
        tr_s, va_s = sharpe(proxy(e, tr_rows)), sharpe(proxy(e, va_rows))
        hist.append(dict(gen=g, train=tr_s, valid=va_s, mean_exposure_train=float(e[tr_rows].mean())))
        if va_s > best[0]:
            best = (va_s, theta.copy(), g)
        if g % 10 == 0 or g == gens - 1:
            log(f"gen {g} train Sharpe {tr_s:.3f} valid {va_s:.3f} exposure {e[tr_rows].mean():.2f}")
    return best, hist


def block_shuffle(Z, seed, block=63):
    rng = np.random.default_rng(seed)
    n = len(Z); starts = np.arange(0, n, block); rng.shuffle(starts)
    idx = np.concatenate([np.arange(s, min(s + block, n)) for s in starts])
    return Z[idx]


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "train":
        out = {}
        for name, Zf, seeds in (("agent", Z, (0, 1, 2)), ("agent_shuffled_features", None, (0, 1, 2))):
            for s in seeds:
                Zs = Z if Zf is not None else block_shuffle(Z, 100 + s)
                print(f"== {name} seed {s}", flush=True)
                (bv, th, g), hist = train(Zs, seed=s)
                e = exposure(th, Zs)
                out[f"{name}_s{s}"] = dict(theta=th.tolist(), best_gen=g, valid_proxy_sharpe=bv, history=hist,
                                           shuffle_seed=None if Zf is not None else 100 + s,
                                           mean_exposure={k: float(e[mk].mean()) for k, mk in
                                                          (("2013-19", TR), ("2020-21", VA), ("2022-26", dates >= "2022-01-01"))})
                json.dump(dict(features=FEATS, mu=mu.tolist(), sd=sd.tolist(), agents=out),
                          open("results/timing_agents.json", "w"), indent=1, default=float)
    elif mode == "eval":
        from alpha.bhav_panel import BhavMarket
        from alpha.signal import pool_score
        from strategies import Strategy
        from backtest import run, metrics, Config
        M = BhavMarket(P, dividends=True)
        s = pool_score(P, "c_council_real")
        score = np.where(P.mask, s, np.nan)

        class TimedBand(Strategy):
            """Band rule for names (top-20, band 100); exposure E[t] for how much is invested."""
            def __init__(self, E, k=20, band=100): self.E, self.k, self.band = E, k, band
            def reset(self, m): super().reset(m); self.hold = set(); self.e = None
            def decide(self, t, state):
                sc = score[t]
                if not np.isfinite(sc).any():
                    return None
                e = self.E[t]
                w = np.array(state["weights"], dtype=float)
                if e == 0:
                    changed = self.e != 0
                    self.e, self.hold = 0.0, set()
                    return np.zeros(len(sc)) if changed else None
                order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf)))
                rank = {i: j for j, i in enumerate(order)}
                keep = {i for i in self.hold if rank[i] < self.band}
                if len(keep) == len(self.hold) == self.k and e == self.e:
                    return None
                slot = state["nav"] * e / self.k
                px = np.nan_to_num(M.close.values[t])
                new = [i for i in order if i not in keep and np.isfinite(sc[i]) and 0 < px[i] <= slot][: self.k - len(keep)]
                out = np.zeros(len(sc))
                inv = w[list(keep)].sum() if keep else 0.0
                for i in keep:
                    out[i] = w[i] * (e / self.e) if (self.e and e != self.e) else w[i]
                rest = e - out.sum()
                for i in new: out[i] = max(rest, 0) / len(new)
                self.hold, self.e = keep | set(new), e
                return out

        J = json.load(open("results/timing_agents.json"))["agents"]
        ma = (ew / ew.rolling(200).mean() - 1).values
        E = {"Always invested": np.ones(len(dates)),
             "Trend filter (EW > 200d avg: 100%, else 50%)": np.where(np.nan_to_num(ma, nan=1) > 0, 1.0, 0.5)}
        for k_, a in J.items():
            Zs = Z if a["shuffle_seed"] is None else block_shuffle(Z, a["shuffle_seed"])
            E[f"Timing {k_}"] = exposure(np.array(a["theta"]), Zs)
        PER = {"2013-19": ("2013-01-01", "2019-12-31"), "2020-21": ("2020-01-01", "2021-12-31"),
               "2022-26": ("2022-01-01", None), "Full": ("2013-01-01", None)}
        rows = []
        for name, e in E.items():
            res = run(M, TimedBand(e), Config(max_weight=0.25, min_trade_frac=0.01, cash_rate=CASH))
            nav = res.nav_post_tax
            for p, (a_, b_) in PER.items():
                msk = (dates >= a_) & ((dates <= b_) if b_ else True)
                rows.append(dict(strategy=name, period=p, **metrics(nav, a_, b_), mean_exposure=float(e[msk].mean()),
                                 switches=int((np.diff(e) != 0).sum()), trades=res.trades, final=float(nav.iloc[-1])))
            print(name, "final %.0f" % nav.iloc[-1], flush=True)
            pd.DataFrame(rows).to_csv("results/timing_eval.csv", index=False)
        df = pd.DataFrame(rows); pd.set_option("display.width", 250)
        print(df.pivot_table(index="strategy", columns="period", values=["CAGR", "Sharpe", "MaxDD"]).round(3).to_string())
        print(df[df.period == "Full"][["strategy", "mean_exposure", "switches", "trades", "final"]].round(2).to_string())
