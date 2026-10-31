# Pre-registration: forward paper-trading of the research-council system

Frozen on 31 Oct 2026, before any paper-trading day. This commit is the record; nothing in
`results/alpha_c_council_real.json`, `paper/config.json` or the trading code may change during the
test. Any fix that becomes necessary is made in a separate, dated commit that explains why, and the
test clock restarts from that commit.

## The system

- **Universe:** each month, the 500 most-traded NSE EQ-series stocks (60-day median traded value,
  price >= Rs 20, >= 250 trading days of history); tradable if 60-day median traded value >= Rs 5 crore.
- **Signal:** the research council's combined model, 17 formulas from three MCTS researchers
  (price-volume, delivery, derivatives) and one LLM researcher, blended with least-squares weights
  fitted on 2013-19 only. File: `results/alpha_c_council_real.json`,
  SHA-256 `9afc257d4f56777af65ac00af27913146c6a1cecc803dbe5504a8d09e30cc4f3`.
- **Trading rule:** band rule. Hold 20 names; replace a holding only when it falls out of the top 100;
  new names share the freed weight equally; skip stocks whose single share costs more than a slot.
  Top-ups and trims smaller than 1% of NAV are skipped. Long only, no leverage.
- **Capital:** Rs 1,00,000. Orders are decided after the close and filled at the next open.
- **Costs and tax:** Zerodha equity delivery, resident individual. STT, stamp duty, NSE transaction
  charges, SEBI fee, GST, DP charge (Rs 15.34 per scrip per sell day), spread by liquidity tier,
  square-root impact; FIFO lots, 20% short-term / 12.5% long-term capital gains tax plus 4% cess.

## Procedure

Every NSE trading day at about 8:45 pm IST a scheduled job: downloads that day's bhavcopy, delivery
and F&O files; applies corporate actions; fills the previous evening's orders at today's open;
records NAV in `paper/nav.csv`; writes the next orders to `paper/orders_after_<date>.json`; appends
the file's SHA-256 to `paper/ledger.txt`; and commits everything here before the next open. The
commit timestamps prove each decision was made before the market it trades in.

## What will be compared

1. **Primary:** post-tax NAV of the system.
2. **Controls:** the same band rule on the council built from the no-edge (null) market
   (`results/alpha_c_council_null.json`); the equal-weight universe; the Nifty 50.
3. **Minimum length before any conclusion:** 12 months. Expected backtest behaviour, for reference
   only: 21.7% a year after costs and tax (Sharpe 1.22, Jan 2013 - Oct 2026), but only about 11%
   a year in 2022-26, roughly level with the null control. The backtest edge is weakest in recent
   years, which is why this forward test decides.

## Known limitations stated in advance

Price returns in the backtest (dividends not modelled); assumed mid-cap spreads; single research
seeds (a multi-seed check is running and will be reported in a separate commit without changing
the frozen system); delisting exits at the last traded price.
