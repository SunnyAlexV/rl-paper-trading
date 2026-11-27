# Diagnostics on stops (27 Nov 2026)

**Price level vs volatility** (universe stocks, every 60th trading day 2013-2026; daily volatility = 20-day std):

| Share price | Median daily volatility | 10th-90th percentile |
|---|---|---|
| under Rs 100 | 2.65% | 1.57-4.60% |
| Rs 100-500 | 2.31% | 1.38-3.97% |
| Rs 500-1,000 | 2.04% | 1.22-3.52% |
| Rs 1,000-3,000 | 1.91% | 1.16-3.35% |
| Rs 3,000-10,000 | 1.80% | 1.08-3.24% |
| over Rs 10,000 | 1.70% | 1.06-2.97% |

Cheaper shares are somewhat more volatile on average (rank correlation -0.28), but the ranges overlap heavily, so
stop distances should come from each stock's own percentage volatility (as in `SPEC_CLIMB.md`), not from its price.

**What stopped stocks did next** (331 stops, climbing rule m = 2, reinvest; returns from the next open):

| After | Stopped stock, mean | Average universe stock | Back above the exit price | Fell a further 10%+ |
|---|---|---|---|---|
| 21 days | +2.7% | +1.9% | 61% | 13% |
| 63 days | +6.8% | +5.9% | 62% | 16% |
| 126 days | +12.9% | +10.7% | 67% | 18% |

Most stops sold a dip that recovered: about 6 in 10 stopped stocks were back above the exit price within a month, and
on average they did slightly better than the average stock afterwards. About 1 in 7 kept falling (the "leak" the stop
plugged). Hence the cost of stops in this strategy: selling recoveries outweighed the falls avoided.
