# Philosophy pods: rules and pass/fail criteria (written 26 Nov 2026, BEFORE any pod backtest)

Research only. Nothing here trades, and the primary test (`paper/`) is untouched. A pod that passes
goes to paper trading only through a dated amendment in `PREREGISTRATION.md`, decided by Sunny.

**Honesty note.** The Trend pod's signal (12-1 momentum) was already backtested on 18 Nov 2026
(`research/momentum/`), so it is not blind. The other pods have not been run on this data.

## Data

NSE bhavcopy, security-wise delivery, F&O bhavcopy and index closes, Jun 2011 - 26 Nov 2026,
downloaded again from NSE archives into a separate working copy (see `README.md`). Check: the
frozen council's 2022-26 return is 11.1% a year (pre-registration: about 11%), and monthly returns of
the council, momentum and null control correlate 0.96-0.997 with the 18 Nov rebuild.
Price returns only (dividends not modelled), as in every earlier backtest.

## Common rules (all pods)

- Universe: the existing point-in-time tradable mask (top 500 by 60-day median traded value,
  price >= Rs 20, 250 days of history, median traded value >= Rs 5 crore).
- Rs 10,00,000 per pod, long only in cash (no leverage), decide at close, fill at next open,
  the repo's cost and tax engine (`backtest.run`), minimum trade 1% of NAV, **max 7.5% per stock**.
- **No parameter is tuned.** Every number below is a textbook default fixed now.
- Periods: 2016-19, 2020-21, 2022-26 and all (Feb 2016 - Nov 2026). No pod has fitted weights,
  so the whole period is out of sample for the rules themselves.

## The pods

| Pod | Philosophy | Rule |
|---|---|---|
| **Trend** | Winners keep winning | Rank by 12-1 momentum (close t-21 / close t-252 - 1). Hold 20, sell when out of the top 100. |
| **Contrarian** | Short-term overreactions revert | Among the 200 most liquid universe stocks, rank by the 21-day return, lowest first. Decide weekly (last trading day of the week). Hold 20, sell when out of the bottom 60. |
| **Defensive** | Calm stocks pay better per unit of risk | Rank by 250-day volatility of daily returns, lowest first. Decide monthly. Hold 20, sell when out of the lowest 100. |
| **Relative value** | Mispriced pairs converge | Needs short futures, which the long-only engine cannot do. Specified separately once a futures-capable engine exists; not part of the first round. |

Pod-level risk (applied in a second run, after each pod's raw result):
- Volatility target: scale invested fraction to 15% / realised 60-day pod volatility, capped at 100%.
- Drawdown rule, measured **relative to the equal-weight universe** (a long-only pod falls 5% with
  the market routinely, so an absolute 5% rule would keep pods switched off): relative drawdown
  5% halves the pod, 7.5% sets it to cash until its shadow (unscaled) relative NAV regains its
  60-day average.

Allocator (third run): equal risk across pods (inverse 60-day volatility of pod returns), monthly,
with a slow tilt toward 12-month Sharpe (at most +-25% of the equal-risk weight) and a penalty
when two pods' 60-day return correlation exceeds 0.3. No RL at this layer.

## Pass/fail (all post-tax, Feb 2016 - Nov 2026, against the same engine)

A pod passes only if **all** hold:
1. Sharpe above both the equal-weight universe and the null control over the whole period,
   and CAGR above both in 2022-26.
2. Beats the equal-weight universe in at least 6 of the 11 calendar years.
3. **Robustness (path sensitivity):** the median of 9 neighbouring variants (holdings 15 / 20 / 25
   x lookback -25% / as specified / +25%) also meets criterion 1.
4. With costs doubled, Sharpe still beats the equal-weight universe.
5. Max drawdown no worse than 1.25 x the equal-weight universe's.

A pod is useful to the combination only if adding it raises the allocator book's Sharpe and its
return correlation with the other pods is below 0.7.

RL versions of any pod are challengers only: built later, with purged walk-forward training,
and kept only if they beat that pod's rule above on the same test.
