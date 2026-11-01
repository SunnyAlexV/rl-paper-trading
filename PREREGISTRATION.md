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

Price returns in the backtest (dividends not modelled; see the amendment below); assumed mid-cap spreads; single research
seeds (a multi-seed check is running and will be reported in a separate commit without changing
the frozen system); delisting exits at the last traded price.

## Amendment, 1 Nov 2026 (before the first paper-trading day)

The paper trader now credits cash dividends: on each ex-date, holdings at the previous close
receive the announced dividend (NSE corporate-action announcements, `data_download_corpact.py`,
parsed by `alpha/dividends.py`), net of slab-rate tax (30% + 4% cess). When NSE adjusts PREVCLOSE for
an extraordinary dividend, the payment is credited as cash and the share count is not scaled.
`nav.csv` gains a `dividends_gross` column. The signal, the trading rule, the costs and the config
are unchanged. No paper-trading day had been run, so the 12-month clock starts with the first run
as planned.

With the same dividend treatment in the backtest (`research/dividends/`), the frozen council
returns 22.2% a year after costs and tax over Jan 2013 - Oct 2026 (Sharpe 1.25), and 11.6% a year in
2022-26 (Sharpe 0.78). Its null twin returns 10.7% a year overall and 11.4% in 2022-26.

## Correction, 1 Nov 2026 (before the first paper-trading day): expected backtest figures

The figures quoted above (21.7% a year; 22.2% with dividends) came from a backtest of the band rule
**without** the slot rule this system trades with: skip a new name whose single share costs more
than a slot. Backtesting the rule exactly as traded (with dividends, no interest on idle cash) gives
**19.2% a year after costs and tax, Jan 2013 - Oct 2026 (Sharpe 1.13), and 8.1% a year in 2022-26
(Sharpe 0.58)**. These are the reference figures for this test. The two rules are both about
99.5% invested; the 3-point gap comes from which names happen to be held. That shows how much
single-name luck sits in any one backtest path.

The same luck shows when the rule's settings are varied (`research/timing/path_noise.csv`). Over
9 variants (15, 20 or 25 names; band 60, 100 or 150), the full-period Sharpe ranges from 0.95 to 1.36
and the 2022-26 Sharpe from 0.46 to 0.95. The frozen settings (20 / 100) sit in the middle overall
and in the lower half for 2022-26. Nothing in the system changes; only the reference numbers are
corrected.
