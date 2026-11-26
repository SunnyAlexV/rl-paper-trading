# Walk-forward discovery agent: rules (written 27 Nov 2026, BEFORE the run; run once, no re-tuning)

Research only. An agent starts in 2014 knowing nothing about which patterns work. At every step it
may use only data before that day. It searches for patterns, tests them on its own recent past,
trades the survivors, learns from how its own predictions turned out, and moves forward to Nov 2026.

**What is fixed by the designer (unavoidable).** The raw inputs, the formula grammar, the search
budget, the tests and the trading rule below. They are the repo's existing defaults, chosen before
the run. No ingredient (momentum, delivery, low volatility, the council) is given to the agent.

## Inputs and grammar

All 14 raw daily fields in `CouncilPanel`: open, high, low, close, volume, vwap, ret, value,
deliv_pct, deliv_val, basis, oi_chg, pcr, fut_oi_val. The repo's grammar (`alpha/grammar.py`):
neg, abs, slog, sign; ts_mean/std/delta/delay/rank/max/min/pct and ts_corr over 5-60 days;
add, sub, mul, div. Formulas are random legal sequences of 2-8 tokens.

## Prediction target and score

Target: return from the next open to the open 20 trading days later (`P.targets[20]`).
Skill of a formula = daily rank correlation (IC) between its cross-sectional rank and the
target, over the universe mask, sampled every 5th trading day. **A day's IC is usable only after
its target has fully happened (21 trading days later).** Formulas are evaluated with
backward-looking operators only.

## Each quarter (first trading day of Jan, Apr, Jul, Oct; first step Jan 2014)

1. **Search.** Pool = 1,500 random formulas generated once from the grammar with no data (seeded),
   plus 60 new formulas per quarter: mutations (one token changed, or a subtree replaced) of the
   current top 20.
2. **Discover** on all usable history except the last 126 trading days: keep formulas whose mean IC
   has |t| >= 3 (t computed on non-overlapping 20-day blocks). The sign is taken from this window.
3. **Test** on the last 126 usable trading days: keep only those whose signed mean IC there is > 0.
4. **Select** up to 10, best discovery t first, skipping any whose IC series correlates > 0.7 with
   one already selected. If none survive, hold the previous quarter's set.
5. **Score** = weighted mean of the selected formulas' signed rank z-scores.

## Learning from its own outcomes (every week)

Each selected formula's weight is updated by multiplicative weights (Hedge):
w <- w x exp(2 x IC), using its most recent matured IC (predictions made 21+ trading days ago),
then normalised. New formulas start at the average weight. Nothing else is fitted.

## Trading

Same as every pods test: Rs 10L, long only, band rule hold 20 / sell when out of the top 100, decide at
the close and fill at the next open, max 7.5% per stock, min trade 1%, the repo's cost and tax engine.
Blind trading period: 1 Jan 2014 - 26 Nov 2026.

## Controls (same machinery, same period)

- **No-learning:** same agent, equal weights (no Hedge).
- **No-skill:** each quarter, 10 formulas picked at random from the pool, no discovery or test.
- Equal-weight universe and Nifty 50.

## Seeds

Three seeds (different random pools): 1, 2, 3. Reported: each seed and the median.

## Pass/fail (post-tax, Jan 2014 - Nov 2026, median of the three seeds)

1. Sharpe above the equal-weight universe's and the no-skill control's; CAGR in 2022-26 above the
   equal-weight universe's.
2. Daily excess return over the equal-weight universe with t >= 2.0.
3. Beats the equal-weight universe in at least 7 of 13 calendar years.
4. Max drawdown no worse than -45%.
Learning helps only if the agent beats its own no-learning version on Sharpe in at least 2 of 3 seeds.
