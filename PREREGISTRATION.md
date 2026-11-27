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

## Amendment, 16 Nov 2026 (parallel Rs 10,00,000 account)

Added after the 16 Nov close. The Rs 1,00,000 account in `paper/` is unchanged and remains the
primary test. A second paper account, `paper_10L/`, runs the identical frozen system
(`paper/config_10L.json` differs only in `capital`) with Rs 10,00,000. Its only purpose is to
measure how much whole-share rounding (about Rs 5,000 per name at Rs 1,00,000) affects results.
It starts with orders written after the 16 Nov close, filled at the 17 Nov open. It runs each
evening after the primary account with `--out paper_10L --no-download`, on the same data, with
its own ledger and the same 12-month minimum.

## Amendment, 16 Nov 2026 (exploratory fleet)

Five more paper accounts start with orders written after the 16 Nov close (first fills 17 Nov
open), listed in `paper/fleet.json` and run nightly by `run_fleet.py` on the same data, after the
primary: daily equal-weight top 20 with no band and no minimum trade (Rs 10L and Rs 1L); band rule
25/60 and 15/150 (Rs 10L); and the pre-registered null control, the band rule on the no-edge
council (Rs 10L). All pay the same fees, costs and tax. The daily rule is a new branch in
`alpha/paper_trade.py`; the band-rule code path used by the primary is unchanged. These accounts
are exploratory: the Rs 1,00,000 account in `paper/` remains the primary test and its rule,
signal and conclusion criteria are unchanged.

Backtest of these variants on the only data the repo holds (Jul 2025 - Nov 2026, post-tax, no
dividends; `research/fleet/`): at Rs 10L, frozen 20/100 +12.4%, 15/150 +15.3%, 25/60 +0.8%,
daily no-band -3.6% (costs Rs 2.57L, 26% of capital), null control -1.6%. At Rs 1L the daily
rule lost 24%. Sixteen months is far too short to rank these; it is recorded before the live
results so they cannot be cherry-picked afterwards.

## Amendment, 16 Nov 2026 (benchmarks and timing-agent account)

- **Benchmarks.** `data_download_indices.py` stores daily closes of the Nifty 50, Nifty 500, Nifty
  Midcap 150 and Nifty Smallcap 250 (NSE price indices) from 30 Oct 2026. `fleet_report.py`
  writes `paper/fleet_report.md`: each account's post-tax return since its start against the
  indices over the same dates. Both run nightly after the accounts. The Nifty 50 is the
  pre-registered market control.
- **Timing account.** `paper_timed_10L/` (Rs 10L) runs the frozen band rule (20 / 100) with the
  research timing agent `agent_s0` (`research/timing/`), which sets the invested fraction to 1,
  0.5 or 0; idle cash earns 5.5% a year taxed at slab rate. Live code: `alpha/timing_live.py`.
  Because the repo keeps 500 trading days, the agent's two strategy-health features use the band
  rule re-simulated over that window (without dividends). On 16 Nov 2026 it is fully invested and
  would have stayed fully invested over the last year, so it will track the 10L band account
  until markets fall. The research found it adds almost nothing after 2021; this is a live check.
- **Check.** Replaying the primary account from 2 Nov with the code before and after these changes
  gives identical results, so the primary's code path is unchanged. Replays on today's data do
  not match the live record exactly, because the rolling 500-day window and the signal have moved
  since; the committed, hashed order files remain the record.

## Amendment, 18 Nov 2026 (momentum account)

- **Account.** `paper_mom_10L/` (Rs 10L, `paper/config_mom_10L.json`) runs the same band rule
  (20 names / band 100, minimum trade 1% of NAV), universe, costs and tax as the frozen system, with
  plain 12-1 momentum in place of the council signal: close(t-21) / close(t-252) - 1 on back-adjusted
  closes. No fitted parameters. It starts with orders written after the 18 Nov close (first fills at
  the 19 Nov open) and is run nightly by `run_fleet.py` after the primary, on the same data.
- **Why.** A rebuild of the system on NSE data for 2015 - Nov 2026 (`research/momentum/`) gave the
  council 17.6% a year post-tax (11.5% in 2022-26) and momentum 12-1 24.5% (18.1% in 2022-26), with a
  deeper drawdown for momentum (-45% vs -39%), similar Sharpe (0.95 vs 1.03) and a difference that
  is not significant (t = 1.3). Momentum 12-1 was picked after being the best of five slow signals on
  that data. Recorded here before any live result.
- **Code.** `alpha/paper_trade.py` computes the momentum score only when a config sets
  `"signal": "momentum_12_1"`; every other account, the primary included, takes the unchanged
  council path. Check: the primary's orders after the 17 Nov close, replayed from a fresh state with
  the code before and after this change, are identical.
- **Status.** Exploratory. The Rs 1,00,000 account in `paper/` remains the primary test; its rule,
  signal and conclusion criteria are unchanged. Comparison for this account: `paper_10L` (the frozen
  rule at the same capital), the null control and the Nifty 50, after at least 12 months.

## Amendment, 27 Nov 2026 (two equal-weight composite accounts)

- **Accounts.** `paper_mdeliv_10L/` (`paper/config_mdeliv_10L.json`) and `paper_integ_10L/`
  (`paper/config_integ_10L.json`), Rs 10L each, same band rule (20 names / band 100, minimum trade
  1% of NAV), universe, costs and tax as the frozen system. Scores, with nothing fitted: the equal-weight
  mean of cross-sectional rank z-scores (`alpha.scoring.zrank`, universe mask) of
  - `mdeliv`: 12-1 momentum (close(t-21)/close(t-252) - 1) and the 60-day mean delivery percentage;
  - `integ`: the same two plus low volatility (minus the 250-day standard deviation of daily returns).
  They start with orders written after the 27 Nov close (first fills at the 30 Nov open) and run
  nightly in `run_fleet.py` after the existing accounts, on the same data.
- **Why.** On NSE data rebuilt for Jun 2011 - Nov 2026 (`research/pods/`), Feb 2016 - Nov 2026,
  Rs 10L, post-tax: `integ` 18.1% a year (11.1% in 2022-26), Sharpe 1.23, max drawdown -28%; it
  **failed** its pre-set criteria (`research/pods/SPEC_INT.md`, `ROUND_INT.md`) on 2022-26 return and
  years beating the equal-weight universe. `mdeliv` 27.8% a year (21.7% in 2022-26), Sharpe 1.35, max
  drawdown -33%, the best book in any round, **but it was one of three diagnostic combinations
  examined after the fact**, so its backtest is not evidence. Forward paper trading is the test.
  Recorded here before any live result.
- **Kill review.** Each account is reviewed (and may be stopped by Sunny) if after 6 months it trails
  `paper_mom_10L` by more than 15 points, or its drawdown exceeds -40%. Main comparison after at
  least 12 months: `paper_mom_10L`, `paper_10L`, the null control and the Nifty 50.
- **Code.** `alpha/paper_trade.py` computes these scores only when a config sets
  `"signal": "mom_deliv"` or `"mom_lowvol_deliv"`; every other account takes the unchanged path.
  Check: the primary's and `paper_mom_10L`'s orders and fills for 26 Nov, replayed from their 25 Nov
  state with the new code, are identical to those committed. The live code's 26 Nov picks match
  the backtest's: 20 of 20 for both (one stock appears under its former symbol in the backtest).
- **Status.** Exploratory. The Rs 1,00,000 account in `paper/` remains the primary test; its rule,
  signal and conclusion criteria are unchanged.

## Amendment, 27 Nov 2026 (safeguards against overfitting)

Written before any live result of the 27 Nov accounts.

1. **Frozen means frozen.** No parameter, ingredient, universe or rule of any running account is
   changed. A changed idea is a new account with its own amendment, never an edit.
2. **Trials are counted.** Every backtest is logged in `research/TRIALS.md` before its result is used,
   and any backtest figure quoted in a review states the trial count behind it.
3. **Rules before results.** Every new study writes its rules and pass/fail criteria in a dated
   commit before it is run (as in `research/pods/SPEC*.md`).
4. **Fleet cap and pace.** At most 12 paper accounts at once (11 now). At most one new exploratory
   account per calendar quarter after 27 Nov 2026, so the fleet does not become a search of its own.
5. **No early verdicts.** No account is judged better or worse than another on less than 12 months of
   live data, except the pre-stated kill reviews (6 months).
6. **Live comparison rule.** Because 10 exploratory accounts run side by side, the best of them will look
   good by chance. An exploratory account counts as beating `paper_mom_10L` or the equal-weight
   universe only if its daily excess return has t >= 2.8 (5% one-sided, Bonferroni for 10 accounts). At
   realistic edges this needs two to three years of live data; 12 months will usually be "not yet known".
7. **Real money gate.** No real money follows any account before it passes rule 6 out of sample. Even
   then, it starts as a small satellite next to a broad index core.

## Amendment, 27 Nov 2026 (new primary test: momentum + delivery)

Decided by Sunny on 27 Nov 2026, **before the account's first live trade** (its first orders are written after the
27 Nov close and first filled at the 30 Nov open), so no live result informed it.

- **New primary test:** `paper_mdeliv_10L/` (rules in the amendment "two equal-weight composite accounts" above;
  unchanged). The 12-month clock starts at its first fill on 30 Nov 2026.
- **Why:** the council's blended signal showed no predictive power over the year to Nov 2026 (`research/committee/`),
  its members offset each other, and at Rs 1L the account is handicapped by charges and whole-share rounding. Momentum +
  delivery led every study (`research/pods/`, `research/wicks/RESULTS_BT.md`), passed its unseen Jul 2012 - Dec 2015
  holdout (26.2% a year post-tax, Sharpe 1.71), was rediscovered by the no-hindsight agents, and passed all three
  pre-set stress tests (`research/stress/RESULTS.md`: 50 of 50 random halves, 100% of 36-month windows, costs x3).
  Caveats: trial count (`research/TRIALS.md`), and the delivery idea is partly hindsight.
- **The council account `paper/` keeps running unchanged as a comparison.** It stays first in `run_fleet.py` because it
  downloads the day's data.
- **Verdicts, fixed now from the stress-test ranges** (benchmark: Nifty 500 price index over the same dates; also the
  null control `paper_null_10L`), post-tax:
  - *At 6 months:* **broken** if the drawdown is worse than -40% or it trails the Nifty 500 by more than 20 points.
  - *At 12 months:* **working** if ahead of the Nifty 500 with max drawdown better than -35%; **unclear but normal** if
    behind by up to 25 points (the rule trailed the equal-weight universe in 15% of past 12-month windows, by up to 25
    points), in which case it continues; **broken** if behind by more than 25 points, or more than 15 points behind the
    null control.
  - *At 24 months:* trailing the Nifty 500 is a serious warning (it trailed the equal-weight universe in only 1.3% of
    past 24-month windows); trailing by more than 10 points counts as broken.
  - **Broken** means: stop and review with Sunny; no rule is changed in place (safeguard 1), and real money stays out.
  - "Working" at 12 months is still not proof (safeguard 6 needs t >= 2.8 against the comparisons), but it allows
    discussing a small real-money satellite next to an index core (safeguard 7).

## Fix, 27 Nov 2026 (data): weekend special sessions are no longer read as corporate actions

`alpha/bhav_panel.py` now ignores sub-split "corporate-action factors" on days when more than 30% of stocks show one
(`ISSUES.md` #1). Those days follow weekend special sessions (Budget days, Muhurat trading, exchange test sessions) that
the weekday download misses; 18 such days in 2011-2026 (56-89% of stocks), against a normal day's 99th percentile of
5%. Without the fix, the live trader would rescale share counts of holdings on such days (it happened on 9 Nov 2026;
rounding left every count unchanged) and the back-adjusted prices drop the missed session's move.

Check: replaying 26 Nov from each account's 25 Nov state, the orders, fills and NAV are identical with and without the fix
for `paper/`, `paper_10L`, `paper_hi_10L`, `paper_lo_10L`, `paper_null_10L`, `paper_timed_10L` and `paper_mom_10L`. The two
daily-rule accounts (`paper_daily_10L`, `paper_daily_1L`), which re-pick their top 20 every day with no band, would have
swapped one stock: the restored 9 Nov move shifts momentum scores slightly. No live share count was ever changed, and
no rule, parameter or signal changed. The new primary has not traded yet.

## Code, 27 Nov 2026: ETF support for a future multi-asset account (not yet active)

`alpha/paper_trade.py` gains a `"rule": "multi"` path and `alpha/etf_prices.py` (ETF prices from the day's bhavcopy, ETF
costs: STT 0.001%, half-spread 0.05%), for `paper/config_multi_10L.json` (mix B, `research/multiasset/SPEC_B.md`).
**The account is not in `paper/fleet.json`**; under the 27 Nov safeguards it can be added by a dated amendment from
Jan 2027. Check: replaying 26 Nov from each account's 25 Nov state, all nine existing accounts' orders, fills and NAV are
identical with the previous and the new engine. A dry run of the multi account (25-26 Nov, scratch copy) bought 20 stocks at
2% each, GOLDBEES 20% and MON100 10%, leaving 32% cash. Before activation, `review_session.py` must also learn to value ETF
holdings.

## Decision, 27 Nov 2026 (Sunny): paper trading only; monthly review

Safeguard 7 stays as written: no real money before an account passes the live bar (t >= 2.8), which on the backtest's
own variability would take about 7 years if the live edge matched the backtest and decades if it were half as large.
**Paper trading continues until Sunny decides otherwise.** A monthly review (`monthly_review.py`, scheduled on the 1st of
each month) checks that every account ran every trading day, the integrity check, results against the pre-set verdicts,
and post-trade learnings, and lists at most three improvement proposals. Proposals are never applied automatically: bug
fixes go through a dated fix entry, new ideas through a new pre-registered account within the 27 Nov safeguards, and
research stays frozen until the 6-month checkpoint.

## Decision, 27 Nov 2026 (Sunny): run horizon to 31 Dec 2028

The fleet keeps paper trading, unchanged, **until 31 Dec 2028** (about 25 months for the primary, which first trades on
30 Nov 2026). Checks continue throughout: the daily run (fleet, integrity check, tests, reviews, post-trade analysis,
committee) and the monthly review. The pre-set checkpoints still apply on their dates: 6 months (late May 2027, broken
checks only), 12 months (late Nov 2027) and 24 months (late Nov 2028). The monthly review of December 2028 (run on
1 Jan 2029) also writes the **final report** for the whole period: every account against its pre-set verdicts, the
primary against the Nifty 50 / Nifty 500 and the backtest's normal ranges, what the post-trade ledger learned, and what
was and was not shown at the t >= 2.8 bar. After that, what happens next is Sunny's decision; nothing changes
automatically, and real money stays off the table unless he decides otherwise.
