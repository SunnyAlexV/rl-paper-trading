# Stops executed like real stop orders (intraday): rules (written 27 Nov 2026, BEFORE the run; run once)

Correction prompted by Sunny: earlier stop tests checked the close and sold at the next open; real stop-loss orders
rest at the exchange and trigger intraday. Re-run with daily open/high/low/close (back-adjusted):
- if the day opens at or below the stop: sold at the open (gap);
- else if the day's low reaches the stop: sold at the stop price;
- if the stock opens below the stop and its high equals its low (locked at the lower circuit): no fill that day; retried
  the next day.
A value-based daily simulator (fractional shares) with the repo's cash costs (`costs.py`: explicit + half-spread +
impact); **pre-tax**; Rs 10L; Jul 2012 - Nov 2026. Book: momentum + delivery, hold 20 / sell when out of the top 100 at the
close (filled next open), max 7.5%. Base without stops in the same simulator.

Stops (same definitions as `SPEC.md` / `SPEC_CLIMB.md`; levels updated at each close, active from the next open):
fixed 15% below entry; trailing 15% below the highest close; climbing pins m = 2 (rest and reinvest).
Rest: stop proceeds wait in cash until the next month-end. Reinvest: next open, best-ranked eligible stock.
Stopped stocks cannot be re-bought for 21 trading days.

Pass (as before): max drawdown at least 20% smaller than this simulator's base **and** Sharpe no more than 0.05 below it.
