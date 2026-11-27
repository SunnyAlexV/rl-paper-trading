# "Bad news exit" on momentum + delivery: rules (written 27 Nov 2026, BEFORE the run; run once)

Motivation (`DIAGNOSTIC.md`, crash event study, all universe stocks 2012-2026): after a stock-specific one-day crash
(stock -15% or worse while the equal-weight universe fell less than 1% that day) stocks trailed the average stock by
4.4 / 6.0 / 8.5 points over the next 1 / 3 / 6 months; after crashes on market-wide down days (universe -3% or worse)
they beat it by 3.1 / 3.8 / 2.3 points. The idea (Sunny): exit on disasters caused by the stock's own problems, not on
normal swings or market-wide shocks. This idea was formed after seeing that event study, so it is not blind.

Base, engine and period as `SPEC.md` (momentum + delivery, hold 20 / band 100, Rs 10L, Stage 2 post-tax, Jul 2012 - Nov 2026).
Rule: if a holding's close-to-close return is at or below -X while the equal-weight universe's return that day is above
-1%, sell it at the next open; it may not be bought again for 63 trading days; the freed money goes to the best-ranked
eligible stock (as any band replacement). X = 10%, **15% (judged)**, 20%.

Pass (it must cost nothing): at the judged X and one other, CAGR and Sharpe both at or above the base's (26.7%, 1.38).
Also reported: number of exits, and the worst single-holding loss with and without the rule.
