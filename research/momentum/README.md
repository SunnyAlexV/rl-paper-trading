# Council band rule vs plain 12-1 momentum (18 Nov 2026), research only

**Question.** Does the frozen council signal beat a one-line momentum rule run through the same
band rule, universe, costs and tax?

**Data.** NSE bhavcopy, security-wise delivery and F&O bhavcopy for Jan 2015 - 17 Nov 2026 were
downloaded again from NSE archives (`download_nse_2015.py`, `download_bhav_zips.py`) into a separate
working copy laid out like `data/`, and the repo's own `CouncilPanel`, `pool_score` and `backtest.run`
were run on it (`compare_mom.py`). The trading repo's `data/` window was not touched. Check of the
rebuild: the frozen council returns 11.5% a year in 2022-26, in line with the pre-registration's
"about 11% a year in 2022-26".

**Setup.** Rs 1,00,000, band rule 20 names / band 100, minimum trade 1% of NAV, max weight 25%, Zerodha
costs, FIFO capital-gains tax, price returns (no dividends). Feb 2016 - 17 Nov 2026. Momentum 12-1 =
close(t-21) / close(t-252) - 1 on back-adjusted closes, over the same universe mask.

**Results** (post-tax; `compare.csv`, monthly NAVs in `navs_monthly.csv`).

| | CAGR all | 2016-19 | 2020-21 | 2022-26 | Sharpe all | Sharpe 2022-26 | Max DD all | Max DD 2022-26 |
|---|---|---|---|---|---|---|---|---|
| Council (frozen) | 17.6% | 10.0% | 50.5% | 11.5% | 1.03 | 0.75 | -39% | -21% |
| Momentum 12-1 | 24.5% | 16.4% | 59.7% | 18.1% | 0.95 | 0.73 | -45% | -45% |
| Null control | 10.5% | 5.7% | 22.7% | 9.3% | 0.56 | 0.53 | -59% | -28% |
| Equal-weight universe | 7.9% | 4.2% | 15.1% | 7.8% | 0.66 | 0.73 | -39% | -14% |
| Nifty 50 (price) | 11.9% | 13.0% | 19.4% | 7.8% | | | | |

2016-19 is in-sample for the council (weights fitted on 2013-19).

**Reading.** Momentum earned about 8 points a year more, with larger drawdowns and very uneven years
(+120% in 2017 and 2023, -22% in 2018, -16% in 2025). Risk-adjusted the two are close, and the daily
return difference is not significant (t = 1.3 over 2016-26, 0.9 over 2022-26; daily correlation 0.7).
Momentum 12-1 was chosen after it was the best of five slow signals on the same data, which flatters it.

**Conclusion.** No change to the primary. Momentum 12-1 is added as an exploratory forward paper
account (`paper_mom_10L/`, amendment of 18 Nov 2026 in `PREREGISTRATION.md`) to see whether the simple
rule keeps pace with the council out of sample.
