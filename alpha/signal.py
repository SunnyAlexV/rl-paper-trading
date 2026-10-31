"""Build a pool's blended signal panel over the full history (weights frozen from discovery)."""
import json, numpy as np
from .grammar import evaluate
from .scoring import zrank


def pool_score(P, tag):
    pool = json.load(open(f"results/alpha_{tag}.json"))
    s = sum(a["weight"] * zrank(evaluate(a["seq"], P.feat), P.mask) for a in pool["alphas"])
    s = np.where(P.mask, s, np.nan)
    mu = np.nanmean(s, 1, keepdims=True); sd = np.nanstd(s, 1, keepdims=True)
    return (s - mu) / np.where(sd > 0, sd, 1)
