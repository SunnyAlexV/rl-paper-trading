# Multi-asset menu: rules (written 27 Nov 2026, BEFORE the run; run once)

Goal (Sunny): stay afloat first, then returns. Find the highest-return mix for each worst-fall limit.

**Assets (daily, pre-tax):**
- **E**: momentum + delivery equity sleeve, the primary rule (`backtest.run`, Rs 10L, all fees, pre-tax NAV), Jul 2012 - Nov 2026;
- **G**: gold, GOLDBEES (split-adjusted close, `etf_series.py`);
- **US**: Nasdaq-100 in rupees, N100/MON100;
- **C**: cash/debt at a constant 6.5% a year (no Indian debt ETF covers 2012-16; SETF10GILT from Jun 2016 is reported as
  a check, not used for selection).

**Mixes:** weights in steps of 10%: E 0-100%, G 0-40%, US 0-30%, C = the rest (>= 0). Rebalanced at each month-end
to target; each rebalance costs 0.15% of the value traded.

**Selection without hindsight:** for each worst-fall limit (10%, 15%, 20%, 25%, none), pick the mix with the highest
CAGR whose max drawdown over the **design period (Jul 2012 - Dec 2019)** is within the limit; then report that same mix
over the **test period (Jan 2020 - Nov 2026)**, unseen when it was picked, and whether its test drawdown stayed within
the limit. Full-period best mixes are reported for reference only (hindsight).

Reported for every chosen mix: design and test CAGR, Sharpe, max drawdown, worst calendar year.
