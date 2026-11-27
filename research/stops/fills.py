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


FILL = "trigger"
def sim(kind=None, x=0.15, mult=2.0, rest=False, k=20, band=100, cap=1e6, tax=False):
    BAS, BT = {}, {}; fy_st = fy_lt = 0.0; cf = 0.0; cur_fy = None; paid = 0.0
    cash, U, ST = cap, {}, {}             # U: units (adjusted); ST: stop state per holding
    cool, resting, pend = {}, 0, None
    nav = np.full(len(D), np.nan); nstops = gaps = locked = 0
    def fy(d): return d.year if d.month >= 4 else d.year - 1
    def tax_due(st_, lt_, cf_):
        st_ = st_ - cf_ if st_ > 0 else st_
        if st_ < 0: lt_ += st_; st_ = 0.0
        return 1.04 * (0.20 * max(st_, 0.0) + 0.125 * max(lt_ - 125_000.0, 0.0)), (-(st_ + lt_) if st_ + lt_ < 0 else 0.0)
    def realise(j, proceeds, t):
        nonlocal fy_st, fy_lt
        if not tax or j not in BAS: BAS.pop(j, None); BT.pop(j, None); return
        g = proceeds - BAS.pop(j); held = t - BT.pop(j)
        if held < 252: fy_st += g
        else: fy_lt += g
    for t in range(t_start, len(D)):
        if tax:
            f = fy(D[t])
            if cur_fy is None: cur_fy = f
            if f != cur_fy:
                due, cf = tax_due(fy_st, fy_lt, cf); cash -= due; paid += due; fy_st = fy_lt = 0.0; cur_fy = f
        # 1. execute yesterday's close decisions at the open
        if pend is not None:
            sells, buys = pend
            for j in sells:
                if j in U and np.isfinite(Oa[t, j]) and Oa[t, j] > 0:
                    v = U.pop(j) * Oa[t, j]; c_ = cost(v, "sell", t, j); cash += v - c_; ST.pop(j, None); realise(j, v - c_, t)
            for j, v in buys:
                if np.isfinite(Oa[t, j]) and Oa[t, j] > 0 and v > 0:
                    v = min(v, cash); c_ = cost(v, "buy", t, j); v -= c_; cash -= v + c_
                    U[j] = v / Oa[t, j]; BAS[j] = v + c_; BT[j] = t
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
                fill = s if FILL == "trigger" else (s * 0.99 if FILL == "1pct" else (s + l) / 2)
            if fill is not None:
                v = U.pop(j) * fill; c_ = cost(v, "sell", t, j); cash += v - c_; ST.pop(j); cool[j] = t + 21; nstops += 1; realise(j, v - c_, t)
                if rest: resting += 1
        # 3. close: mark, move pins
        V = {j: U[j] * Ca[t, j] for j in U}; NAV = cash + sum(V.values())
        nav[t] = NAV - (tax_due(fy_st, fy_lt, cf)[0] if tax else 0.0)
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




rows = []
base = sim(tax=True)[0]; a0 = metrics(base, START, None)
rows.append(dict(book="with tax: base", CAGR=round(float(a0["CAGR"]), 4), Sharpe=round(float(a0["Sharpe"]), 3), MaxDD=round(float(a0["MaxDD"]), 3)))
for f in ("trigger", "1pct", "halfway"):
    FILL = f; nav, n, g, lk = sim(kind="climb", mult=2.0, rest=True, tax=True); a = metrics(nav, START, None)
    rows.append(dict(book=f"with tax: climb m=2, rest, fill={f}", CAGR=round(float(a["CAGR"]), 4), Sharpe=round(float(a["Sharpe"]), 3), MaxDD=round(float(a["MaxDD"]), 3), stops=n))
    print(rows[-1], flush=True)
print(rows[0]); pd.DataFrame(rows).to_csv("research/stops/fill_metrics.csv", index=False)
