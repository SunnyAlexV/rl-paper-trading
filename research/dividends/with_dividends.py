"""Re-run the main books with cash dividends credited (taxed at 31.2%), Stage 2 post-tax, Jul 2012 - Nov 2026.
Run from the history working copy (needs data/corpact/ for 2011-2026)."""
import sys; sys.path.insert(0, ".")
import numpy as np, pandas as pd
exec(open("research/stress/stress.py").read().split("def score(mask)")[0])          # P, M, c, dp, zrank, BandM, EWM, run, metrics, Config
from alpha.dividends import dividend_panel
from alpha.signal import pool_score
divp, div_events = dividend_panel(P)
print("announcements matched:", len(div_events), "| credited:", int(div_events["credited"].sum()), "| already in price factor:", int(div_events["in_price_factor"].sum()), "| implausible dropped:", int(div_events["implausible"].sum()))
mom = (c.shift(21) / c.shift(252) - 1).values; dlv = dp.rolling(60, min_periods=36).mean().values
books = {"momentum + delivery (primary)": lambda: BandM(np.where(P.mask, (zrank(mom, P.mask) + zrank(dlv, P.mask)) / 2, np.nan), 20, 100),
         "momentum only": lambda: BandM(np.where(P.mask, mom, np.nan), 20, 100),
         "council (frozen)": lambda: BandM(np.where(P.mask, pool_score(P, "c_council_real"), np.nan), 20, 100),
         "equal-weight universe": lambda: EWM(P.mask)}
cfg = Config(capital=CAP, start=START, max_weight=0.075, min_trade_frac=0.01)
nonzero = (divp.reindex(index=M.div.index, columns=M.div.columns).fillna(0.0) > 0).sum().sum()
print("dividend events in panel:", int(nonzero))
rows = []
for name, mk in books.items():
    out = {}
    for label, d in (("price only", pd.DataFrame(0.0, index=M.div.index, columns=M.div.columns)),
                     ("with dividends", divp.reindex(index=M.div.index, columns=M.div.columns).fillna(0.0))):
        M.div = d
        r_ = run(M, mk(), cfg); a = metrics(r_.nav_post_tax, START, None); b = metrics(r_.nav_post_tax, "2022-01-01", None)
        out[label] = r_; rows.append(dict(book=name, version=label, CAGR=round(float(a["CAGR"]), 4), Sharpe=round(float(a["Sharpe"]), 3),
                                          MaxDD=round(float(a["MaxDD"]), 3), CAGR_2022_26=round(float(b["CAGR"]), 4),
                                          dividends_gross_rs=round(r_.costs.get("dividends", 0.0)) if isinstance(r_.costs, dict) else None))
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv("research/dividends/with_dividends.csv", index=False)
