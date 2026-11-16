"""Live version of the research timing agent (research/timing/), for the paper fleet.

The agent sets only HOW MUCH of NAV is invested (1, 0.5 or 0); the band rule still picks WHICH
stocks. Policy, feature standardisation and hysteresis are exactly those of
research/timing/timing.py and the saved weights in research/timing/timing_agents.json.

Differences from the research setting, forced by the data the repo keeps (500 trading days):
- 'strat' (the fully invested band rule's NAV, used by health63 and dd252) is re-simulated in the
  exact engine over the stored window, without dividends;
- the exposure state is carried in the account's state.json; on the first day it is initialised
  by running the hysteresis over the window's history.
vol_ratio has mu = inf / sd = nan in the saved file, so (as in training) it always enters as 0.
"""
import json
import numpy as np, pandas as pd

H = 0.25


def step(cur, v):
    if cur == 1.0 and v < -H: cur = 0.5
    if cur == 0.5 and v > H: cur = 1.0
    if cur == 0.5 and v < -1 - H: cur = 0.0
    if cur == 0.0 and v > -1 + H: cur = 0.5
    return cur


def band_nav(P, score, k=20, band=100):
    """Fully invested band rule NAV in the exact engine (Rs 10L, post-tax), over the stored window."""
    from alpha.bhav_panel import BhavMarket
    from strategies import Strategy
    from backtest import run, Config
    M = BhavMarket(P); px = np.nan_to_num(M.close.values)
    sc_all = np.where(P.mask, score, np.nan)

    class Band(Strategy):
        def reset(s, m): super().reset(m); s.hold = set()
        def decide(s, t, st):
            sc = sc_all[t]
            if not np.isfinite(sc).any(): return None
            w = np.array(st["weights"], float)
            order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf))); rank = {i: j for j, i in enumerate(order)}
            keep = {i for i in s.hold if rank[i] < band}
            if len(keep) == len(s.hold) == k: return None
            slot = st["nav"] / k
            new = [i for i in order if i not in keep and np.isfinite(sc[i]) and 0 < px[t, i] <= slot][: k - len(keep)]
            out = np.zeros(len(sc))
            for i in keep: out[i] = w[i]
            for i in new: out[i] = max(1 - out.sum(), 0) / len(new)
            s.hold = keep | set(new); return out

    first = int(np.argmax(np.isfinite(sc_all).any(1)))
    r = run(M, Band(), Config(capital=1_000_000, start=str(P.dates[first].date()), max_weight=0.25, min_trade_frac=0.01))
    return r.nav_post_tax.reindex(P.dates)


def policy_inputs(P, score, agent_file, agent):
    A = json.load(open(agent_file))
    theta = np.array(A["agents"][agent]["theta"]); mu = np.array(A["mu"], float); sd = np.array(A["sd"], float)
    C = P.raw_close.ffill()
    dr = (C / C.shift(1) - 1).where(P.mask)
    ew_r = dr.mean(1).fillna(0); ew = (1 + ew_r).cumprod()
    ma200 = C.rolling(200, min_periods=150).mean()
    vol20 = ew_r.rolling(20).std()
    strat = band_nav(P, score).ffill().bfill()
    X = pd.DataFrame({
        "ew63": ew / ew.shift(63) - 1,
        "ew252": ew / ew.shift(252) - 1,
        "ew_ma200": ew / ew.rolling(200).mean() - 1,
        "vol_ratio": np.log(vol20 / vol20.rolling(252).median()),
        "breadth": (C > ma200).where(P.mask).mean(1) - 0.5,
        "health63": (strat / strat.shift(63) - 1) - (ew / ew.shift(63) - 1),
        "dd252": strat / strat.rolling(252, min_periods=20).max() - 1,
    }, index=P.dates)
    assert list(X.columns) == A["features"]
    with np.errstate(invalid="ignore"):
        Z = ((X - mu) / sd).fillna(0).clip(-4, 4)
    u = Z.values @ theta[1:] + theta[0]
    valid = X.drop(columns="vol_ratio").notna().all(1).values
    return pd.Series(u, index=P.dates), valid, X


def exposure_today(P, score, t, prev_e, agent_file, agent):
    """Exposure for orders written after close t, plus a small record for the order file."""
    u, valid, X = policy_inputs(P, score, agent_file, agent)
    if prev_e is None:                       # first day: run the hysteresis over stored history
        cur = 1.0
        for j in np.where(valid[: t + 1])[0]:
            cur = step(cur, u.iloc[j])
        e = cur
    else:
        e = step(float(prev_e), u.iloc[t])
    return e, dict(u=float(u.iloc[t]), features={k: float(v) for k, v in X.iloc[t].items()})
