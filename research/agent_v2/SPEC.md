# Agent v2, "the diagnostic batter": rules (written 27 Nov 2026, BEFORE any code or run; run once)

Research only. Design from the 26-27 Nov discussion with Sunny:
- **Doctor:** read symptoms together, not one at a time; the same symptom means different things in
  different company and in different market conditions.
- **Batter:** swing only at pitches it has proven it hits well; let everything else go by (no
  called strikes; the money waits in a core basket).
- **Learning:** the zone grows where evidence accumulates and shrinks where a pattern stops working.
  It learns from every pitch (every stock, traded or not), never from the future.

Nothing here (momentum, delivery, low volatility, the council) is given to the agent as "known to
work". The symptoms are generic readings of the available data; which combinations work is learned.

## 1. Symptoms (20 per stock per day; all backward-looking)

Each is turned into a cross-sectional state each day over the universe mask: **high** (top third),
**low** (bottom third) or neither. Missing (e.g. F&O readings for non-F&O stocks) = neither.

| # | Symptom | # | Symptom |
|---|---|---|---|
| 1 | 5-day return | 11 | size: log 60-day median traded value |
| 2 | 20-day return | 12 | delivery share: 20-day mean of deliv_pct |
| 3 | 60-day return | 13 | delivery trend: 20-day mean minus 120-day mean of deliv_pct |
| 4 | 12-month return skipping the last month | 14 | delivery value surge: 5-day / 60-day mean of deliv_val |
| 5 | closeness to the 250-day high (close / max) | 15 | futures open-interest change over 20 days (F&O only) |
| 6 | height above the 60-day low (close / min) | 16 | futures basis, 5-day mean (F&O only) |
| 7 | 20-day volatility | 17 | basis change: 5-day minus 60-day mean (F&O only) |
| 8 | 250-day volatility | 18 | put/call open-interest ratio, 20-day mean (F&O only) |
| 9 | volatility shift: 20-day / 250-day | 19 | price-delivery divergence: rank of #2 minus rank of #13 |
| 10 | volume surge: 5-day / 60-day mean volume | 20 | hollow volume: rank of #10 minus rank of #14 |

**Market context (patient history), the same for all stocks on a day**, each high/low against
its own trailing 750 trading days (point in time): market trend (equal-weight universe 60-day return),
breadth (share of universe stocks above their 200-day average), market stress (equal-weight universe
20-day volatility).

## 2. Diagnoses (setups)

A setup is one symptom state, or two symptom states together (each high or low), optionally
restricted to one market-context state: (20 x 2 singles + 190 x 4 pairs) x (any context + 6 context
states) = **5,600 setups**. No setup uses more than 2 symptoms plus 1 context reading.

## 3. Outcome of every pitch (Stage 1)

For every stock on every 5th trading day: the return from the next open to the open 60 trading
days later, **minus the universe average** over the same days, **minus a round-trip execution cost**
(2 x (half-spread + square-root impact) for a Rs 50,000 position, from the repo's cost model on that
day). No fees, no tax (Stage 1, `research/STAGES.md`). An outcome may be used only after it has fully
happened (61 trading days later).

## 4. Track record and the zone (updated at every month-end)

For each setup, over all matured sample days on which at least 3 stocks were in it:
- daily mean outcome of its stocks; weights fade with age (half-life 3 years);
- edge = weighted mean; uncertainty = weighted standard deviation / sqrt(n_eff), where n_eff is the
  effective number of sample days divided by 12 (60-day outcomes sampled every 5 days overlap 12-fold);
- **cautious edge** = edge - z x uncertainty; **upper edge** = edge + z x uncertainty;
- a setup is **in the zone** if cautious edge > 0, n_eff >= 5, and its mean outcome is positive in both
  the older and the newer half of its history; it is a **warning** if upper edge < 0 on the same terms.

## 5. Swing decision (every month-end)

For each stock: **conviction = the largest cautious edge among zone setups it matches + the most
negative upper edge among warning setups it matches** (0 where none). Best confirmed diagnosis minus
strongest contraindication.
- **Swing:** stocks with conviction > 0, best first, at most 10 held.
  Size proportional to conviction, at most 5% each, satellite at most 50% of NAV.
- **Hold** until conviction computed with z - 1 is <= 0 (confidence lost even at a lower bar).
- **Everything else stays in the core:** equal weight in every universe stock, rebalanced monthly,
  funded down by whatever the satellite holds.

## 6. Bars (pre-declared, all reported; the medium bar is the one judged)

lenient z = 2, **medium z = 3**, strict z = 4. With 5,600 setups, z = 3 lets through roughly 8 false
setups by chance, and z = 4 lets through fewer than 1. Control: **no bar** (z = 0).

## 7. Test

Walk forward, first decision at the end of Dec 2014, trading Jan 2015 - 26 Nov 2026, Rs 10L, the repo's
engine (decide at the close, fill at the next open), **Stage 1 costs only** (spread + impact; no fees,
no tax). Comparators: the core alone; the agent with no bar.

## 8. Pass/fail (Stage 1, Jan 2015 - Nov 2026, medium bar)

1. Sharpe and CAGR above the core's, over the whole period and in 2022-26.
2. Daily excess return over the core with t >= 2.0.
3. Beats the core in at least 7 of 12 calendar years.
4. Selectivity helps: Sharpe above the no-bar agent's.
5. Robustness: lenient and strict bars also beat the core on Sharpe.

Passing all five sends it to Stage 2 (all fees and tax) with these rules unchanged. Reported in any
case: swings per year, turnover, share of months with an empty satellite, and the setups most often
in the zone, in plain words.
