# Two-stage evaluation (adopted 27 Nov 2026, at Sunny's request)

**Stage 1: is there a real pattern?** Research backtests count only the cost of execution itself:
the bid-ask spread and market impact (the price actually obtained). No brokerage, STT, exchange
charges, GST, stamp duty, DP charges or tax. Every Stage 1 result also reports **turnover**
(times the portfolio is traded per year), because Stage 2 costs scale with it.

**Stage 2: can it be traded profitably?** Adds every fee and tax (the repo's full engine). A strategy
reaches Stage 2 only after passing Stage 1, and only Stage 2 decides a live paper account.

Unchanged: every running paper account, the primary included, keeps its pre-registered full-cost
(Stage 2) accounting. Pass/fail criteria already committed for earlier studies keep their stated basis.

## Stage 1 vs Stage 2, Jan 2014 - Nov 2026 (Rs 10L, `research/agent_wf/stage1.csv`, `gross_vs_net.csv`)

| Book | Turnover / yr | No costs at all | **Stage 1** (spread + impact) | Stage 2 (everything) |
|---|---|---|---|---|
| Equal-weight universe | 0.4x | 15.8% / 0.89 | **15.7% / 0.89** | 15.0% / 0.86 |
| Momentum + delivery | 1.8x | 32.8% / 1.63 | **31.6% / 1.58** | 28.2% / 1.40 |
| Trend (momentum) | 2.0x | 25.8% / 1.05 | **25.3% / 1.03** | 21.2% / 0.89 |
| Council (frozen) | 7.4x | 28.6% / 1.69 | **26.0% / 1.56** | 20.3% / 1.24 |
| Agent seed 1 | 28.0x | 24.5% / 1.31 | **18.3% / 1.03** | 10.3% / 0.63 |
| Agent seed 2 | 20.6x | 20.1% / 1.15 | **15.5% / 0.93** | 8.8% / 0.57 |
| Agent seed 3 | 7.8x | 13.4% / 0.77 | **11.1% / 0.66** | 7.4% / 0.47 |

(CAGR / Sharpe. Agents: no-learning version rebuilt from the logged quarterly selections.)
