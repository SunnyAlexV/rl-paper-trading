# Walk-forward discovery agent: results (27 Nov 2026)

Rules: `SPEC.md` (committed before the run). Run once, no re-tuning. Blind trading Jan 2014 - 26 Nov 2026,
Rs 10L, post-tax. Each agent searched ~4,600 formulas walk-forward (1,500 random + 60 mutations a quarter).

| | Sharpe | CAGR | 2022-26 CAGR | Max DD | Excess over EW (t) | Years beating EW |
|---|---|---|---|---|---|---|
| Agent seed 1 | 0.64 | 10.5% | 10.1% | -47% | -4.1%/yr (-1.6) | 5/13 |
| Agent seed 2 | 0.59 | 9.4% | 7.8% | -41% | -5.2%/yr (-2.1) | 4/13 |
| Agent seed 3 | 0.40 | 5.7% | 7.2% | -50% | -8.5%/yr (-3.4) | 3/13 |
| No-learning (median) | 0.57 | 8.8% | 9.2% | | | |
| No-skill control (median) | 0.13 | 0.5% | 0.8% | | | |
| Equal-weight universe | 0.86 | 15.0% | 13.0% | -48% | | |
| Nifty 50 (price) | 0.78 | 11.6% | 8.2% | -38% | | |

**Verdict: Fail** on every criterion (median seed). Learning from its own outcomes (Hedge) beat the
no-learning version in 2 of 3 seeds, by tiny margins (Sharpe +0.01, +0.02; -0.08 in seed 3): no real effect.

**What it shows.**
- Discovery is not nothing: every agent beat random formulas by a wide margin (Sharpe ~0.6 vs ~0.1).
  But after costs and tax none beat simply holding the average universe stock.
- **All three agents, without being told, converged on delivery data**: 73-81% of selected formulas in
  seeds 1 and 3 use deliv_val or deliv_pct, and 74% of seed 2's. That independently supports delivery as a real
  pattern in Indian stocks.
- The agents could not find 12-month momentum, the strongest signal in the hindsight studies, because the
  repo's grammar only has windows up to 60 days (nesting reaches ~120). This limit was fixed before the
  run; widening it would be a new trial.
- Compared with the hindsight backtests (council 18%, momentum + delivery 28% a year), an agent with no
  hindsight made 6-10% a year. That gap is a measure of how much hindsight flatters backtests.

## Diagnostic: before vs after costs and tax (27 Nov 2026)

Same books with all costs (STT, charges, spread, impact) and tax set to zero (`gross_vs_net.csv`;
agent = no-learning version rebuilt from the logged quarterly selections, net figures match the run).
Jan 2014 - Nov 2026:

| Book | Gross CAGR / Sharpe | Net CAGR / Sharpe | Lost to costs + tax |
|---|---|---|---|
| Equal-weight universe | 15.8% / 0.89 | 15.0% / 0.86 | 0.8 pts |
| Momentum + delivery | 32.8% / 1.63 | 28.2% / 1.40 | 4.6 pts |
| Trend (momentum) | 25.8% / 1.05 | 21.2% / 0.89 | 4.6 pts |
| Council (frozen) | 28.6% / 1.69 | 20.3% / 1.24 | 8.3 pts |
| Agent seed 1 | 24.5% / 1.31 | 10.3% / 0.63 | 14.2 pts |
| Agent seed 2 | 20.1% / 1.15 | 8.8% / 0.57 | 11.2 pts |
| Agent seed 3 | 13.4% / 0.77 | 7.4% / 0.47 | 6.0 pts |

Before costs, two of three no-hindsight agents beat the equal-weight universe clearly. Their patterns
were real but short-lived (fast turnover), so costs and short-term tax took most of the edge.
Slow signals (momentum, momentum + delivery) keep most of theirs.
