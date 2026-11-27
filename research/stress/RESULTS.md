# Stress tests of momentum + delivery: results (27 Nov 2026)

Criteria: `SPEC.md` (committed before the run). Stage 2 (all fees, post-tax), Jul 2012 - Nov 2026, Rs 10L unless stated.

| Test | Result | Pass bar | Verdict |
|---|---|---|---|
| 1. Random halves (50 halves of the stock list) | Beat its half's equal-weight universe in **50 of 50** (median Sharpe 1.24 vs 0.78; smallest margin +0.18; median 18.3% vs 13.2% a year) | >= 90% | **Pass** |
| 2. 36-month windows (137) | Beat the equal-weight universe in **100%** (worst window still +11.4 pts, median +60.9 pts) | >= 75% | **Pass** |
| 3. Implicit costs x2 / x3 | Sharpe 1.36 / 1.33 (CAGR 26.3% / 25.4%) vs equal weight 0.79 / 0.78 | x2 above EW | **Pass** |

Shorter windows: 24 months, beat equal weight in 98.7% of 149 windows (worst -2.2 pts, from Aug 2024);
12 months, 85.1% of 161 windows (worst -24.9 pts, from Jul 2013); an absolute loss in 14% of 12-month windows and 4% of
24-month windows.

**Drawdowns (five deepest):**

| Peak | Trough | Depth | Recovered | Months peak to recovery |
|---|---|---|---|---|
| 19 Feb 2020 | 23 Mar 2020 | -31.8% | 3 Aug 2020 | 5.5 |
| 23 Sep 2024 | 28 Feb 2025 | -27.8% | 7 Aug 2026 | 22.5 |
| 11 Jan 2018 | 9 Oct 2018 | -26.2% | 4 Feb 2020 | 24.8 |
| 11 Apr 2022 | 20 Jun 2022 | -24.0% | 6 Sep 2022 | 4.9 |
| 7 Aug 2015 | 29 Feb 2016 | -21.7% | 25 Jul 2016 | 11.6 |

Against the equal-weight universe: deepest relative drawdown -27.4%; longest stretch below a previous relative peak
about 21 months.

**Capital:** Rs 1L 27.8% a year (Sharpe 1.43, max DD -34%); Rs 50L 25.0% (1.32, -32%).

All three pass criteria are met. Caveats stand: backtest only; the delivery idea is partly hindsight; drawdowns of
25-32% with up to two years to recover are normal for this rule.
