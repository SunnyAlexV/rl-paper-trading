# Integrated long-only score: rules and pass/fail criteria (written 27 Nov 2026, BEFORE this backtest)

Research only; the primary test is untouched.

**What is not blind.** This idea was formed after round 1 (momentum passed; low volatility failed
alone but moved against momentum, excess-return correlation -0.32) and after the 26 Nov
signal-health check (delivery signals weak in the last year). The weights are not fitted, but the
choice of ingredients was influenced by those results.

## Score

Each trading day, within the universe mask, three ingredients are turned into cross-sectional
rank z-scores (`alpha.scoring.zrank`) and **averaged with equal weights (1/3 each). Nothing is fitted.**

| Ingredient | Philosophy | Definition |
|---|---|---|
| Momentum | Winners keep winning | close(t-21) / close(t-252) - 1 |
| Low volatility | Calm stocks pay better per unit of risk | minus the standard deviation of daily returns over 250 days |
| Delivery | Buyers who take delivery are committed | mean delivery percentage (delivered / traded quantity) over 60 days |

A stock missing an ingredient gets 0 (neutral) for it, as in `zrank`.

## Book

Same as round 1 (`SPEC.md`): Rs 10,00,000, long only in cash, hold 20, sell when out of the
top 100, decide daily at the close and fill at the next open, max 7.5% per stock, minimum trade 1% of NAV,
the repo's cost and **tax** engine (`backtest.run`), price returns. Feb 2016 - 26 Nov 2026.

## Pass/fail (post-tax)

The integrated book passes only if **all** hold:
1. Sharpe over the whole period >= 1.0 and above the Trend pod's (0.92); CAGR in 2022-26 above
   both the frozen council's (10.1%) and the equal-weight universe's (13.2%).
2. Max drawdown no worse than -40%.
3. Beats the equal-weight universe in at least 7 of 11 calendar years.
4. Robustness: the median of 9 variants (holdings 15 / 20 / 25 x all lookbacks -25% / as specified / +25%)
   meets criterion 1.
5. With implicit costs doubled, whole-period Sharpe >= 0.9.

Diagnostics only (not pass/fail): the three two-ingredient versions, to show what each ingredient
adds, and the correlation of excess returns with the council and the Trend pod.
