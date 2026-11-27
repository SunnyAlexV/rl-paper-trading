"""Stress tests of momentum + delivery (criteria in SPEC.md). Run from the history working copy."""
import sys, time, json; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/pods/int_bt.py").read().split("def bt(")[0].replace('CAP, START, OUT = 1_000_000, "2016-02-01"', 'CAP, START, OUT = 1_000_000, "2012-07-02"'))
t0 = time.time(); OUT = "research/stress/"; res = {}
mom = (c.shift(21) / c.shift(252) - 1).values; dlv = dp.rolling(60, min_periods=36).mean().values


class BandM(Strategy):                       # band rule on an explicit mask
    def __init__(s, sc, k, band): s.sc, s.k, s.band = sc, k, band
    def reset(s, m): super().reset(m); s.hold = set()
    def decide(s, t, st):
        sc = s.sc[t]
        if not np.isfinite(sc).any(): return None
        w = np.array(st["weights"], float)
        order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf))); rank = {i: j for j, i in enumerate(order)}
        keep = {i for i in s.hold if rank[i] < s.band and np.isfinite(sc[i])}
        if len(keep) == len(s.hold) == s.k: return None
        slot = st["nav"] / s.k; px = np.nan_to_num(M.close.values[t])
        new = [i for i in order if i not in keep and np.isfinite(sc[i]) and 0 < px[i] <= slot][: s.k - len(keep)]
        out = np.zeros(len(sc))
        for i in keep: out[i] = w[i]
        rest = 1 - out.sum()
        for i in new: out[i] = max(rest, 0) / len(new)
        s.hold = keep | set(new); return out


class EWM(Strategy):
    def __init__(s, mask): s.mask = mask
    def decide(s, t, st):
        if not month_end[t] and getattr(s, "started", False): return None
        m = s.mask[t] & (np.nan_to_num(M.close.values[t]) > 0)
        if not m.any(): return None
        s.started = True; out = np.zeros(len(m)); out[m] = 1 / m.sum(); return out


def score(mask): return np.where(mask, (zrank(mom, mask) + zrank(dlv, mask)) / 2, np.nan)
def cfg(cap=CAP, mult=1.0): return Config(capital=cap, start=START, max_weight=0.075, min_trade_frac=0.01, implicit_mult=mult)
sh = lambda nav: float(metrics(nav, START, None)["Sharpe"])

# 3 + 5 + full-period navs
full = {}
for mult in (1.0, 2.0, 3.0):
    full[f"mdeliv x{mult:g}"] = run(M, BandM(score(P.mask), 20, 100), cfg(mult=mult)).nav_post_tax
    full[f"ew x{mult:g}"] = run(M, EWM(P.mask), cfg(mult=mult)).nav_post_tax
for cap in (100_000, 5_000_000):
    full[f"mdeliv cap {cap}"] = run(M, BandM(score(P.mask), 20, 100), cfg(cap=cap)).nav_post_tax
res["costs"] = {k: dict(CAGR=round(float(metrics(v, START, None)["CAGR"]), 4), Sharpe=round(sh(v), 3), MaxDD=round(float(metrics(v, START, None)["MaxDD"]), 3)) for k, v in full.items()}
print("costs/capital", json.dumps(res["costs"], indent=0), round(time.time() - t0), "s", flush=True)

# 2. rolling windows (month-end starts)
md, ew = full["mdeliv x1"], full["ew x1"]; mdm, ewm = md.resample("ME").last(), ew.resample("ME").last()
res["windows"] = {}
for n in (12, 24, 36):
    rm = (mdm.shift(-n) / mdm - 1).dropna(); re = (ewm.shift(-n) / ewm - 1).dropna(); d = (rm - re)
    res["windows"][f"{n}m"] = dict(windows=len(d), share_beating=round(float((d > 0).mean()), 3),
        worst_relative_pct=round(float(d.min() * 100), 1), worst_start=str(d.idxmin().date()), median_relative_pct=round(float(d.median() * 100), 1),
        share_absolute_loss=round(float((rm < 0).mean()), 3))
print("windows", res["windows"], flush=True)

# 4. drawdowns
dd = md / md.cummax() - 1; eps = []; i = 0; v = dd.values; idx = dd.index
while i < len(v):
    if v[i] < 0:
        j = i
        while j < len(v) and v[j] < 0: j += 1
        k = i + int(np.argmin(v[i:j])); eps.append(dict(start=str(idx[i - 1].date()), trough=str(idx[k].date()), depth_pct=round(float(v[k] * 100), 1),
                                                         recovered=str(idx[j].date()) if j < len(v) else "not yet", months=round((idx[min(j, len(v) - 1)] - idx[i - 1]).days / 30.4, 1)))
        i = j
    else: i += 1
res["drawdowns"] = sorted(eps, key=lambda e: e["depth_pct"])[:5]
rel = (md / ew); rdd = rel / rel.cummax() - 1; under = (rdd < 0).astype(int); run_len = under.groupby((under == 0).cumsum()).cumsum()
res["longest_relative_underwater_months"] = round(float(run_len.max() / 21), 1); res["deepest_relative_drawdown_pct"] = round(float(rdd.min() * 100), 1)
print("drawdowns", res["drawdowns"], res["longest_relative_underwater_months"], res["deepest_relative_drawdown_pct"], flush=True)

# 1. random halves
rng = np.random.default_rng(7); halves = []
for s in range(25):
    inA = rng.random(len(P.names)) < 0.5
    for hname, sel in (("A", inA), ("B", ~inA)):
        mk = P.mask & sel[None, :]
        a = run(M, BandM(score(mk), 10, 50), cfg()).nav_post_tax; b = run(M, EWM(mk), cfg()).nav_post_tax
        halves.append(dict(split=s, half=hname, rule_sharpe=round(sh(a), 3), ew_sharpe=round(sh(b), 3),
                           rule_cagr=round(float(metrics(a, START, None)["CAGR"]), 4), ew_cagr=round(float(metrics(b, START, None)["CAGR"]), 4)))
    print("split", s, halves[-2:], round(time.time() - t0), "s", flush=True)
H = pd.DataFrame(halves); H.to_csv(OUT + "halves.csv", index=False)
res["halves"] = dict(n=len(H), share_rule_beats=round(float((H.rule_sharpe > H.ew_sharpe).mean()), 3),
                     median_rule_sharpe=float(H.rule_sharpe.median()), median_ew_sharpe=float(H.ew_sharpe.median()),
                     worst_gap=float((H.rule_sharpe - H.ew_sharpe).min()), median_rule_cagr=float(H.rule_cagr.median()), median_ew_cagr=float(H.ew_cagr.median()))
json.dump(res, open(OUT + "results.json", "w"), indent=1); pd.DataFrame(full).to_csv(OUT + "navs.csv")
print("halves", res["halves"]); print("done", round(time.time() - t0), "s")
