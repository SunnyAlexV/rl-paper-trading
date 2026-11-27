# Agent v2 (diagnostic batter): results (27 Nov 2026)

Rules: `SPEC.md` (committed before any code). Run once. Jan 2015 - 26 Nov 2026, Rs 10L, walk-forward.

## Stage 1 (spread + impact only) - the pre-registered test

| Book | CAGR | 2022-26 | Sharpe | Excess over core (t) | Years beating core | Swings/yr | Months with empty satellite |
|---|---|---|---|---|---|---|---|
| Core only (equal-weight universe) | 11.2% | 12.9% | 0.70 | | | | |
| **Medium bar z=3 (judged)** | 10.8% | 13.3% | 0.67 | -0.3%/yr (-0.3) | 2/12 | 10.9 | 60% |
| Strict bar z=4 | 11.2% | 12.9% | 0.70 | never swung | | 0 | 100% |
| Lenient bar z=2 | 13.3% | 16.7% | 0.78 | +2.0%/yr (1.4) | 8/12 | 23.4 | 14% |
| No bar z=0 (control) | 15.7% | 18.7% | 0.91 | +4.2%/yr (2.5) | 8/12 | 34.8 | 0% |

**Verdict: Fail.** The medium bar fails all five criteria: below the core on Sharpe; no excess (t = -0.3);
beat the core in only 2 of 12 years; below the no-bar control (so selectivity did not help);
the strict bar never traded.

**The hypothesis was backwards here.** The pickier the agent, the worse it did. Demanding very high
confidence (with the 12-fold overlap correction and 5,600 setups to guard against) let almost nothing through,
and what did get through came late, after the evidence had piled up. The best results came from swinging every
month at the best-looking setups with a positive record in both halves of their history.

## What the agent found on its own

Most-used setups (months in the zone), with nothing pre-loaded:
- no bar: near 250-day high + low recent volume; near 250-day high + small size; 20-day and 12-month return both
  high; recent return high + delivery trend rising;
- lenient: near 250-day high + small size; **12-month return high + near 250-day high**; **12-month return high +
  delivery share high** (the momentum + delivery idea now in a live paper account), 12-month return high + small size.

So a no-hindsight agent independently rediscovered momentum, the "near the 52-week high" effect, and
momentum + delivery.

## Stage 2 diagnostic (all fees and tax; not part of the pass/fail)

| Book | CAGR | Sharpe | Excess over core (t) |
|---|---|---|---|
| Core only | 8.3% | 0.55 | |
| No bar | 11.0% | 0.67 | +2.6%/yr (1.5) |
| Lenient | 9.2% | 0.58 | +0.9%/yr (0.6) |
| Medium | 7.6% | 0.50 | -0.6%/yr (-0.7) |

The core is penalised at Stage 2 because rebalancing ~500 stocks monthly pays a DP charge on every trimmed
stock; a real core would be one index fund or ETF. All books share that core, so the comparison
between them is still fair.

The no-bar version was a control, not the pre-declared candidate, so its result is a hypothesis, not evidence.
