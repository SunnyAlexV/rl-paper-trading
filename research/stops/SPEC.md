# Stop-losses on momentum + delivery: rules (written 27 Nov 2026, BEFORE the run; run once)

Research only: the primary test is frozen; a stop rule that passes could only become a new paper account.

Base: the primary rule (momentum + delivery composite, hold 20 / sell when out of the top 100, max 7.5%, min trade 1%),
Rs 10L, `backtest.run`, Stage 2 (all fees, post-tax), 2 Jul 2012 - 26 Nov 2026. Decisions at the close, fills at the next
open (overnight gaps included). Reference prices are back-adjusted closes.

| Stop | Rule | Settings (judged in bold) |
|---|---|---|
| Fixed | sell a holding whose close is X% below its close on the day it was chosen | 10, **15**, 20% |
| Trailing | sell a holding whose close is X% below its highest close since it was chosen | 10, **15**, 20% |
| Portfolio | when NAV is X% below its running peak, hold every position at half weight (50% cash) for 21 trading days, then return to full; the peak resets at that point | 10, **15**, 20% |

A stopped stock is replaced by the best-ranked stock not held and not stopped out in the last 21 trading days.

**A stop helps only if, at the judged setting and at least one other:** max drawdown improves by at least 20% of the base
(from -32% to -25.6% or better) **and** Sharpe is no more than 0.05 below the base's.
