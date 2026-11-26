"""Long-short pods (rules fixed in SPEC_LS.md before this was run). Research only.

Run from the history working copy (see README.md):  python3 -W ignore research/pods/ls_bt.py
Value-based daily simulator: cash long leg + stock-futures short leg (or NIFTY-futures hedge),
decide at close, fill at next open, today's cost schedule, pre-tax.
"""
import sys, os, glob, time
sys.path.insert(0, ".")
import numpy as np, pandas as pd
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
from alpha.bhav_panel import BhavMarket, build, parse_all, stitch_renames
from alpha.signal import pool_score
from costs import explicit_costs, implicit_cost_frac
from backtest import metrics

t0 = time.time()
OUT = "research/pods/"
P = CouncilPanel(); M = BhavMarket(P); B = build()
D, N = P.dates, list(P.names); nD, nN = len(D), len(N); col = {n: j for j, n in enumerate(N)}
dpos = {d: i for i, d in enumerate(D)}
O = M.open.values; C = M.close.values                     # back-adjusted (share units consistent)
SIG, SPR, MV = M.sigma.values, M.spread.values, M.medvol.values
FAC = B["factor"].reindex(index=D, columns=N).fillna(1.0).values
MASK = P.mask

# ---------- futures panel: active contract per (day, stock), roll when <= 3 trading days left
long = parse_all(); long = long[long["isin"].astype(str).str.startswith("INE")]
long, _ = stitch_renames(long)
k_ = long[["date", "sym", "id"]].drop_duplicates(["date", "sym"])
symid = dict(zip(zip(k_["date"], k_["sym"]), k_["id"]))
fr = []
for f in sorted(glob.glob("data/fut/*.csv")):
    x = pd.read_csv(f); x["date"] = pd.Timestamp(os.path.basename(f)[:8]); fr.append(x)
F = pd.concat(fr, ignore_index=True); F["exp"] = pd.to_datetime(F["exp"])
F = F[F["date"].isin(dpos)]
print("futures rows", len(F), round(time.time() - t0), "s", flush=True)
cal = np.array(D.values, dtype="datetime64[D]")


def tdays_left(d, e):    # trading days from d (exclusive) to expiry e (inclusive)
    return np.searchsorted(cal, np.datetime64(e, "D"), side="right") - np.searchsorted(cal, np.datetime64(d, "D"), side="right")


# price lookup by (date, symbol-or-id, expiry)
F["tl"] = [tdays_left(d, e) for d, e in zip(F["date"].values, F["exp"].values)]
stk = F[F.kind == "stk"].copy()
stk["id"] = [symid.get((d, s)) for d, s in zip(stk["date"], stk["symbol"])]
stk["id"] = stk["id"].fillna(stk["symbol"])
stk = stk[stk["id"].isin(col)]
FP = {(dpos[d], col[i], e): (o, c) for d, i, e, o, c in zip(stk["date"], stk["id"], stk["exp"].values.astype("datetime64[D]"), stk["open"], stk["close"])}
act = stk[stk.tl > 3].sort_values("exp").groupby(["date", "id"]).head(1)
ACT = {}                                   # (t, j) -> active expiry
for d, i, e in zip(act["date"], act["id"], act["exp"].values.astype("datetime64[D]")): ACT[(dpos[d], col[i])] = e
HASFUT = np.zeros((nD, nN), bool)
for (t, j) in ACT: HASFUT[t, j] = True
nf = F[(F.kind == "idx") & (F.symbol == "NIFTY")]
NFP = {(dpos[d], e): (o, c) for d, e, o, c in zip(nf["date"], nf["exp"].values.astype("datetime64[D]"), nf["open"], nf["close"])}
nact = nf[nf.tl > 3].sort_values("exp").groupby("date").head(1)
NACT = {dpos[d]: e for d, e in zip(nact["date"], nact["exp"].values.astype("datetime64[D]"))}
BAN = np.zeros((nD, nN), bool)
for f in glob.glob("data/ban/*.txt"):
    d = pd.Timestamp(os.path.basename(f)[:8])
    if d in dpos:
        for s in open(f).read().split():
            j = col.get(symid.get((d, s), s))
            if j is not None: BAN[dpos[d], j] = True
I = pd.read_csv("data/indices/all_long.csv", dtype={"date": str})
I = I[I["Index Name"].str.strip().isin(["S&P CNX Nifty", "CNX Nifty", "Nifty 50"])]
NIFTY = pd.Series(I["Closing Index Value"].values, index=pd.to_datetime(I["date"])).sort_index()
NIFTY = NIFTY[~NIFTY.index.duplicated()].reindex(D).ffill()
print("panels ready", round(time.time() - t0), "s; F&O names/day median", int(np.median(HASFUT.sum(1)[HASFUT.sum(1) > 0])), flush=True)

# ---------- signals
c = pd.DataFrame(P.feat["close"], index=D).ffill()
SC = {"trend": np.where(MASK, (c.shift(21) / c.shift(252) - 1).values, np.nan),
      "council": np.where(MASK, pool_score(P, "c_council_real"), np.nan)}
month_end = np.r_[D[1:].month != D[:-1].month, True]

FUT_BROK, FUT_STT, FUT_EXCH, FUT_SEBI, FUT_STAMP, GST = 20.0, 2e-4, 1.73e-5, 1e-6, 2e-5, 0.18


def fut_cost(v, side, t, j, mult):
    brok = min(FUT_BROK, 3e-4 * v)
    exp = brok + FUT_EXCH * v + FUT_SEBI * v
    tot = exp + GST * (brok + FUT_EXCH * v + FUT_SEBI * v) + (FUT_STT * v if side == "sell" else FUT_STAMP * v)
    if j is not None and np.isfinite(C[t - 1, j]) and C[t - 1, j] > 0:
        tot += float(np.nan_to_num(implicit_cost_frac(v / C[t - 1, j], SPR[t - 1, j], SIG[t - 1, j], MV[t - 1, j]), nan=0.002)) * v * mult
    return tot


def cash_cost(v, side, t, j, mult):
    e = explicit_costs(v, side)["total"]
    p = C[t - 1, j]
    if not (np.isfinite(p) and p > 0): return e + 0.004 * v * mult
    return e + float(np.nan_to_num(implicit_cost_frac(v / p, SPR[t - 1, j], SIG[t - 1, j], MV[t - 1, j]), nan=0.004)) * v * mult


def sim(sig, kL=20, kS=15, longw=0.8, shortw=0.8, mode="ls", mult=1.0, cap=2e7, start="2016-02-01"):
    """mode: 'ls' (short stock futures), 'hedge' (short NIFTY futures x beta), 'long', 'ew'."""
    t_start = dpos[D[D >= start][0]]
    cash, L, S = cap, {}, {}           # L: j -> value; S: j -> [notional(neg), expiry, last price]
    H = None                            # NIFTY hedge: [notional(neg), expiry, last]
    pend = None                         # decisions made at t-1 close
    nav = np.full(nD, np.nan); shortpl = np.zeros(nD); events = 0; turn = 0.0; costs = 0.0
    lret = np.full(nD, np.nan)
    for t in range(t_start, nD):
        # ---- 1. overnight: move positions from previous close to today's open; roll futures
        for j in list(L):
            if np.isfinite(O[t, j]) and np.isfinite(C[t - 1, j]) and C[t - 1, j] > 0: L[j] *= O[t, j] / C[t - 1, j]
        def fut_overnight(pos, key_open, j=None):
            n, e, last = pos
            po = key_open(e)
            if po is None or not np.isfinite(po[0]) or po[0] <= 0 or last <= 0: return pos, 0.0
            f = FAC[t, j] if j is not None else 1.0
            pl = n * (po[0] / (last * f) - 1)
            if j is not None and abs(po[0] / (last * f) - 1) > 0.4 and np.isfinite(O[t, j]) and C[t - 1, j] > 0:
                pl = n * (O[t, j] / C[t - 1, j] - 1)       # unrecorded corporate action: use the stock
            return [n + pl, e, po[0]], pl
        dpl = 0.0
        for j in list(S):
            n, e, last = S[j]
            if np.datetime64(D[t], "D") > e:               # expired (stock left F&O): settled at last close
                del S[j]; continue
            S[j], pl = fut_overnight(S[j], lambda e: FP.get((t, j, e)), j); dpl += pl
        if H is not None:
            H, pl = fut_overnight(H, lambda e: NFP.get((t, e))); dpl += pl
        cash += dpl
        # rolls at the open
        for j in list(S):
            n, e, last = S[j]; ne = ACT.get((t, j))
            if ne is not None and ne != e and tdays_left(D[t], e) <= 3 and FP.get((t, j, ne)):
                v = abs(n); k = fut_cost(v, "buy", t, j, mult) + fut_cost(v, "sell", t, j, mult)
                cash -= k; costs += k; S[j] = [n, ne, FP[(t, j, ne)][0]]
        if H is not None:
            n, e, last = H; ne = NACT.get(t)
            if ne is not None and ne != e and tdays_left(D[t], e) <= 3 and NFP.get((t, ne)):
                k = fut_cost(abs(n), "buy", t, None, mult) + fut_cost(abs(n), "sell", t, None, mult)
                cash -= k; costs += k; H = [n, ne, NFP[(t, ne)][0]]
        # ---- 2. execute yesterday's decisions at the open
        if pend is not None:
            tL, tS, tH = pend
            for j in list(L):                                  # sells first
                tgt = tL.get(j, 0.0)
                gone = M.delist_day[j] >= 0 and t > M.delist_day[j]      # delisted: exit at last price
                if tgt < L[j] - 1e-6 and (np.isfinite(O[t, j]) or gone):
                    v = L[j] - tgt; k = cash_cost(v, "sell", t, j, mult)
                    cash += v - k; costs += k; turn += v; L[j] = tgt
                    if L[j] <= 1e-6: del L[j]
            for j, tgt in tL.items():
                cur = L.get(j, 0.0)
                if tgt > cur + 1e-6 and np.isfinite(O[t, j]):
                    v = min(tgt - cur, max(cash - 0, 0)); k = cash_cost(v, "buy", t, j, mult)
                    if v <= 0: continue
                    cash -= v + k; costs += k; turn += v; L[j] = cur + v
            for j in list(S):                                  # covers / resizes
                tgt = tS.get(j, 0.0)
                n, e, last = S[j]
                if abs(n) > tgt + 1e-6 and FP.get((t, j, e)):
                    v = abs(n) - tgt; k = fut_cost(v, "buy", t, j, mult); cash -= k; costs += k; turn += v
                    S[j][0] = -tgt
                    if tgt <= 1e-6: del S[j]
            for j, tgt in tS.items():                          # new shorts / increases
                if BAN[t, j] and j not in S: continue
                e = S[j][1] if j in S else ACT.get((t, j))
                if e is None or not FP.get((t, j, e)): continue
                cur = abs(S[j][0]) if j in S else 0.0
                if tgt > cur + 1e-6:
                    if BAN[t, j]: continue
                    v = tgt - cur; k = fut_cost(v, "sell", t, j, mult); cash -= k; costs += k; turn += v
                    if j in S: S[j][0] -= v
                    else: S[j] = [-v, e, FP[(t, j, e)][0]]
            if tH is not None:
                e = H[1] if H is not None else NACT.get(t)
                if e is not None and NFP.get((t, e)):
                    cur = abs(H[0]) if H is not None else 0.0
                    v = abs(tH - cur)
                    if v > 0.01 * (cash + sum(L.values())):
                        k = fut_cost(v, "sell" if tH > cur else "buy", t, None, mult); cash -= k; costs += k
                        H = [-tH, e, NFP[(t, e)][0]] if H is None else [-tH, H[1], H[2]]
            pend = None
        # ---- 3. open -> close
        lv0 = sum(L.values())
        for j in list(L):
            if np.isfinite(C[t, j]) and np.isfinite(O[t, j]) and O[t, j] > 0: L[j] *= C[t, j] / O[t, j]
        lret[t] = sum(L.values()) / lv0 - 1 if lv0 > 0 else np.nan
        dpl2 = 0.0
        for j in list(S):
            n, e, last = S[j]; p = FP.get((t, j, e))
            if p and np.isfinite(p[1]) and p[1] > 0 and last > 0:
                pl = n * (p[1] / last - 1)
                if abs(p[1] / last - 1) > 0.4 and np.isfinite(C[t, j]) and O[t, j] > 0: pl = n * (C[t, j] / O[t, j] - 1)
                S[j] = [n + pl, e, p[1]]; dpl2 += pl
        if H is not None:
            n, e, last = H; p = NFP.get((t, e))
            if p and p[1] > 0 and last > 0:
                pl = n * (p[1] / last - 1); H = [n + pl, e, p[1]]; dpl2 += pl
        cash += dpl2; shortpl[t] = dpl + dpl2
        NAV = cash + sum(L.values()); nav[t] = NAV
        if NAV <= 0: break
        # ---- 4. margin check, then decide for tomorrow
        req = 0.20 * sum(abs(s[0]) for s in S.values()) + (0.12 * abs(H[0]) if H is not None else 0.0)
        s = sig[t] if sig is not None else None
        tL, tS, tH = dict(L), {j: abs(v[0]) for j, v in S.items()}, (abs(H[0]) if H is not None else None)
        changed = False
        if mode == "ew":
            if month_end[t] or not L:
                m = np.where(MASK[t] & np.isfinite(C[t]))[0]
                tL = {j: longw * NAV / len(m) for j in m}; changed = True
        else:
            ok = np.isfinite(s)
            order = np.argsort(-np.where(ok, s, -np.inf)); rank = np.empty(nN, int); rank[order] = np.arange(nN)
            keep = [j for j in L if ok[j] and rank[j] < 5 * kL]
            if len(keep) < len(L) or len(L) < kL or month_end[t]:
                new = [j for j in order[: 5 * kL] if j not in keep and ok[j]][: kL - len(keep)]
                names = keep + new
                if month_end[t]:
                    tL = {j: longw * NAV / kL for j in names}
                else:
                    free = max(longw * NAV - sum(L[j] for j in keep), 0)
                    tL = {j: L[j] for j in keep}; tL.update({j: free / len(new) for j in new} if new else {})
                changed = True
            if mode == "ls":
                fo = ok & HASFUT[t]
                ford = np.argsort(np.where(fo, s, np.inf)); frank = np.full(nN, 10 ** 6); frank[ford[: fo.sum()]] = np.arange(fo.sum())
                keepS = [j for j in S if fo[j] and frank[j] < 3 * kS]
                if len(keepS) < len(S) or len(S) < kS or month_end[t]:
                    newS = [j for j in ford[: 3 * kS] if fo[j] and j not in keepS and not BAN[t, j]][: kS - len(keepS)]
                    if month_end[t]:
                        tS = {j: shortw * NAV / kS for j in keepS + newS}
                    else:
                        free = max(shortw * NAV - sum(abs(S[j][0]) for j in keepS), 0)
                        tS = {j: abs(S[j][0]) for j in keepS}; tS.update({j: free / len(newS) for j in newS} if newS else {})
                    changed = True
            if mode == "hedge" and month_end[t] and t - t_start > 60:
                lr = pd.Series(lret[t - 60:t + 1]); nr = NIFTY.iloc[t - 60:t + 1].pct_change().reset_index(drop=True)
                ok2 = lr.notna() & nr.notna()
                beta = np.clip(np.cov(lr[ok2], nr[ok2])[0, 1] / nr[ok2].var(), 0, 1.5) if ok2.sum() > 40 else 1.0
                tH = beta * sum(tL.values()); changed = True
        # margin: if the buffer is short, sell longs pro rata
        if cash < req:
            need = req + 0.02 * NAV - cash; lv = sum(tL.values())
            if lv > 0: tL = {j: v * max(1 - need / lv, 0) for j, v in tL.items()}; events += 1; changed = True
        if changed: pend = (tL, tS, tH)
    navs = pd.Series(nav, index=D).dropna()
    return dict(nav=navs, shortpl=pd.Series(shortpl, index=D).loc[navs.index], events=events,
                turnover=turn / cap / (len(navs) / 252), costs=costs)


PER = [("2016-19", "2016-02-01", "2019-12-31"), ("2020-21", "2020-01-01", "2021-12-31"),
       ("2022-26", "2022-01-01", None), ("all", "2016-02-01", None)]
rows, navs, spl = [], {}, {}
def rec(name, r, **kw):
    navs[name] = r["nav"]; spl[name] = r["shortpl"]
    nr = NIFTY.reindex(r["nav"].index).pct_change(); dr = r["nav"].pct_change()
    for pn, a, b in PER:
        m = metrics(r["nav"], a, b)
        rows.append(dict(run=name, period=pn, events=r["events"], turnover=round(r["turnover"], 2),
                         costs_cr=round(r["costs"] / 1e7, 3), corr_nifty=round(dr.corr(nr), 3), **kw,
                         **{k: round(v, 4) for k, v in m.items()}))
    print(name, f"CAGR {metrics(r['nav'], '2016-02-01', None)['CAGR']:.3f} Sharpe {metrics(r['nav'], '2016-02-01', None)['Sharpe']:.2f}",
          f"events {r['events']}", round(time.time() - t0), "s", flush=True)

rec("Nifty 50 index", dict(nav=NIFTY.loc["2016-02-01":] * 1.0, shortpl=pd.Series(0.0, index=NIFTY.loc["2016-02-01":].index), events=0, turnover=0, costs=0), book="bench")
rec("EW universe", sim(None, mode="ew", longw=1.0), book="bench")
for s in ("trend", "council"):
    rec(f"Long-{s}", sim(SC[s], mode="long", longw=1.0), book=f"long-{s}")
    rec(f"LS-{s} L20 S15", sim(SC[s]), book=f"ls-{s}", kL=20, kS=15)
    rec(f"LS-{s} L20 S15 stress", sim(SC[s], mult=2.0), book=f"ls-{s}", kL=20, kS=15, stress=True)
    for kL in (15, 20, 25):
        for kS in (10, 15, 20):
            if (kL, kS) != (20, 15): rec(f"LS-{s} L{kL} S{kS}", sim(SC[s], kL=kL, kS=kS), book=f"ls-{s}", kL=kL, kS=kS)
rec("Hedged-trend", sim(SC["trend"], mode="hedge"), book="hedged-trend")

R = pd.DataFrame(rows); R.to_csv(OUT + "ls_metrics.csv", index=False)
NV = pd.DataFrame(navs); NV.resample("ME").last().to_csv(OUT + "ls_navs_monthly.csv")
Y = NV.resample("YE").last(); Y = Y.pct_change().fillna(Y.iloc[0] / NV.bfill().iloc[0] - 1)
Y.to_csv(OUT + "ls_years.csv"); NV.to_pickle("/tmp/ls_navs.pkl"); pd.DataFrame(spl).to_pickle("/tmp/ls_shortpl.pkl")
print("done", round(time.time() - t0), "s")
