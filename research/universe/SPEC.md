# Which universe should momentum + delivery pick from? (written 27 Nov 2026, BEFORE the run; run once)

Same rule as the primary (equal-weight rank z-scores of 12-1 momentum and 60-day delivery %, computed **within** each
universe; hold 20, sell when out of the top 100, or top half if the universe is under 200 names; max 7.5%; min trade 1%),
Rs 10L, `backtest.run`, Stage 2 (all fees, post-tax), Jul 2012 - Nov 2026. Universes (point in time, each day, all
inside the current mask):
- current: top 500 by 60-day median traded value (the primary);
- top 300, top 200, top 100 by 60-day median traded value;
- current minus the most volatile third (250-day volatility);
- F&O stocks only (stock futures that day).
Each universe's own equal-weight portfolio is also reported.

A menu, not a pass/fail: report CAGR, Sharpe, max drawdown and 2022-26 CAGR. A universe is a candidate if its max
drawdown is at least 5 points smaller than the current universe's and its Sharpe is no more than 0.10 lower.
