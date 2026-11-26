# Pods round 1 results (26 Nov 2026)

Rules and criteria: `SPEC.md` (committed before this run). Script: `pods_bt.py`, run on the rebuilt
2011-2026 history. Rs 10L per book, Feb 2016 - 26 Nov 2026, post-tax, max 7.5% per stock.
Files: `round1_metrics.csv`, `round1_years.csv`, `round1_navs_monthly.csv`.

| Book | CAGR all | CAGR 2022-26 | Sharpe all | Sharpe 2022-26 | Max DD | Years beating EW | Verdict |
|---|---|---|---|---|---|---|---|
| **Trend** (12-1 momentum) | 22.5% | 18.2% | 0.92 | 0.76 | -46% | 8/11 | **Pass** (all 5 criteria; not blind, see SPEC) |
| **Contrarian** (21-day losers) | 0.7% | 1.6% | 0.16 | 0.18 | -73% | 1/11 | **Fail** (every criterion) |
| **Defensive** (low volatility) | 10.6% | 4.4% | 0.84 | 0.44 | -25% | 3/11 | **Fail** (criteria 1 and 2) |
| Council (frozen, reference) | 18.3% | 10.1% | 1.11 | 0.71 | -35% | | |
| Equal-weight universe | 14.6% | 13.2% | 0.83 | 0.78 | -52% | | |
| Null control | 10.6% | 8.7% | 0.57 | 0.51 | -58% | | |

**Trend.** All 9 neighbouring variants have Sharpe 0.86-1.06 (median 0.96); doubled implicit costs
cost little (0.92 -> 0.90). It is volatile: -46% max drawdown, years from -17% to +127%.

**Contrarian.** Buying the most liquid recent losers lost money relative to everything, in every
variant (Sharpe 0.03-0.20). In Indian large/mid caps over 2016-26, 1-month losers kept losing.

**Defensive.** The steadiest book (-25% max drawdown, positive in 2018 when the market fell 19%),
but it lagged badly in 2022-26 and beat the market in only 3 of 11 years, so it fails as a
stand-alone pod under the pre-set rules.

**Diversification.** Daily excess returns over the equal-weight universe: trend vs defensive -0.32,
trend vs contrarian 0.03, trend vs council -0.04, defensive vs council 0.41. The trend pod and the
council make nearly unrelated bets, which is useful for a combined book.

Note: the equal-weight universe is much stronger at Rs 10L (14.6% a year) than in the Rs 1L study
(7.7%), because at Rs 1L many shares cost more than a slot.

**Conclusion under the pre-set rules.** Only Trend passes. Contrarian and Defensive are rejected as
pods. Using low volatility as a hedge inside the risk engine would be a new hypothesis and needs
its own rules written down before it is tested.
