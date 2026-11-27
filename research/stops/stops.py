"""Stop-losses on momentum + delivery (rules in SPEC.md). Run from the history working copy."""
import sys, time, json; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/pods/int_bt.py").read().split("def bt(")[0].replace('CAP, START, OUT = 1_000_000, "2016-02-01"', 'CAP, START, OUT = 1_000_000, "2012-07-02"'))
MD = np.where(P.mask, (zrank((c.shift(21) / c.shift(252) - 1).values, P.mask) + zrank(dp.rolling(60, min_periods=36).mean().values, P.mask)) / 2, np.nan)
PX = M.close.values


class StopBand(Strategy):
    def __init__(s, sc, kind=None, x=None, k=20, band=100): s.sc, s.kind, s.x, s.k, s.band = sc, kind, x, k, band
    def reset(s, m):
        super().reset(m); s.hold, s.ref, s.mx, s.cool = set(), {}, {}, {}
        s.e, s.peak, s.until, s.nstops = 1.0, None, -1, 0
    def decide(s, t, st):
        sc = s.sc[t]
        if not np.isfinite(sc).any(): return None
        px = np.nan_to_num(PX[t]); nav = st["nav"]
        for i in s.hold: s.mx[i] = max(s.mx.get(i, px[i]), px[i])
        stopped = set()
        if s.kind == "fixed": stopped = {i for i in s.hold if px[i] > 0 and px[i] <= s.ref[i] * (1 - s.x)}
        if s.kind == "trailing": stopped = {i for i in s.hold if px[i] > 0 and px[i] <= s.mx[i] * (1 - s.x)}
        e_prev = s.e
        if s.kind == "portfolio":
            if s.e == 1.0:
                s.peak = nav if s.peak is None else max(s.peak, nav)
                if nav < s.peak * (1 - s.x): s.e, s.until = 0.5, t + 21; s.nstops += 1
            elif t >= s.until:
                s.e, s.peak = 1.0, nav
        for i in stopped: s.cool[i] = t + 21
        s.nstops += len(stopped)
        w = np.array(st["weights"], float)
        order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf))); rank = {i: j for j, i in enumerate(order)}
        keep = {i for i in s.hold if i not in stopped and np.isfinite(sc[i]) and rank[i] < s.band}
        if len(keep) == len(s.hold) == s.k and s.e == e_prev: return None
        slot = nav * s.e / s.k
        new = [i for i in order if i not in keep and np.isfinite(sc[i]) and s.cool.get(i, -1) < t and 0 < px[i] <= max(slot, nav / s.k)][: s.k - len(keep)]
        out = np.zeros(len(sc)); scale = s.e / e_prev if e_prev else 1.0
        for i in keep: out[i] = w[i] * scale
        rest = s.e - out.sum()
        for i in new: out[i] = max(rest, 0) / len(new); s.ref[i] = px[i]; s.mx[i] = px[i]
        if out.sum() > s.e + 1e-9: out *= s.e / out.sum()
        for i in list(s.ref):
            if i not in keep and i not in new: s.ref.pop(i, None); s.mx.pop(i, None)
        s.hold = keep | set(new); return out


rows = []; t0 = time.time()
runs = [("base (no stop)", None, None)] + [(f"{kd} {int(x*100)}%", kd, x) for kd in ("fixed", "trailing", "portfolio") for x in (0.10, 0.15, 0.20)]
for name, kd, x in runs:
    strat = StopBand(MD, kd, x)
    r = run(M, strat, Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01))
    m = metrics(r.nav_post_tax, START, None); m22 = metrics(r.nav_post_tax, "2022-01-01", None)
    rows.append(dict(book=name, CAGR=round(float(m["CAGR"]), 4), Sharpe=round(float(m["Sharpe"]), 3), MaxDD=round(float(m["MaxDD"]), 3),
                     CAGR_2022_26=round(float(m22["CAGR"]), 4), turnover=round(r.turnover, 2), stop_events=strat.nstops))
    print(rows[-1], round(time.time() - t0), "s", flush=True)
pd.DataFrame(rows).to_csv("research/stops/stops_metrics.csv", index=False)
