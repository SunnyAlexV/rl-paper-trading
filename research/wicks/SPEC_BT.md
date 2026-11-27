# Wick backtest and momentum + delivery holdout: rules (written 27 Nov 2026, BEFORE the run; run once)

Same engine and rules as every pods test: Rs 10L, long only, band rule (hold k, sell when out of the
top 5k), decide at the close, fill at the next open, max 7.5% per stock, min trade 1% of NAV.
**Period: 2 Jul 2012 (first day with a universe) - 26 Nov 2026.** Reported at Stage 1 (spread + impact only)
and Stage 2 (all fees and post-tax).

Scores (equal-weight mean of rank z-scores, nothing fitted):
- **wick** = 20-day mean of the lower-wick share, (min(open, close) - low) / (high - low);
- **mom + deliv** = 12-1 momentum and 60-day mean delivery % (the live `paper_mdeliv_10L` rule);
- **mom + deliv + wick** = all three.
Comparators: equal-weight universe (monthly), momentum 12-1 alone. Variants k = 15 / 20 / 25.

Criteria:
- **A. Wick as its own pod:** at k = 20, Sharpe above the equal-weight universe at Stage 1 and at Stage 2 over the
  whole period, and Stage 1 CAGR above it in 2022-26; the median of the three k variants also beats it on Stage 1 Sharpe.
- **B. Wick adds to momentum + delivery:** Stage 2 Sharpe of mom + deliv + wick above mom + deliv's in at least
  2 of the 3 k variants.
- **C. Holdout for momentum + delivery** (2 Jul 2012 - 31 Dec 2015, never seen when its rules were chosen):
  at k = 20, Stage 2 CAGR and Sharpe above the equal-weight universe's.
