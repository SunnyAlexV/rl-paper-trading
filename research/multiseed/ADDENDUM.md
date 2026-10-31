# Addendum, 31 Oct 2026: multi-seed check of the frozen system

Written after the pre-registration commit (094ea60) and before the first paper-trading day.
It reports the check promised under "Known limitations". **Nothing in the frozen system changes**:
`paper/config.json`, the signal file and the trading code are untouched. This is context for
reading the forward result.

## What was done

The MCTS search that produced the price-volume and delivery researchers' formula pools was rerun
with four more seeds (1-4). Each seed also got a luck twin: the same search on a market whose
20-day targets were shuffled across stocks each day, so that any edge it found must be luck. A
council was then rebuilt for every seed, exactly as the frozen one was built: the union of the
pools, with least-squares weights fitted on 2013-19. Rebuilding seed 0 reproduces the frozen file
exactly (17 members, identical weights). Every council was then traded with the frozen band rule in
the exact engine: Rs 1,00,000, all costs and taxes, 1% minimum trade size.

Code: `council_seeds.py` (`build`, `backtest`) and `deflated.py`, run from the research repo root.

## Researcher level (formulas in pool / IR 2013-19 train / IR 2020-21 validation)

IR is the after-cost information ratio of the top-20 portfolio against the equal-weight universe.

| | s0 (frozen) | s1 | s2 | s3 | s4 |
|---|---|---|---|---|---|
| Price-volume, real | 5 / 1.01 / 0.79 | 4 / 0.72 / 0.94 | 5 / 1.08 / 0.21 | 5 / 0.97 / 1.76 | 5 / 1.09 / 1.24 |
| Price-volume, null | 1 / 0.37 / 0.21 | 2 / 0.25 / -0.37 | 2 / 0.14 / -0.69 | 2 / 0.13 / -1.24 | 1 / 0.05 / -1.34 |
| Delivery, real | 5 / 1.02 / -0.46 | 1 / 0.64 / 0.12 | 1 / 0.52 / 0.40 | 2 / 1.17 / -0.46 | 2 / 0.71 / 0.31 |
| Delivery, null | 2 / 0.34 / -1.06 | 1 / 0.15 / -0.60 | 2 / 0.17 / 0.08 | 2 / 0.19 / -0.15 | 3 / 0.26 / -1.52 |

- **Price-volume is robust.** Every real seed beats every null seed in training. In validation the
  real seeds average 0.99 and the nulls -0.69.
- **Delivery is fragile.** The frozen seed's five-formula pool has the worst real validation IR
  (-0.46). Other seeds keep only one or two formulas. About a third of the frozen council comes from
  this pool.

## Council level, band rule, post-tax (Sharpe; CAGR in brackets)

| Seed | Real 2013-19 | Real 2022-26 | Real full | Null 2013-19 | Null 2022-26 | Null full |
|---|---|---|---|---|---|---|
| 0 (frozen) | 1.27 (21.3%) | 0.74 (10.9%) | 1.22 (21.7%) | 0.40 (6.1%) | 0.51 (9.7%) | 0.50 (9.3%) |
| 1 | 1.06 (16.1%) | 0.73 (10.1%) | 1.14 (18.6%) | -0.66 | -3.69 | -1.28 |
| 2 | 1.02 (16.3%) | 0.54 (7.7%) | 1.03 (17.5%) | -0.86 | -3.27 | -2.08 |
| 3 | 1.06 (16.5%) | 0.59 (8.5%) | 1.10 (18.5%) | 0.40 (6.0%) | 0.59 (9.9%) | 0.59 (10.5%) |
| 4 | 0.86 (13.5%) | 0.68 (10.7%) | 1.01 (18.1%) | 0.03 (-2.3%) | 0.41 (6.5%) | 0.26 (3.4%) |

- Over the full period every real council beats every null council. The frozen seed is the best
  of the five real seeds, but it is not an outlier: the others give a Sharpe of 1.01-1.14.
- **Null seeds 1 and 2 are degenerate.** Their signals churn 15-25 times a year. The fixed Rs 15.34
  DP charge per scrip per sell day then grows as a share of a shrinking account until the account
  is ruined. That is the cost model working as it should, but it makes them a weak benchmark. The
  fair nulls are seeds 0, 3 and 4.
- **In 2022-26 the edge over the fair nulls is small:** Sharpe 0.54-0.74 for the real councils
  against 0.41-0.59 for the fair nulls, and CAGR 7.7-10.9% against 6.5-9.9%.
- Null caveat: the derivatives and LLM pools exist as single runs. Every seed's null council
  therefore reuses the seed-0 null versions of them, re-weighted on that seed's own shuffle.

## Deflated Sharpe ratio (Bailey & Lopez de Prado), frozen council

The deflated Sharpe ratio is the probability that the true Sharpe is above zero, after allowing
for picking the best of N strategy trials whose Sharpes spread with standard deviation sd
(annualised). The Sharpe spread across the five seeds alone is 0.085, which understates the spread
across the genuinely different systems tried in this project. Across the 31 strategy
backtests from stages 5-6, the 24 non-degenerate ones (Sharpe above -1) have sd = 0.42, so
sd = 0.3-0.5 and N = 30-100 are realistic.

| | sd 0.085 | sd 0.25 | sd 0.5 | sd 0.75 |
|---|---|---|---|---|
| Full 2013-26, N = 50 | 1.00 | 0.99 | 0.61 | 0.04 |
| Full 2013-26, N = 100 | 1.00 | 0.98 | 0.44 | 0.01 |
| 2022-26, N = 50 | 0.89 | 0.66 | 0.21 | 0.02 |
| 2022-26, N = 100 | 0.88 | 0.61 | 0.14 | 0.01 |

Under plausible assumptions the full-period Sharpe of 1.22 is more likely than not to be real.
The 2022-26 Sharpe of 0.74 does not survive deflation. The full grid is in
`council_deflated_sharpe_grid.csv`.

## What this means for the forward test

The search reliably finds a price-volume edge, and the frozen seed is representative of the
search. Whether that edge still exists is exactly what the backtest cannot settle: since 2022 it is
close to luck level. The pre-registered 12-month forward test is the deciding evidence. A forward
Sharpe of roughly 0.5 or below would be consistent with the edge having gone.
