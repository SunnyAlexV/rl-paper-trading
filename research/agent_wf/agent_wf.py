"""Walk-forward discovery agent (rules in SPEC.md, fixed before the run). Research only.

Run from the history working copy:  python3 -W ignore research/agent_wf/agent_wf.py --seed 1
Stage 1 evaluates the random pool (cached); stage 2 walks forward quarter by quarter (searching,
testing, selecting, learning weekly) and builds the score panel; stage 3 trades it with the repo's
engine. Writes research/agent_wf/seed<k>_*.{csv,json}.
"""
import sys, os, json, time, argparse, pickle
sys.path.insert(0, ".")
import numpy as np, pandas as pd
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
from alpha.grammar import evaluate, legal, is_complete, arity, to_str, TOKENS, FEATURES
from alpha.scoring import zrank
from alpha.bhav_panel import BhavMarket
from strategies import Strategy
from backtest import run, metrics, Config

ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=1); a = ap.parse_args()
SEED = a.seed; rng = np.random.default_rng(SEED)
OUT = "research/agent_wf/"; t0 = time.time()
P = CouncilPanel(); D = P.dates; nD = len(D); MASK = P.mask
TGT = P.targets[20]                                   # log open(t+21) - log open(t+1)
SAMP = np.arange(0, nD, 5)                            # IC sampled every 5th trading day
VALID = MASK[SAMP] & np.isfinite(TGT[SAMP])
ZT = zrank(TGT[SAMP], VALID)
LAG = 22                                              # a sample row r is usable at step t if r <= t - LAG
POOL_N, MUT_N, MAXLEN, TOP_KEEP, T_MIN, TEST_DAYS, CORR_MAX, ETA = 1500, 60, 8, 10, 3.0, 126, 0.7, 2.0
if os.environ.get("SMOKE"): POOL_N, MUT_N, OUT = 60, 4, "/tmp/agent_smoke_"
FEAT_TOK = [t for t in TOKENS if arity(t) == 0]


def log(*x): print(f"[seed {SEED} {time.time() - t0:6.0f}s]", *x, flush=True)


def random_formula(maxlen=MAXLEN, minlen=2):
    for _ in range(100):
        seq = []
        target = rng.integers(minlen, maxlen + 1)
        while True:
            opts = legal(seq, maxlen)
            if is_complete(seq) and (len(seq) >= target or not opts): break
            if not opts: break
            seq.append(opts[rng.integers(len(opts))])
        if is_complete(seq) and len(seq) >= minlen and any(arity(t) > 0 for t in seq): return seq
    return ["close", "ts_pct_20"]


def ic_series(seq):
    """Per sampled day rank IC (NaN where undefined). Formula values are backward-looking."""
    x = evaluate(seq, P.feat)[SAMP]
    if not np.isfinite(x).any(): return None
    z = zrank(x, VALID)
    za = np.where(VALID, z, np.nan); zb = np.where(VALID, ZT, np.nan)
    za = za - np.nanmean(za, 1, keepdims=True); zb = zb - np.nanmean(zb, 1, keepdims=True)
    with np.errstate(all="ignore"):
        ic = np.nansum(za * zb, 1) / np.sqrt(np.nansum(za * za, 1) * np.nansum(zb * zb, 1))
    ic[~np.isfinite(ic)] = np.nan
    if np.nanstd(ic) < 1e-6: return None
    return ic.astype(np.float32)


def mutate(seq):
    s = list(seq)
    for _ in range(50):
        s = list(seq); i = rng.integers(len(s)); tok = s[i]
        if arity(tok) == 0 and rng.random() < 0.5:                 # replace a leaf by a small subtree
            sub = random_formula(maxlen=3, minlen=1) if rng.random() < 0.7 else [FEAT_TOK[rng.integers(len(FEAT_TOK))]]
            s = s[:i] + sub + s[i + 1:]
        else:                                                       # change one token, same arity
            same = [t for t in TOKENS if arity(t) == arity(tok) and t != tok]
            s[i] = same[rng.integers(len(same))]
        if is_complete(s) and len(s) <= MAXLEN + 2 and s != seq: return s
    return None


# ---------------- stage 1: the random pool (generated without data, then scored per day)
pool_file = f"{OUT}pool_seed{SEED}.pkl"
if os.path.exists(pool_file):
    POOL = pickle.load(open(pool_file, "rb")); log("pool loaded", len(POOL))
else:
    POOL, seen = [], set()
    while len(POOL) < POOL_N:
        s = random_formula(); k = " ".join(s)
        if k in seen: continue
        seen.add(k); ic = ic_series(s)
        if ic is not None: POOL.append(dict(seq=s, ic=ic, born=0))
        if len(seen) % 250 == 0: log("pool", len(POOL), "of", len(seen))
    pickle.dump(POOL, open(pool_file, "wb")); log("pool done", len(POOL))

# ---------------- stage 2: walk forward
qstarts = [i for i in range(1, nD) if D[i] >= pd.Timestamp("2014-01-01") and D[i].month in (1, 4, 7, 10) and D[i].month != D[i - 1].month]
wstarts = set(i for i in range(1, nD) if D[i].isocalendar().week != D[i - 1].isocalendar().week)
samp_pos = {r: k for k, r in enumerate(SAMP)}


def tstat(v):
    v = v[np.isfinite(v)]
    if len(v) < 20: return 0.0, 0.0
    return float(v.mean()), float(v.mean() / (v.std() + 1e-12) * np.sqrt(len(v) / 4))


def latest_ic(f, t):
    k = np.searchsorted(SAMP, t - LAG, side="right") - 1
    while k >= 0 and not np.isfinite(f["ic"][k]): k -= 1
    return float(f["ic"][k]) if k >= 0 else 0.0


score = {m: np.full((nD, len(P.names)), np.nan, np.float32) for m in ("agent", "nolearn", "noskill")}
active, weights, log_q, FBY = [], {}, [], {}
for qi, t in enumerate(qstarts):
    # 1. search: mutations of the current top 20 (by discovery t on usable history)
    usable = np.searchsorted(SAMP, t - LAG, side="right")            # sample rows usable now
    test_from = np.searchsorted(SAMP, t - LAG - TEST_DAYS, side="right")
    stats = []
    for f in POOL:
        m, ts = tstat(f["ic"][:test_from])
        stats.append((abs(ts), m, f))
    stats.sort(key=lambda x: -x[0])
    born = 0
    for _, _, f in stats[:20]:
        for _ in range(3):
            if born >= MUT_N: break
            s = mutate(f["seq"])
            if s is None or any(s == g["seq"] for g in POOL[-500:]): continue
            ic = ic_series(s)
            if ic is not None: POOL.append(dict(seq=s, ic=ic, born=t)); born += 1
    # 2-3. discover and test
    cand = []
    for f in POOL:
        m, ts = tstat(f["ic"][:test_from])
        if abs(ts) < T_MIN: continue
        sgn = np.sign(m); tv = f["ic"][test_from:usable]; tv = tv[np.isfinite(tv)]
        if len(tv) >= 10 and sgn * tv.mean() > 0: cand.append((abs(ts), sgn, f))
    cand.sort(key=lambda x: -x[0])
    # 4. select, diverse
    sel = []
    for ts, sgn, f in cand:
        ok = True
        for _, _, g in sel:
            a_, b_ = f["ic"][:usable], g["ic"][:usable]; mm = np.isfinite(a_) & np.isfinite(b_)
            if mm.sum() > 20 and abs(np.corrcoef(a_[mm], b_[mm])[0, 1]) > CORR_MAX: ok = False; break
        if ok: sel.append((ts, sgn, f))
        if len(sel) >= TOP_KEEP: break
    if sel:
        keys = [(id(f), int(sgn)) for _, sgn, f in sel]
        for _, _, f in sel: FBY[id(f)] = f
        keep_w = [weights[k] for k in keys if k in weights]
        avg = float(np.mean(keep_w)) if keep_w else 1.0
        new_w = {k: weights.get(k, avg) for k in keys}
        tot = sum(new_w.values()); weights = {k: v / tot for k, v in new_w.items()}
        active = [(f, sgn) for _, sgn, f in sel]
    log_q.append(dict(date=str(D[t].date()), pool=len(POOL), survivors=len(cand), selected=[
        dict(formula=to_str(f["seq"]), sign=int(sgn), discovery_t=round(ts, 2), born=str(D[f["born"]].date()) if f["born"] else "pool")
        for ts, sgn, f in sel]))
    # 5. score the quarter, learning weekly
    t_end = qstarts[qi + 1] if qi + 1 < len(qstarts) else nD
    rows = np.arange(t, t_end)
    rnd = [POOL[i] for i in rng.choice(len(POOL), size=min(10, len(POOL)), replace=False)]
    rnd_sgn = rng.choice([-1, 1], size=len(rnd))
    if active:
        Z = {id(f): zrank(evaluate(f["seq"], P.feat)[rows], MASK[rows]) for f, _ in active}
        for k, tt in enumerate(rows):
            if tt in wstarts and tt != t:
                for key in weights: weights[key] *= np.exp(ETA * key[1] * latest_ic(FBY[key[0]], tt))
                tot = sum(weights.values()); weights = {kk: v / tot for kk, v in weights.items()}
            score["agent"][tt] = sum(weights[(id(f), int(sgn))] * sgn * Z[id(f)][k] for f, sgn in active)
            score["nolearn"][tt] = sum(sgn * Z[id(f)][k] for f, sgn in active) / len(active)
    Zr = [zrank(evaluate(f["seq"], P.feat)[rows], MASK[rows]) for f in rnd]
    score["noskill"][rows] = sum(s_ * z for s_, z in zip(rnd_sgn, Zr)) / len(Zr)
    log(D[t].date(), "pool", len(POOL), "survivors", len(cand), "selected", len(sel),
        "| top:", to_str(sel[0][2]["seq"])[:70] if sel else "-")
json.dump(log_q, open(f"{OUT}seed{SEED}_quarters.json", "w"), indent=1)

# ---------------- stage 3: trade
M = BhavMarket(P)


class Band(Strategy):
    def __init__(s, sc, k=20, band=100): s.sc, s.k, s.band = sc, k, band
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


navs, rows_out = {}, []
for name, sc in score.items():
    sc = np.where(MASK, sc, np.nan)
    r = run(M, Band(sc), Config(capital=1_000_000, start="2014-01-01", max_weight=0.075, min_trade_frac=0.01))
    navs[name] = r.nav_post_tax
    for pn, a_, b_ in [("2014-17", "2014-01-01", "2017-12-31"), ("2018-21", "2018-01-01", "2021-12-31"), ("2022-26", "2022-01-01", None), ("all", "2014-01-01", None)]:
        rows_out.append(dict(seed=SEED, run=name, period=pn, **{k: round(v, 4) for k, v in metrics(r.nav_post_tax, a_, b_).items()}))
    log(name, "traded", metrics(r.nav_post_tax, "2014-01-01", None))
pd.DataFrame(rows_out).to_csv(f"{OUT}seed{SEED}_metrics.csv", index=False)
pd.DataFrame(navs).to_csv(f"{OUT}seed{SEED}_navs.csv")
log("done")
