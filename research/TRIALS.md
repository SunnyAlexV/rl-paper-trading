# Trials ledger: every strategy test, so the multiple-testing burden stays visible

Rule: every backtest run on the rebuilt history is logged here before its result is used anywhere.
The more strategies tried, the more likely the best one looks good by luck; this count is what any
"best result" must be discounted for.

| Date | Study | Strategies tested | Selected / reported |
|---|---|---|---|
| Oct 2026 | Research council (`results/`) | thousands of formulas searched by MCTS and an LLM; 17 kept | frozen council (primary) |
| 18 Nov 2026 | `research/momentum/` | 5 slow signals | 12-1 momentum (exploratory account) |
| 26 Nov 2026 | Signal health (`research/committee/`) | 4 researchers + council + momentum x 3 horizons x 3 size buckets x F&O split | diagnostics only |
| 26 Nov 2026 | Pods round 1 (`research/pods/ROUND1.md`) | 3 pods x 9 variants + cost stress | trend passed |
| 27 Nov 2026 | Long-short (`ROUND_LS.md`) | 3 books, 18 variants + 2 stress | none passed |
| 27 Nov 2026 | Integrated (`ROUND_INT.md`) | 1 composite x 9 variants + stress + 3 diagnostic pairs | integrated failed; momentum+delivery chosen after the fact |

**Count of strategy-level trials in the pods work: about 45 backtests, about 10 distinct ideas.**
The delivery ingredient also inherits the council's search, since delivery formulas were nominated
by that search.

## Deflated Sharpe check (27 Nov 2026)

Probability that the backtest Sharpe reflects a real edge rather than the luck of picking the best
of N trials (Bailey & Lopez de Prado deflated Sharpe ratio; trial-Sharpe dispersion estimated from the 43
backtests of the pods work; Feb 2016 - Nov 2026, post-tax daily returns):

| Book | Sharpe | N = 10 | N = 30 | N = 100 | N = 1000 |
|---|---|---|---|---|---|
| Momentum + delivery | 1.35 | 0.99 | 0.95 | 0.86 | 0.58 |
| Integrated (3 ingredients) | 1.23 | 0.97 | 0.90 | 0.77 | 0.43 |
| Council (frozen) | 1.11 | 0.94 | 0.82 | 0.64 | 0.29 |
| Trend pod | 0.92 | 0.83 | 0.63 | 0.40 | 0.12 |

Excess return over the equal-weight universe: momentum + delivery +11.3% a year (t = 3.4), trend
+8.4% (t = 2.0), council +2.8% (t = 0.9), integrated +2.2% (t = 0.6). Momentum + delivery's excess is
concentrated: +41 points in 2017 and +34 in 2024; -2 to -6 in 2022 and 2025.

Reading: if the honest trial count is tens, momentum + delivery is probably real; if it includes
the council's search (thousands), it is close to a coin flip. Forward paper trading settles it.

| 27 Nov 2026 | Walk-forward discovery agent (`research/agent_wf/`) | 1 agent design x 3 seeds + 2 controls; inside each run the agent itself searches ~4,600 formulas walk-forward | rules in `research/agent_wf/SPEC.md`, run once |
| 27 Nov 2026 | Agent v2, diagnostic batter (`research/agent_v2/`) | 1 design x 3 pre-declared bars + no-bar control; the agent tracks 5,600 setups walk-forward | rules in `research/agent_v2/SPEC.md`, medium bar judged, run once |
| 27 Nov 2026 | Agent v2 Stage 2 diagnostic | same 4 books + core with all fees and tax | diagnostic only |
| 27 Nov 2026 | Candle wick diagnostic (`research/wicks/`) | 4 wick measures (daily and 20-day mean of upper wick %, lower wick %, lower minus upper) x 3 horizons x size buckets; rank IC only | diagnostic, Sunny's hypothesis: lower vs upper wick share |
| 27 Nov 2026 | Wick backtest + mom+deliv holdout (`research/wicks/SPEC_BT.md`) | 3 scores x 3 k + 2 comparators, Stage 1 and 2, Jul 2012 - Nov 2026 | rules fixed before run |
| 27 Nov 2026 | Wick long-short (`research/wicks/SPEC_LS.md`) | 1 book + stress + long-only comparator, Jul 2012 - Nov 2026 | rules fixed before run |
| 27 Nov 2026 | Upper wick as a sell signal (`research/wicks/SPEC_EXIT.md`) | 2 books x 3 thresholds + 3 comparators, Stage 1 and 2 | rules fixed before run |
