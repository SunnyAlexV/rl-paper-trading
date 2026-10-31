"""Multi-seed sceptic, council level.

For each research seed k = 0..4 the council is rebuilt exactly as the frozen one was:
union of the price-volume (seed k) and delivery (seed k) pools with the derivatives and LLM pools
(single runs; the derivatives researcher was at null level and the LLM pool is fixed text), blended
with least-squares weights fitted on 2013-19 only. The same is done on the null (shuffled-target)
market, where each seed has its own shuffle. Every council is then traded with the frozen band rule
(top-20, band 100, 1% minimum trade) in the exact engine, Rs 1,00,000, post-tax.

Seed 0 is the frozen paper-trading system; seeds 1-4 measure how much of its result is the luck
of one search.

  python -m alpha.council_seeds build     # pools -> results/alpha_c_council_{real,null}_s{k}.json
  python -m alpha.council_seeds backtest  # -> results/council_seeds_eval.csv, daily returns
"""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
from alpha.grammar import evaluate, to_str
from alpha.scoring import Scorer
from alpha.netproxy import NetProxy

ALL_FEATS = sorted({f for fs in RESEARCHERS.values() for f in fs})
grammar.configure(ALL_FEATS)
SEEDS = range(5)
NULL_SHUFFLE = {0: 7, 1: 11, 2: 12, 3: 13, 4: 14}   # shuffle used by each seed's luck twin
mode = sys.argv[1]
P = CouncilPanel()


def pool_file(r, tag, k):
    return f"results/alpha_c_{r}_{tag}.json" if k == 0 else f"results/alpha_c_{r}_{tag}_s{k}.json"


if mode == "build":
    tr, va = P.idx("train"), P.idx("valid")
    lo, hi = tr[0] - 120, va[-1] + 1
    feat = {f: P.feat[f][lo:hi] for f in ALL_FEATS}
    tgt, mask, spr = P.targets[20][lo:hi], P.mask[lo:hi], P.spread[lo:hi]
    S_va, N_va = Scorer(tgt, mask, va - lo), NetProxy(tgt, mask, spr, va - lo, 20)
    for k in SEEDS:
        for tag in ("real", "null"):
            null = None if tag == "real" else NULL_SHUFFLE[k]
            seqs, src = [], []
            for r in ("pricevol", "delivery"):
                for a in json.load(open(pool_file(r, tag, k)))["alphas"]:
                    seqs.append(a["seq"]); src.append(r)
            for r in ("derivs", "llm"):
                for a in json.load(open(f"results/alpha_c_{r}_{tag}.json"))["alphas"]:
                    seqs.append(a["seq"]); src.append(r)
            S = Scorer(tgt, mask, tr - lo, permute_seed=null)
            N = NetProxy(tgt, mask, spr, tr - lo, 20, permute_seed=null)
            zs = [S.alpha_z(evaluate(q, feat)) for q in seqs]
            w, tr_ic = S.combine(zs)
            zv = [S_va.alpha_z(evaluate(q, feat)) for q in seqs]
            out = dict(seed=k, market=tag, n_members=len(seqs), train_net_ir=N.ir(S.blend(zs, w)),
                       valid_net_ir=N_va.ir(S_va.blend(zv, w)),
                       alphas=[dict(seq=q, formula=to_str(q), weight=float(wi), researcher=s_)
                               for q, wi, s_ in zip(seqs, w, src)])
            json.dump(out, open(f"results/alpha_c_council_{tag}_s{k}.json", "w"), indent=1, default=float)
            print(k, tag, len(seqs), "train IR %.3f valid IR %.3f" % (out["train_net_ir"], out["valid_net_ir"]), flush=True)

elif mode == "backtest":
    from alpha.bhav_panel import BhavMarket
    from alpha.signal import pool_score
    from strategies import TopKBand
    from backtest import run, metrics, Config
    M = BhavMarket(P)
    PERIODS = {"2013-19": ("2013-01-01", "2019-12-31"), "2020-21": ("2020-01-01", "2021-12-31"),
               "2022-26": ("2022-01-01", None), "Full": ("2013-01-01", None)}
    rows, rets = [], {}
    for k in SEEDS:
        for tag in ("real", "null"):
            s = pool_score(P, f"c_council_{tag}_s{k}")
            class Sig: score = np.where(P.mask, s, np.nan)
            r = run(M, TopKBand(Sig, 20, 100), Config(max_weight=0.25, min_trade_frac=0.01))
            nav = r.nav_post_tax
            rets[f"{tag}_s{k}"] = nav.pct_change()
            for p, (a, b) in PERIODS.items():
                rows.append(dict(seed=k, market=tag, period=p, **metrics(nav, a, b),
                                 turnover=r.turnover, trades=r.trades, final=float(nav.iloc[-1])))
            print(k, tag, "final %.0f" % nav.iloc[-1], flush=True)
            pd.DataFrame(rows).to_csv("results/council_seeds_eval.csv", index=False)
    pd.DataFrame(rets).to_csv("results/council_seeds_daily_returns.csv")
