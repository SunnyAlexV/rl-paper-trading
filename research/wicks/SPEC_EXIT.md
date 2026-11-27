# Upper wick as a SELL signal on long holdings (written 27 Nov 2026, BEFORE the run; run once)

Sunny's clarification: no shorting. Buy on a strong lower wick; sell the holding when its upper wick turns strong.

Engine as every pods test (`backtest.run`): Rs 10L, long only, decide at the close, fill at the next open,
max 7.5% per stock, min trade 1% of NAV, 20 holdings, freed weight shared equally by new names.
Period 2 Jul 2012 - 26 Nov 2026; Stage 1 (spread + impact) and Stage 2 (all fees, post-tax).
Wick shares are 20-day means: lower = (min(open, close) - low) / (high - low), upper = (high - max(open, close)) / (high - low).
"Upper wick strong" = the stock's 20-day upper-wick share is in the top X% of the universe that day, X = **20 (judged)**,
also 30 and 10.

Books:
1. **Pure wick:** buy the highest 20-day lower-wick stocks; sell a holding only when its upper wick is strong
   (or it leaves the universe). New buys skip stocks whose upper wick is strong.
2. **Mom + deliv + upper-wick exit:** the live momentum + delivery band rule (sell when out of the top 100), plus sell
   when the holding's upper wick is strong; new buys skip stocks whose upper wick is strong.
Comparators: equal-weight universe; mom + deliv without the exit; lower-wick band rule without the exit (sell when out
of the top 100).

Pass:
- **Book 1:** Stage 2 Sharpe above the equal-weight universe and above the lower-wick band rule, at X = 20 and at
  least one of X = 10 / 30.
- **Book 2:** Stage 2 Sharpe above mom + deliv without the exit, at X = 20 and at least one of X = 10 / 30.
