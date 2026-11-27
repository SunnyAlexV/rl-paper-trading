"""Stops executed intraday like real stop orders (rules in SPEC_INTRADAY.md). Run from the history working copy."""
import sys, time; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/stops/climb.py").read().split("class Climb")[0])     # P, M, MD, PX(close), V20, month_end, metrics
from costs import explicit_costs, implicit_cost_frac
Oa, Ha, La, Ca = P.feat["open"], P.feat["high"], P.feat["low"], M.close.values
SPR, SIG, MV = M.spread.values, M.sigma.values, M.medvol.values
t_start = int(np.searchsorted(D, pd.Timestamp(START)))


def cost(v, side, t, j):
    p = Ca[t - 1, j]
    imp = implicit_cost_frac(v / p, SPR[t - 1, j], SIG[t - 1, j], MV[t - 1, j]) if p > 0 else 0.004
    return explicit_costs(v, side)["total"] + float(np.nan_to_num(imp, nan=0.004)) * v


def sim(kind=None, x=0.15, mult=2.0, rest=False, k=20, band=100, cap=1e6):
    cash, U, ST = cap, {}, {}             # U: units (adjusted); ST: stop state per holding
    cool, resting, pend = {}, 0, None
    nav = np.full(len(D), np.nan); nstops = gaps = locked = 0
    for t in range(t_start, len(D)):
        # 1. execute yesterday's close decisions at the open
        if pend is not None:
            sells, buys = pend
            for j in sells:
                if j in U and np.isfinite(Oa[t, j]) and Oa[t, j] > 0:
                    v = U.pop(j) * Oa[t, j]; cash += v - cost(v, "sell", t, j); ST.pop(j, None)
            for j, v in buys:
                if np.isfinite(Oa[t, j]) and Oa[t, j] > 0 and v > 0:
                    v = min(v, cash); c_ = cost(v, "buy", t, j); v -= c_; cash -= v + c_
                    U[j] = v / Oa[t, j]
                    if kind:
                        d = float(np.clip(mult * np.nan_to_num(V20[t - 1, j], nan=0.02) * np.sqrt(20), 0.10, 0.30)) if kind == "climb" else x
                        e = Oa[t, j]; ST[j] = dict(e=e, d=d, H=e, Hpin=e, stop=e * (1 - d))
            pend = None
        # 2. intraday stops (levels set at earlier closes)
        for j in list(U):
            if j not in ST: continue
            s, o, h, l = ST[j]["stop"], Oa[t, j], Ha[t, j], La[t, j]
            if not (np.isfinite(o) and o > 0): continue
            fill = None
            if o <= s:
                if np.isfinite(h) and np.isfinite(l) and h <= l * 1.0001: locked += 1; continue      # stuck at lower circuit
                fill = o; gaps += 1
            elif np.isfinite(l) and l <= s:
                fill = s
            if fill is not None:
                v = U.pop(j) * fill; cash += v - cost(v, "sell", t, j); ST.pop(j); cool[j] = t + 21; nstops += 1
                if rest: resting += 1
        # 3. close: mark, move pins
        V = {j: U[j] * Ca[t, j] for j in U}; NAV = cash + sum(V.values()); nav[t] = NAV
        for j, q in ST.items():
            p = Ca[t, j]
            if not (p > 0): continue
            if kind == "trailing": q["H"] = max(q["H"], p); q["stop"] = max(q["stop"], q["H"] * (1 - q["d"]))
            if kind == "climb":
                q["H"] = max(q["H"], p)
                if q["H"] >= q["Hpin"] * (1 + q["d"] / 2): q["Hpin"] = q["H"]; q["stop"] = max(q["stop"], q["H"] * (1 - q["d"]))
                if p >= q["e"] * (1 + q["d"]): q["stop"] = max(q["stop"], q["e"])
        if month_end[t]: resting = 0
        # 4. decide for the next open (band rule)
        sc = MD[t]
        if not np.isfinite(sc).any(): continue
        order = np.argsort(-np.where(np.isfinite(sc), sc, -np.inf)); rank = np.empty(len(sc), int); rank[order] = np.arange(len(sc))
        sells = [j for j in U if not (np.isfinite(sc[j]) and rank[j] < band)]
        keep = [j for j in U if j not in sells]
        n_new = k - len(keep) - resting
        if n_new <= 0 and not sells: continue
        new = [j for j in order[: 5 * band] if np.isfinite(sc[j]) and j not in U and cool.get(j, -1) < t and Ca[t, j] > 0][: max(n_new, 0)]
        budget = cash + sum(V[j] for j in sells) - resting * (NAV / k)
        per = min(max(budget, 0) / len(new), 0.075 * NAV) if new else 0
        pend = (sells, [(j, per) for j in new])
    s = pd.Series(nav, index=D).dropna()
    return s, nstops, gaps, locked


rows = []; t0 = time.time()
for name, kw in [("base (no stop)", {}), ("fixed 15%", dict(kind="fixed", x=0.15)), ("trailing 15%", dict(kind="trailing", x=0.15)),
                 ("climb m=2, rest", dict(kind="climb", rest=True)), ("climb m=2, reinvest", dict(kind="climb"))]:
    nav, n, g, lk = sim(**kw); a = metrics(nav, START, None)
    rows.append(dict(book=name, CAGR=round(float(a["CAGR"]), 4), Sharpe=round(float(a["Sharpe"]), 3), MaxDD=round(float(a["MaxDD"]), 3),
                     stops=n, filled_at_gap_open=g, blocked_lower_circuit_days=lk))
    print(rows[-1], round(time.time() - t0), "s", flush=True)
pd.DataFrame(rows).to_csv("research/stops/intraday_metrics.csv", index=False)
