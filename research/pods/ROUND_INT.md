# Integrated long-only score results (27 Nov 2026)

Rules and criteria: `SPEC_INT.md` (committed before this run). Script: `int_bt.py`. Rs 10L, Feb 2016 -
26 Nov 2026, post-tax, max 7.5% per stock. Files: `int_metrics.csv`, `int_years.csv`, `int_navs_monthly.csv`.

| Book | CAGR all | 2016-19 | 2020-21 | 2022-26 | Sharpe all | Sharpe 22-26 | Max DD |
|---|---|---|---|---|---|---|---|
| **Integrated** (momentum + low vol + delivery, equal weights) | 18.1% | 19.5% | 33.3% | 11.1% | **1.23** | 0.84 | **-28%** |
| Council (frozen) | 18.3% | 12.4% | 53.5% | 10.1% | 1.11 | 0.71 | -35% |
| Trend pod | 22.5% | 15.9% | 46.8% | 18.2% | 0.92 | 0.76 | -46% |
| Equal-weight universe | 14.6% | 5.6% | 38.1% | 13.2% | 0.83 | 0.78 | -52% |

**Verdict: Fail** under the pre-set rules.

| Criterion | Result |
|---|---|
| 1. Sharpe >= 1.0 and > 0.92; 2022-26 CAGR > 10.1% and > 13.2% | Sharpe passes (1.23); **2022-26 CAGR 11.1% fails** (below the equal-weight universe) |
| 2. Max DD no worse than -40% | Pass (-28%) |
| 3. Beats equal weight in >= 7 of 11 years | **Fail (5 of 11)** |
| 4. Median of 9 variants meets 1 | **Fail** (Sharpe median 1.23 passes; 2022-26 CAGR median 11.6% fails) |
| 5. Doubled implicit costs, Sharpe >= 0.9 | Pass (1.22) |

It is the steadiest book tested (best Sharpe and smallest drawdown; +8% in 2018 when the universe
fell 19%), but low volatility held it back in the 2022-26 bull market.

**Diagnostics (not pre-registered candidates):**

| Two-ingredient version | CAGR all | 2022-26 | Sharpe all | Max DD |
|---|---|---|---|---|
| Momentum + delivery | 27.8% | 21.7% | 1.35 | -33% |
| Momentum + low vol | 19.1% | 14.1% | 1.19 | -28% |
| Low vol + delivery | 11.4% | 5.7% | 0.91 | -25% |

Momentum + delivery is the strongest book in any round so far. It was found by looking at three
diagnostic combinations after the fact, so it is a hypothesis, not a result. The only clean test
left for it is forward paper trading.

Excess-return correlations: integrated vs council 0.47, vs trend pod -0.24.
