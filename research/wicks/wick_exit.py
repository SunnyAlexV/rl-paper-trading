"""Upper wick as a sell signal (rules in SPEC_EXIT.md). Run from the history working copy."""
import sys, time; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/pods/int_bt.py").read().split("def bt(")[0].replace('CAP, START, OUT = 1_000_000, "2016-02-01"', 'CAP, START, OUT = 1_000_000, "2012-07-02"'))
from costs import FeeSchedule
ZERO = FeeSchedule(brokerage_rate=0, stt_rate=0, exch_rate=0, ipft_rate=0, sebi_rate=0, gst_rate=0, stamp_rate=0, dp_charge=0)
F = lambda k: pd.DataFrame(P.feat[k], index=D)
o, h, l, cl = F("open"), F("high"), F("low"), F("close")
rg = (h - l).where(h > l)
LWr = ((np.minimum(o, cl) - l) / rg).rolling(20, min_periods=12).mean()
UWr = ((h - np.maximum(o, cl)) / rg).rolling(20, min_periods=12).mean()
UWpct = UWr.where(P.mask).rank(axis=1, pct=True).values            # 1 = strongest upper wick
LW = np.where(P.mask, LWr.values, np.nan)
MD = np.where(P.mask, (zrank((c.shift(21) / c.shift(252) - 1).values, P.mask) + zrank(dp.rolling(60, min_periods=36).mean().values, P.mask)) / 2, np.nan)


class ExitRule(Strategy):
    """Hold k. Sell a holding when (band is set and it leaves the top `band`) or (exit_x set and its upper wick is in
    the top exit_x share). New names: best by score, skipping strong-upper-wick stocks; freed weight shared equally."""
    def __init__(s, sc, k=20, band=None, exit_x=None): s.sc, s.k, s.band, s.x = sc, k, band, exit_x
    def reset(s, m): super().reset(m); s.hold = set()
    def decide(s, t, st):
        sc = s.sc[t]
        if not np.isfinite(sc).any(): return None
        w = np.array(st["weights"], float)
        order = list(np.argsort(-np.where(np.isfinite(sc), sc, -np.inf))); rank = {i: j for j, i in enumerate(order)}
        strong_up = (UWpct[t] >= 1 - s.x) if s.x else np.zeros(len(sc), bool)
        keep = {i for i in s.hold if np.isfinite(sc[i]) and not strong_up[i] and (s.band is None or rank[i] < s.band)}
        if len(keep) == len(s.hold) == s.k: return None
        slot = st["nav"] / s.k; px = np.nan_to_num(M.close.values[t])
        new = [i for i in order if i not in keep and np.isfinite(sc[i]) and not strong_up[i] and 0 < px[i] <= slot][: s.k - len(keep)]
        out = np.zeros(len(sc))
        for i in keep: out[i] = w[i]
        rest = 1 - out.sum()
        for i in new: out[i] = max(rest, 0) / len(new)
        s.hold = keep | set(new); return out


books = {"equal-weight universe": lambda: EW(),
         "lower-wick band rule (no exit signal)": lambda: ExitRule(LW, band=100),
         "mom + deliv (no exit signal)": lambda: ExitRule(MD, band=100)}
for x in (0.10, 0.20, 0.30):
    books[f"pure wick, sell on upper wick top {int(x*100)}%"] = lambda x=x: ExitRule(LW, exit_x=x)
    books[f"mom + deliv + upper-wick exit top {int(x*100)}%"] = lambda x=x: ExitRule(MD, band=100, exit_x=x)
rows = []; t0 = time.time()
for name, mk in books.items():
    for stage in (1, 2):
        r = run(M, mk(), Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01, **({"fees": ZERO, "tax": False} if stage == 1 else {})))
        nav = r.nav if stage == 1 else r.nav_post_tax
        for pn, a, b in [("all", START, None), ("2012-15", START, "2015-12-31"), ("2022-26", "2022-01-01", None)]:
            rows.append(dict(book=name, stage=stage, period=pn, turnover=round(r.turnover, 2), **{k: round(float(v), 4) for k, v in metrics(nav, a, b).items()}))
    print(name, "done", round(time.time() - t0), "s", flush=True)
R = pd.DataFrame(rows); R.to_csv("research/wicks/wick_exit_metrics.csv", index=False)
A = R[R.period == "all"].pivot_table(index="book", columns="stage", values=["CAGR", "Sharpe", "MaxDD", "turnover"])
print(A.round(3).to_string())
