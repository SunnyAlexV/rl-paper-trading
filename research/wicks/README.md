# Candle wicks (Sunny's hypothesis, 27 Nov 2026): diagnostic, Stage 1, no costs

Upper wick % = (high - max(open, close)) / (high - low); lower wick % = (min(open, close) - low) / (high - low).
Rank IC (Spearman, universe mask) vs the return from the next open over 5 / 20 / 60 days, non-overlapping
samples, Jul 2012 - Nov 2026. 54 combinations tested (`wicks.py`, `wick_ic.csv`).

**Lower wicks matter; upper wicks much less.**

| Measure | 5 days | 20 days | 60 days | Both halves (2012-19 / 2019-26), 20 days |
|---|---|---|---|---|
| Lower wick %, 20-day mean | IC +0.024 (t 5.9) | +0.031 (t 4.2) | +0.037 (t 2.7) | +0.040 / +0.022 |
| Upper wick %, 20-day mean | -0.011 (t -3.0) | -0.013 (t -1.7) | -0.006 (t -0.5) | -0.009 / -0.016 |
| Lower minus upper, 20-day mean | +0.020 (t 4.8) | +0.025 (t 3.2) | +0.023 (t 1.6) | +0.029 / +0.022 |

Stronger in the smallest third of stocks (lower wick, 60 days: IC +0.056, t 3.4). The 20-day lower-wick result
survives the 54-test multiple-comparison correction (t above ~3.2).

**Is it new information?** (`wicks_check.py`) Cross-sectional correlation of the 20-day lower-wick share with
momentum 12-1 -0.03, 20-day return 0.00, delivery share +0.18, 20-day volatility -0.34 (stocks with long lower wicks
are calmer). Same method, 2012-2026:

| Signal | IC 20 days (t) | IC 60 days (t) |
|---|---|---|
| Lower wick 20d | +0.031 (4.2) | +0.037 (2.7) |
| Momentum 12-1 | +0.042 (3.3) | +0.061 (3.1) |
| Delivery share 20d | +0.052 (3.7) | +0.068 (2.9) |
| Momentum + delivery | +0.064 (4.3) | +0.090 (3.9) |
| Momentum + delivery + lower wick | +0.064 (4.6) | +0.086 (4.0) |

Reading: a real, steady effect, unrelated to momentum, weaker on its own than momentum or delivery, and adding little to the
momentum + delivery combination (slightly steadier, not stronger). Stage 2 untested; a 20-day signal trades more
often than 12-month momentum, so costs will matter.
