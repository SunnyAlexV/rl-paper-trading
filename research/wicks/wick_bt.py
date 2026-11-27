"""Wick backtest + momentum+delivery holdout (rules in SPEC_BT.md). Run from the history working copy."""
import sys, time; sys.path.insert(0, ".")
import numpy as np, pandas as pd
src = open("research/pods/int_bt.py").read().split("def bt(")[0].replace('CAP, START, OUT = 1_000_000, "2016-02-01"', 'CAP, START, OUT = 1_000_000, "2012-07-02"')
exec(src)                                   # P, M, c, dp, zrank, Band, EW, run, metrics, Config, month_end
from costs import FeeSchedule
ZERO = FeeSchedule(brokerage_rate=0, stt_rate=0, exch_rate=0, ipft_rate=0, sebi_rate=0, gst_rate=0, stamp_rate=0, dp_charge=0)
F = lambda k: pd.DataFrame(P.feat[k], index=D)
o, h, l, cl = F("open"), F("high"), F("low"), F("close")
lw = ((np.minimum(o, cl) - l) / (h - l).where(h > l)).rolling(20, min_periods=12).mean()
z = {"mom": zrank((c.shift(21) / c.shift(252) - 1).values, P.mask),
     "deliv": zrank(dp.rolling(60, min_periods=36).mean().values, P.mask),
     "wick": zrank(lw.values, P.mask)}
sc = lambda keys: np.where(P.mask, sum(z[k] for k in keys) / len(keys), np.nan)
BOOKS = {"wick": ("wick",), "mom + deliv": ("mom", "deliv"), "mom + deliv + wick": ("mom", "deliv", "wick")}
PER = [("2012-15 holdout", "2012-07-02", "2015-12-31"), ("2016-19", "2016-01-01", "2019-12-31"), ("2020-21", "2020-01-01", "2021-12-31"),
       ("2022-26", "2022-01-01", None), ("all", "2012-07-02", None)]
rows = []; t0 = time.time()
def go(name, strat, k=None):
    for stage in (1, 2):
        cfg = Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01,
                     **({"fees": ZERO, "tax": False} if stage == 1 else {}))
        r = run(M, strat(), cfg); nav = r.nav if stage == 1 else r.nav_post_tax
        for pn, a, b in PER:
            rows.append(dict(book=name, k=k, stage=stage, period=pn, turnover=round(r.turnover, 2), **{kk: round(float(v), 4) for kk, v in metrics(nav, a, b).items()}))
    print(name, k, "done", round(time.time() - t0), "s", flush=True)
go("equal-weight universe", lambda: EW())
go("momentum 12-1", lambda: Band(np.where(P.mask, (c.shift(21) / c.shift(252) - 1).values, np.nan), 20, 100), 20)
for name, keys in BOOKS.items():
    s = sc(keys)
    for k in (15, 20, 25): go(name, lambda s=s, k=k: Band(s, k, 5 * k), k)
R = pd.DataFrame(rows); R.to_csv("research/wicks/wick_bt_metrics.csv", index=False)
print(R[(R.k.isin([20]) | R.k.isna())].pivot_table(index=["book", "stage"], columns="period", values=["CAGR", "Sharpe"]).round(3).to_string())
