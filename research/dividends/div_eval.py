"""Backtests with and without cash dividends (frozen council, its null twin, price-volume alone),
band rule, Rs 1,00,000, all costs and taxes, 1% minimum trade. Also the equal-weight universe as a
frictionless total-return benchmark (dividends reinvested at the ex-date close)."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from alpha.council_panel import CouncilPanel, RESEARCHERS
from alpha import grammar
from alpha.bhav_panel import BhavMarket
from alpha.signal import pool_score
from strategies import TopKBand
from backtest import run, metrics, Config

grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
P = CouncilPanel()
PERIODS = {"2013-19": ("2013-01-01", "2019-12-31"), "2020-21": ("2020-01-01", "2021-12-31"),
           "2022-26": ("2022-01-01", None), "Full": ("2013-01-01", None)}
rows, navs = [], {}
for divs in (False, True):
    M = BhavMarket(P, dividends=divs)
    for name, tag in (("Council (real)", "c_council_real"), ("Council (NULL)", "c_council_null"),
                      ("Price-volume alone", "c_pricevol_real")):
        s = pool_score(P, tag)
        class Sig: score = np.where(P.mask, s, np.nan)
        r = run(M, TopKBand(Sig, 20, 100), Config(max_weight=0.25, min_trade_frac=0.01))
        navs[f"{name} | div={divs}"] = r.nav_post_tax
        for p, (a, b) in PERIODS.items():
            rows.append(dict(strategy=name, dividends=divs, period=p, **metrics(r.nav_post_tax, a, b),
                             dividends_gross=r.costs.get("dividends", np.nan), div_tax=r.costs.get("div_tax", np.nan),
                             final=float(r.nav_post_tax.iloc[-1])))
        print(name, divs, "final %.0f" % r.nav_post_tax.iloc[-1], "dividends %.0f" % r.costs.get("dividends", 0), flush=True)
    # equal-weight universe, frictionless
    ret = np.expm1(P.targets[1])                    # open-to-open, row t = return from t+1 to t+2 open
    ew = pd.Series(np.nanmean(np.where(P.mask, ret, np.nan), 1), index=P.dates).shift(1).fillna(0)
    if divs:
        C = P.raw_close.ffill().shift(1)
        dy = (M.div / C).where(P.mask).mean(1).fillna(0)          # average dividend yield that day
        ew = ew + dy.values
    nav = (1 + ew.loc["2013-01-01":]).cumprod() * 1e5
    for p, (a, b) in PERIODS.items():
        rows.append(dict(strategy="EW universe (frictionless)", dividends=divs, period=p, **metrics(nav, a, b), final=float(nav.iloc[-1])))
df = pd.DataFrame(rows); df.to_csv("results/div_eval.csv", index=False)
pd.DataFrame(navs).to_csv("results/div_eval_navs.csv")
pd.set_option("display.width", 250)
print(df.pivot_table(index=["strategy", "dividends"], columns="period", values=["CAGR", "Sharpe"]).round(3).to_string())
