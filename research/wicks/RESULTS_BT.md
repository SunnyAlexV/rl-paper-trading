# Wick backtest and momentum + delivery holdout: results (27 Nov 2026)

Rules: `SPEC_BT.md` (committed before the run). Jul 2012 - Nov 2026, Rs 10L, k = 20 unless stated (`wick_bt_metrics.csv`).

| Book | Stage 2 CAGR all | Stage 2 Sharpe all | 2012-15 holdout CAGR / Sharpe (Stage 2) | 2022-26 CAGR (Stage 2) | Max DD (Stage 2) | Turnover/yr |
|---|---|---|---|---|---|---|
| Equal-weight universe | 13.3% | 0.79 | 11.2% / 0.68 | 12.8% | -49% | 0.4 |
| Momentum 12-1 | 20.0% | 0.87 | 14.3% / 0.76 | 20.4% | | 2 |
| **Momentum + delivery** | **26.7%** | **1.38** | **26.2% / 1.71** | 21.9% | -32% | 1.8 |
| Momentum + delivery + wick | 21.8% | 1.26 | 24.4% / 1.62 | 13.1% | -33% | 4.8 |
| Wick alone | 7.2% | 0.51 | 9.2% / 0.61 | 4.3% | -53% | 11.2 |

**A. Wick as its own pod: Fail.** Stage 1 Sharpe 0.81 vs 0.82 for the equal-weight universe (median of k variants 0.79);
Stage 2 0.51 vs 0.79. The signal is real (rank IC +0.03, t 4.2, `README.md`) but too small for its turnover (11x a year).

**B. Wick adds to momentum + delivery: Fail.** Adding it lowered Stage 2 Sharpe in all three variants
(k = 15: 1.12 vs 1.44; k = 20: 1.26 vs 1.38; k = 25: 1.23 vs 1.42), mainly by nearly tripling turnover.

**C. Holdout for momentum + delivery: Pass.** In Jul 2012 - Dec 2015, a period its rules never saw, it returned 26.2% a
year post-tax (Sharpe 1.71) against 11.2% (0.68) for the equal-weight universe; k = 15 and 25 gave 28.2% / 1.78 and
26.4% / 1.77. Caveats: the universe was small then (about 180-230 stocks), and the delivery ingredient was partly
suggested by the council, whose weights were fitted on 2013-19, so the holdout is clean for the rule but not
perfectly clean for the idea. Momentum has decades of outside evidence.

## Wick long-short (rules `SPEC_LS.md`, pre-tax, Rs 2 crore, Jul 2012 - Nov 2026; `wick_ls_metrics.csv`)

| Book | CAGR | Sharpe | Max DD | Positive years |
|---|---|---|---|---|
| **Long lower wick / short upper wick** | **-9.7%** | **-0.97** | **-77%** | 2/15 |
| Same, implicit costs doubled | -16.3% | -1.70 | -92% | 0/15 |
| Long-only lower wick (same simulator) | 6.1% | 0.45 | -56% | 9/15 |
| Equal-weight universe | 12.4% | 0.72 | -55% | 11/15 |
| Nifty 50 (price) | 11.7% | 0.79 | -38% | 13/15 |

**Fail on every criterion.** The short leg lost 65% of starting capital over the period; it made money only in 2013,
2016, 2018 and 2022. Upper wicks carry almost no predictive information (rank IC -0.013 at 20 days, t -1.7), so the
short leg was close to shorting at random in a market that rose about 12% a year, and its fast turnover added costs.

## Upper wick as a SELL signal on long holdings (rules `SPEC_EXIT.md`; Jul 2012 - Nov 2026, Rs 10L; `wick_exit_metrics.csv`)

| Book | Stage 2 CAGR | Stage 2 Sharpe | Max DD | Turnover/yr |
|---|---|---|---|---|
| Equal-weight universe | 13.3% | 0.79 | -49% | 0.4 |
| Lower-wick band rule (no exit signal) | 7.2% | 0.51 | -54% | 11.0 |
| **Pure wick, sell on upper wick top 20% (judged)** | 7.8% | 0.53 | -42% | 3.4 |
| Pure wick, top 10% / top 30% | 9.8% / 7.4% | 0.63 / 0.51 | -41% / -46% | 1.7 / 5.4 |
| Mom + deliv (no exit signal) | 26.7% | 1.38 | -32% | 1.8 |
| **Mom + deliv + upper-wick exit top 20% (judged)** | 17.6% | 0.98 | -34% | 6.3 |
| Mom + deliv + exit top 10% / top 30% | 19.6% / 15.4% | 1.07 / 0.89 | -37% / -32% | 3.9 / 9.0 |

**Book 1 (pure wick): Fail.** The upper-wick exit is an improvement on the band rule (turnover 11 -> 3.4 a year, drawdown -54% -> -42%),
but the book still trails the equal-weight universe by a wide margin (Sharpe 0.53 vs 0.79).
**Book 2 (exit added to momentum + delivery): Fail.** Every threshold lowered returns; the more often it sold, the worse
(Sharpe 1.38 -> 1.07 / 0.98 / 0.89). Strong stocks often show upper wicks near their highs, so the rule sold winners early and
more than tripled trading.
