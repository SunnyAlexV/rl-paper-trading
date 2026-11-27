"""Agent v2, the diagnostic batter (rules in SPEC.md, fixed before this code). Research only.

Run from the history working copy:  python3 -W ignore research/agent_v2/agent_v2.py
"""
import sys, time, json, itertools
sys.path.insert(0, ".")
import numpy as np, pandas as pd
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
from alpha.bhav_panel import BhavMarket, build
from strategies import Strategy
from backtest import run, metrics, Config
from costs import FeeSchedule, implicit_cost_frac

import os
STAGE2 = bool(os.environ.get("STAGE2"))   # diagnostic: all fees and tax
t0 = time.time(); OUT = "research/agent_v2/" + ("stage2_" if STAGE2 else "")
def log(*x): print(f"[{time.time() - t0:6.0f}s]", *x, flush=True)

P = CouncilPanel(); M = BhavMarket(P); B = build()
D, names = P.dates, list(P.names); T, N = len(D), len(names); MASK = P.mask
F = lambda k: pd.DataFrame(P.feat[k], index=D)
c = F("close").ffill(); ret = c.pct_change()
vol, dp, dv = F("volume"), F("deliv_pct"), F("deliv_val")
tv = B["tv"].reindex(index=D, columns=P.names)

# ---------------- 1. symptoms (backward-looking)
def mm(x, w, mp=None): return x.rolling(w, min_periods=mp or max(2, int(w * 0.6))).mean()
S = {}
S["5-day return"] = c / c.shift(5) - 1
S["20-day return"] = c / c.shift(20) - 1
S["60-day return"] = c / c.shift(60) - 1
S["12-month return (skip 1m)"] = c.shift(21) / c.shift(252) - 1
S["closeness to 250-day high"] = c / c.rolling(250, min_periods=200).max()
S["height above 60-day low"] = c / c.rolling(60, min_periods=40).min()
S["20-day volatility"] = ret.rolling(20, min_periods=15).std()
S["250-day volatility"] = ret.rolling(250, min_periods=200).std()
S["volatility shift"] = S["20-day volatility"] / S["250-day volatility"]
S["volume surge"] = mm(vol, 5) / mm(vol, 60)
S["size"] = np.log(tv.rolling(60, min_periods=40).median())
S["delivery share"] = mm(dp, 20)
S["delivery trend"] = mm(dp, 20) - mm(dp, 120)
S["delivery value surge"] = mm(dv, 5) / mm(dv, 60)
S["futures OI change"] = F("oi_chg").rolling(20, min_periods=12).sum()
S["futures basis"] = mm(F("basis"), 5)
S["basis change"] = mm(F("basis"), 5) - mm(F("basis"), 60)
S["put/call ratio"] = mm(F("pcr"), 20)
def xrank(x): return x.where(MASK).rank(axis=1, pct=True)
S["price-delivery divergence"] = xrank(S["20-day return"]) - xrank(S["delivery trend"])
S["hollow volume"] = xrank(S["volume surge"]) - xrank(S["delivery value surge"])
SYM = list(S); K = len(SYM)
X = np.zeros((T, N, K), np.int8)
for k, s in enumerate(SYM):
    r = xrank(S[s].replace([np.inf, -np.inf], np.nan)).values
    X[:, :, k] = np.where(r >= 2 / 3, 1, np.where(r <= 1 / 3, -1, 0))
log("symptoms", K)

# market context (point in time against its own trailing 750 days)
mret = ret.where(MASK).mean(axis=1)
ctx_raw = {"market trend": (1 + mret).rolling(60).apply(np.prod, raw=True) - 1,
           "breadth": (c > c.rolling(200, min_periods=150).mean()).where(MASK).mean(axis=1),
           "market stress": mret.rolling(20).std()}
CTXN = list(ctx_raw)
CTX = np.zeros((T, 3), np.int8)
for j, k in enumerate(CTXN):
    pr = ctx_raw[k].rolling(750, min_periods=250).rank(pct=True).values
    CTX[:, j] = np.where(pr >= 2 / 3, 1, np.where(pr <= 1 / 3, -1, 0))

# ---------------- 3. outcome of every pitch: 60-day excess return net of round-trip spread + impact
o = M.open.ffill()
fwd = (o.shift(-61) / o.shift(-1) - 1).where(MASK)
exc = fwd.sub(fwd.mean(axis=1), axis=0)
q = 50_000 / M.close.replace(0, np.nan)
half = pd.DataFrame(implicit_cost_frac(q.values, M.spread.values, M.sigma.values, M.medvol.values), index=D, columns=P.names)
Y = (exc - 2 * half).values
first = int(np.argmax(np.isfinite(S["250-day volatility"].where(MASK)).sum(axis=1).values > 100))
SAMP = np.arange(first, T - 61, 5); nS = len(SAMP)
log("samples", nS, "from", D[first].date())

# ---------------- 2. setups: singles (k, s) and pairs (a, b, sa, sb); per sample day mean outcome and count
SING = [(k, s) for k in range(K) for s in (-1, 1)]
PAIRS = list(itertools.combinations(range(K), 2))
PCELL = {(-1, -1): 0, (-1, 1): 2, (1, -1): 6, (1, 1): 8}
BASE = [("s", k, s) for k, s in SING] + [("p", a, b, sa, sb) for a, b in PAIRS for (sa, sb) in PCELL]
nB = len(BASE)
MEAN = np.full((nS, nB), np.nan, np.float32); CNT = np.zeros((nS, nB), np.int32)
for i, d in enumerate(SAMP):
    ok = MASK[d] & np.isfinite(Y[d]); x = X[d, ok]; y = Y[d, ok]
    col = 0
    for k, s in SING:
        sel = x[:, k] == s; n = sel.sum(); CNT[i, col] = n
        if n: MEAN[i, col] = y[sel].mean()
        col += 1
    for a, b in PAIRS:
        code = (x[:, a] + 1) * 3 + (x[:, b] + 1)
        n = np.bincount(code, minlength=9); sm = np.bincount(code, weights=y, minlength=9)
        for cell in (0, 2, 6, 8):
            CNT[i, col] = n[cell]
            if n[cell]: MEAN[i, col] = sm[cell] / n[cell]
            col += 1
log("setup outcomes", nB, "base setups x", nS, "sample days")
CTXV = [None] + [(j, s) for j in range(3) for s in (-1, 1)]             # context variants
ctx_s = CTX[SAMP]


# ---------------- 4. track records at a decision day t
def records(t):
    usable = SAMP <= t - 61
    out = []
    w_age = 0.5 ** ((t - SAMP) / 756.0)
    for cv in CTXV:
        dm = usable & (True if cv is None else (ctx_s[:, cv[0]] == cv[1]))
        V = (CNT >= 3) & np.isfinite(MEAN) & dm[:, None]
        W = np.where(V, w_age[:, None], 0.0); Mv = np.where(V, MEAN, 0.0)
        sw = W.sum(0); sw2 = (W ** 2).sum(0)
        with np.errstate(all="ignore"):
            mu = (W * Mv).sum(0) / sw
            var = (W * (Mv - mu) ** 2).sum(0) / sw
            neff = sw ** 2 / sw2 / 12.0
            cc = np.cumsum(V, 0); tot = V.sum(0); h1 = V & (cc <= tot / 2); h2 = V & ~h1
            m1 = (W * Mv * h1).sum(0) / (W * h1).sum(0); m2 = (W * Mv * h2).sum(0) / (W * h2).sum(0)
        se = np.sqrt(var) / np.sqrt(neff)
        out.append(dict(mu=mu, se=se, neff=neff, m1=m1, m2=m2))
    return out


def conviction(t, R, z, stocks):
    """Best cautious edge among zone setups matched minus strongest warning, per stock index."""
    x = X[t, stocks]; best = np.zeros(len(stocks)); worst = np.zeros(len(stocks)); used = []
    for ci, cv in enumerate(CTXV):
        if cv is not None and CTX[t, cv[0]] != cv[1]: continue
        r = R[ci]; ok = np.isfinite(r["mu"]) & (r["neff"] >= 5)
        lo = r["mu"] - z * r["se"]; hi = r["mu"] + z * r["se"]
        zone = ok & (lo > 0) & (r["m1"] > 0) & (r["m2"] > 0)
        warn = ok & (hi < 0) & (r["m1"] < 0) & (r["m2"] < 0)
        for col in np.where(zone | warn)[0]:
            b = BASE[col]
            sel = (x[:, b[1]] == b[2]) if b[0] == "s" else ((x[:, b[1]] == b[3]) & (x[:, b[2]] == b[4]))
            if not sel.any(): continue
            if zone[col]:
                best[sel] = np.maximum(best[sel], lo[col]); used.append((ci, col))
            else:
                worst[sel] = np.minimum(worst[sel], hi[col])
    return best + worst, used


def setup_name(ci, col):
    b = BASE[col]; hl = {1: "high", -1: "low"}
    s = f"{SYM[b[1]]} {hl[b[2]]}" if b[0] == "s" else f"{SYM[b[1]]} {hl[b[3]]} + {SYM[b[2]]} {hl[b[4]]}"
    cv = CTXV[ci]
    return s + ("" if cv is None else f" | {CTXN[cv[0]]} {hl[cv[1]]}")


# ---------------- 5. month-end decisions for every bar (computed once, then traded)
month_end = np.r_[D[1:].month != D[:-1].month, True]
DEC = [t for t in np.where(month_end)[0] if D[t] >= pd.Timestamp("2014-12-31")]
BARS = {"no bar (z=0)": 0.0, "lenient (z=2)": 2.0, "medium (z=3)": 3.0, "strict (z=4)": 4.0}
plans = {b: {} for b in BARS}; held = {b: {} for b in BARS}; stats = {b: dict(swings=0, empty=0, zone_use={}) for b in BARS}
for t in DEC:
    R = records(t)
    stocks = np.where(MASK[t] & np.isfinite(M.close.values[t]))[0]
    for bname, z in BARS.items():
        conv, used = conviction(t, R, z, stocks)
        conv_exit, _ = conviction(t, R, z - 1.0, stocks)
        cmap = dict(zip(stocks, conv)); emap = dict(zip(stocks, conv_exit))
        keep = {i: max(cmap.get(i, 0), emap.get(i, 0)) for i in held[bname] if emap.get(i, 0) > 0}
        new = [i for i in stocks[np.argsort(-conv)] if cmap[i] > 0 and i not in keep][: max(0, 10 - len(keep))]
        stats[bname]["swings"] += len(new)
        sat = dict(keep); sat.update({i: cmap[i] for i in new})
        if not sat: stats[bname]["empty"] += 1
        tot = sum(sat.values())
        w = {i: min(0.05, 0.5 * v / tot) for i, v in sat.items()} if tot > 0 else {}
        held[bname] = w; plans[bname][t] = (stocks, w)
        for u in set(used): stats[bname]["zone_use"][u] = stats[bname]["zone_use"].get(u, 0) + 1
    if t % 12 == 0 or t == DEC[-1]: log(D[t].date(), {b: len(held[b]) for b in BARS})
plans["core only"] = {t: (np.where(MASK[t] & np.isfinite(M.close.values[t]))[0], {}) for t in DEC}

# ---------------- 7. trade, Stage 1 (spread + impact only)
ZERO = FeeSchedule(brokerage_rate=0, stt_rate=0, exch_rate=0, ipft_rate=0, sebi_rate=0, gst_rate=0, stamp_rate=0, dp_charge=0)


class Plan(Strategy):
    def __init__(s, plan): s.plan = plan
    def decide(s, t, st):
        if t not in s.plan: return None
        stocks, w = s.plan[t]; out = np.zeros(N)
        sat = sum(w.values()); out[stocks] = (1 - sat) / len(stocks)
        for i, v in w.items(): out[i] += v
        return out


navs, rows = {}, []
PER = [("2015-19", "2015-01-01", "2019-12-31"), ("2020-21", "2020-01-01", "2021-12-31"), ("2022-26", "2022-01-01", None), ("all", "2015-01-01", None)]
for name, plan in plans.items():
    r = run(M, Plan(plan), Config(capital=1_000_000, start="2015-01-01", max_weight=0.075, min_trade_frac=0.0)) if STAGE2 else \
        run(M, Plan(plan), Config(capital=1_000_000, start="2015-01-01", max_weight=0.075, min_trade_frac=0.0, fees=ZERO, tax=False))
    r.nav = r.nav_post_tax if STAGE2 else r.nav
    navs[name] = r.nav
    for pn, a, b in PER:
        rows.append(dict(run=name, period=pn, turnover=round(r.turnover, 2), **{k: round(float(v), 4) for k, v in metrics(r.nav, a, b).items()}))
    log(name, metrics(r.nav, "2015-01-01", None))
R_ = pd.DataFrame(rows); R_.to_csv(OUT + "metrics.csv", index=False)
NV = pd.DataFrame(navs); NV.to_csv(OUT + "navs.csv")
core = NV["core only"].pct_change()
yc = NV["core only"].resample("YE").last(); yc = yc.pct_change().fillna(yc.iloc[0] / NV["core only"].iloc[0] - 1)
summary = {}
for b in BARS:
    ex = (NV[b].pct_change() - core).dropna()
    y = NV[b].resample("YE").last(); y = y.pct_change().fillna(y.iloc[0] / NV[b].iloc[0] - 1)
    top = sorted(stats[b]["zone_use"].items(), key=lambda kv: -kv[1])[:15]
    summary[b] = dict(excess_pct_per_yr=round(ex.mean() * 252 * 100, 2), excess_t=round(ex.mean() / ex.std() * np.sqrt(len(ex)), 2),
                      years_beating_core=int((y > yc).sum()), years=len(y), swings=stats[b]["swings"],
                      swings_per_year=round(stats[b]["swings"] / (len(DEC) / 12), 1),
                      empty_months_share=round(stats[b]["empty"] / len(DEC), 3),
                      yearly_pct={str(k.year): round(v * 100, 1) for k, v in y.items()},
                      top_zone_setups=[dict(setup=setup_name(ci, col), months=n) for (ci, col), n in top])
summary["core only"] = dict(yearly_pct={str(k.year): round(v * 100, 1) for k, v in yc.items()})
json.dump(summary, open(OUT + "summary.json", "w"), indent=1)
log("done")
