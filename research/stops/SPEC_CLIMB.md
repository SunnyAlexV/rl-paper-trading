# "Climbing protection" stops on momentum + delivery: rules (written 27 Nov 2026, BEFORE the run; run once)

Sunny's idea: protection like a climber's pins. Slack lets the stock move normally; pins go in as it climbs and only
move up; after a fall the climber rests before climbing again. Research only (the primary is frozen).

Base, engine and period as `SPEC.md` (momentum + delivery, hold 20 / band 100, Rs 10L, Stage 2 post-tax, Jul 2012 - Nov 2026,
decide at the close, fill at the next open).

For each holding, every day at the close (back-adjusted closes):
- **slack** d = m x (20-day standard deviation of daily returns) x sqrt(20), clipped to [10%, 30%], fixed at the day the
  stock is chosen; m = 1.5, **2 (judged)**, 3.
- **first pin**: stop = entry x (1 - d).
- **climbing pins**: track the highest close H since entry; whenever H has risen by at least d/2 above the H used for
  the last pin, the stop moves up to H x (1 - d). The stop never moves down.
- **safety pin**: once a close is at least entry x (1 + d), the stop is never below entry.
- A close at or below the stop sells the holding at the next open.
- **Rest (judged variant)**: the proceeds stay in cash until the next month-end; at month-end the book refills empty
  slots with the best-ranked stocks not stopped out in the last 21 trading days. **Reinvest variant**: refill immediately
  (as in `SPEC.md`).

Pass: at m = 2 with rest, and at least one other m with rest: max drawdown -25.6% or better **and** Sharpe >= 1.33.
