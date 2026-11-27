"""Climbing-protection stops (rules in SPEC_CLIMB.md). Run from the history working copy."""
import sys, time; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/pods/int_bt.py").read().split("def bt(")[0].replace('CAP, START, OUT = 1_000_000, "2016-02-01"', 'CAP, START, OUT = 1_000_000, "2012-07-02"'))
MD = np.where(P.mask, (zrank((c.shift(21) / c.shift(252) - 1).values, P.mask) + zrank(dp.rolling(60, min_periods=36).mean().values, P.mask)) / 2, np.nan)
PX = M.close.values; V20 = r.rolling(20, min_periods=15).std().values


class Climb(Strategy):
    def __init__(s, sc, mult, rest, k=20, band=100): s.sc, s.mult, s.rest, s.k, s.band = sc, mult, rest, k, band
    def reset(s, mk):
        super().reset(mk); s.hold, s.cool, s.st = set(), {}, {}; s.resting = 0; s.nstops = 0
    def decide(s, t, st):
        sc = s.sc[t]
        if not np.isfinite(sc).any(): return None
        px = np.nan_to_num(PX[t])
        for i in s.hold:                                     # move the pins
            q = s.st[i]
            if px[i] <= 0: continue
            q["H"] = max(q["H"], px[i])
            if q["H"] >= q["Hpin"] * (1 + q["d"] / 2): q["Hpin"] = q["H"]; q["stop"] = max(q["stop"], q["H"] * (1 - q["d"]))
            if px[i] >= q["e"] * (1 + q["d"]): q["stop"] = max(q["stop"], q["e"])
        stopped = {i for i in s.hold if px[i] > 0 and px[i] <= s.st[i]["stop"]}
        for i in stopped: s.cool[i] = t + 21
        s.nstops += len(stopped)
        if month_end[t]: s.resting = 0
        w = np.array(st["weights"], float)
        order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf))); rank = {i: j for j, i in enumerate(order)}
        keep = {i for i in s.hold if i not in stopped and np.isfinite(sc[i]) and rank[i] < s.band}
        band_out = s.hold - keep - stopped
        if s.rest: s.resting += len(stopped)
        n_new = s.k - len(keep) - (s.resting if s.rest else 0)
        if not stopped and not band_out and n_new <= 0: return None
        slot = st["nav"] / s.k
        new = [i for i in order if i not in keep and np.isfinite(sc[i]) and s.cool.get(i, -1) < t and 0 < px[i] <= slot][: max(n_new, 0)]
        out = np.zeros(len(sc))
        for i in keep: out[i] = w[i]
        if s.rest and not month_end[t]:
            budget = sum(w[i] for i in band_out)          # only money freed by normal band sells; stop money rests in cash
        else:
            budget = 1 - out.sum()
        for i in new:
            out[i] = max(budget, 0) / len(new)
            d = float(np.clip(s.mult * np.nan_to_num(V20[t, i], nan=0.02) * np.sqrt(20), 0.10, 0.30))
            s.st[i] = dict(e=px[i], d=d, H=px[i], Hpin=px[i], stop=px[i] * (1 - d))
        s.hold = keep | set(new)
        for i in list(s.st):
            if i not in s.hold: s.st.pop(i)
        return out


rows = []; t0 = time.time()
for m in (1.5, 2.0, 3.0):
    for rest in (True, False):
        strat = Climb(MD, m, rest)
        res = run(M, strat, Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01))
        a = metrics(res.nav_post_tax, START, None); b = metrics(res.nav_post_tax, "2022-01-01", None)
        rows.append(dict(book=f"climb m={m:g} {'rest' if rest else 'reinvest'}", CAGR=round(float(a["CAGR"]), 4), Sharpe=round(float(a["Sharpe"]), 3),
                         MaxDD=round(float(a["MaxDD"]), 3), CAGR_2022_26=round(float(b["CAGR"]), 4), turnover=round(res.turnover, 2), stops=strat.nstops))
        print(rows[-1], round(time.time() - t0), "s", flush=True)
pd.DataFrame(rows).to_csv("research/stops/climb_metrics.csv", index=False)
