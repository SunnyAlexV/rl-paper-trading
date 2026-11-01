# Timing layer on top of the band rule (1 Nov 2026), research only, not traded

**Question.** Can an RL agent that sets only the exposure level (0, 50% or 100% of NAV invested,
with idle cash in a 5.5% liquid fund taxed at slab rate) improve the frozen band rule?

**Setup.** The agent is an 8-parameter policy over 7 market-state features, trained with evolution
strategies on a block-bootstrapped proxy. Training covers 2013-19; the agent is selected on 2020-21
and tested on 2022-26, which stayed untouched until the end. Every policy is then run in the exact
engine. The controls are an always-invested rule, a 200-day trend filter, and the same agent
trained on features shuffled in time. Code: `timing.py`, run from the research repo root.

**Results.** Sharpe after costs and tax, `timing_eval.csv`, k = 20 names, band 100.

| | 2013-19 | 2020-21 | 2022-26 | Max drawdown |
|---|---|---|---|---|
| Always invested | 1.24 | 1.82 | 0.57 | -35% |
| Timing agent, 3 seeds | 0.97-1.14 | 2.78-2.86 | 0.58-0.64 | -24% to -26% |
| Agent on shuffled features | 1.13-1.30 | 1.82-1.88 | 0.57-0.58 | -35% to -37% |
| Trend filter | 1.25 | 2.43 | 0.72 | -22% |

The agent's gain comes from the COVID crash, the single event in its selection window. In
2022-26 it adds almost nothing. In the exact engine it also loses in-sample, because cutting
exposure sells winners and realises tax.

**Is the trend filter better?** `path_noise.py` checks this across 9 rule settings (15, 20 or 25
names; band 60, 100 or 150). Its first run had a weighting bug; it was fixed and rerun.

- Mean change in Sharpe from the filter: -0.13 in 2013-19, -0.02 in 2022-26, -0.01 overall.
  It improves Sharpe in only 3 of the 9 settings.
- Average max drawdown falls from -33% to -23%, at a cost of about 2.5 points of CAGR a year.

The filter trades return for smaller drawdowns. It does not reliably add risk-adjusted return, and
its strong result at 20/100 is luck of that one setting.

**Conclusion.** Neither the learned timing agent nor the trend filter is added to the system.
