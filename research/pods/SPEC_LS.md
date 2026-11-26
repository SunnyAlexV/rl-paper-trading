# Long-short pods: rules and pass/fail criteria (written 27 Nov 2026, BEFORE any long-short backtest)

Research only. Shorts are possible here only through futures, so every short is a stock-futures or
NIFTY-futures position, as a real Indian account would hold it. Nothing trades; the primary test
is untouched.

**What is not blind.** 12-1 momentum and the council have been backtested long-only (round 1,
`research/momentum/`). The short legs and the hedged book have not been run.

## Data (added to the rebuilt history, see README.md)

F&O bhavcopy futures rows (stock futures and NIFTY index futures, nearest two expiries: open,
close, settle, open interest, contracts; lot size only in files after Jul 2024) and the daily F&O
ban list, Jun 2011 - 26 Nov 2026 (`get_futures.py`).

## Book

- **Paper capital Rs 2 crore per book.** One stock-futures lot is worth about Rs 6.5 lakh at the
  median (Rs 2.8-12.9 lakh, 26 Nov 2026), so smaller books cannot hold a diversified short leg.
- **Long leg:** 80% of NAV in cash equities, 20 names equal weight, from the universe mask.
  Sell when a holding leaves the top 100 (5 x k).
- **Short leg:** short stock futures with notional 80% of NAV, 15 names equal weight, from universe
  stocks that have stock futures that day. Cover when a short leaves the bottom 45 (3 x k) of the
  F&O names. No new short in a stock on the F&O ban list that day.
- **Cash buffer** 20% of NAV for margin. Margin assumed at 20% of short notional (stock futures
  SPAN plus exposure margin is typically 15-25%). If losses push cash below the requirement, longs
  are sold pro rata to restore it plus 2% of NAV; such events are counted and reported.
- **Month-end:** both legs are re-equalised to their targets; in between, only band replacements.
- **Fills:** decide at the close, fill at the next open (cash open for stocks, futures open of the
  traded contract). Value-based positions (fractional shares and contracts); whole-lot feasibility
  is reported separately using 2024-26 lot sizes.
- **Futures mechanics:** trade the nearest expiry; roll to the next expiry at the open when 3 or
  fewer trading days remain. Daily mark to the futures close. Corporate actions: the equity
  adjustment factor is applied to futures on ex-dates.
- **Costs (today's schedule applied to the whole history, as in every repo backtest).**
  Cash leg: the repo's `costs.py` (explicit + half-spread + square-root impact).
  Futures (Zerodha, as known mid-2026, to be verified): brokerage min(Rs 20, 0.03%) per order,
  STT 0.02% on sells, exchange 0.00173%, SEBI Rs 10/crore, stamp 0.002% on buys, GST 18% on
  brokerage + exchange + SEBI; implicit cost = the underlying stock's half-spread + impact
  (conservative: futures are usually at least as liquid as the stock). No interest on cash.
- **Tax is not modelled** for long-short books: futures profits are business income taxed at the
  person's slab, so the after-tax result depends on Sunny's whole income. All comparisons in this
  round are **pre-tax**, including the long-only comparators, which are rerun in the same simulator.

## Books tested

| Book | Long leg | Short leg |
|---|---|---|
| **LS-Trend** | top 20 by 12-1 momentum | bottom 15 F&O names by 12-1 momentum |
| **LS-Council** | top 20 by frozen council score | bottom 15 F&O names by council score |
| **Hedged-Trend** | top 20 by 12-1 momentum, 80% of NAV | short NIFTY futures, notional = long value x 60-day beta of the long leg to the Nifty 50 (clipped 0-1.5), reset monthly; margin 12% |

Comparators, same simulator, pre-tax: Long-Trend and Long-Council (20 names, 100% invested, same
band rules), equal-weight universe (monthly), Nifty 50 price index.

## Pass/fail (pre-tax, Feb 2016 - 26 Nov 2026)

LS-Trend and LS-Council each pass only if **all** hold:
1. Sharpe >= 0.8 over the whole period and >= 0.5 in 2022-26.
2. Max drawdown no worse than -25%.
3. Positive in at least 7 of 11 calendar years.
4. Low market exposure: daily return correlation with the Nifty 50 between -0.4 and 0.4.
5. Robustness: the median of 9 variants (long 15/20/25 x short 10/15/20 names) meets criterion 1.
6. With implicit costs doubled, whole-period Sharpe >= 0.6.

Hedged-Trend passes if its Sharpe beats Long-Trend's and its max drawdown is at least 30% smaller.

Reported for every book: the short leg's own P&L, beta to the Nifty 50, margin events, turnover,
and position sizes in lots.
