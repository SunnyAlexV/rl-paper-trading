# Long-short pods results (27 Nov 2026)

Rules and criteria: `SPEC_LS.md` (committed before this run). Script: `ls_bt.py`. Rs 2 crore per book,
Feb 2016 - 26 Nov 2026, **pre-tax**, full costs. Files: `ls_metrics.csv`, `ls_years.csv`, `ls_navs_monthly.csv`.

| Book | CAGR | Sharpe | Max DD | Corr. with Nifty | Verdict |
|---|---|---|---|---|---|
| **LS-Trend** (long top-20 momentum, short bottom-15 F&O momentum) | 5.0% | 0.36 | -38% | -0.13 | **Fail** (criteria 1, 2, 3, 5, 6) |
| **LS-Council** | 1.0% | 0.15 | -43% | -0.46 | **Fail** (all) |
| **Hedged-Trend** (long momentum, short Nifty futures x beta) | 13.2% | 0.83 | -35% | 0.33 | **Fail** (Sharpe below Long-Trend; drawdown only 24% smaller) |
| Long-Trend (comparator) | 22.4% | 0.94 | -46% | 0.64 | |
| Long-Council (comparator) | 17.2% | 1.09 | -35% | 0.70 | |
| Equal-weight universe | 13.8% | 0.79 | -55% | 0.81 | |
| Nifty 50 (price) | 12.1% | 0.80 | -38% | 1 | |

Robustness: all 9 LS-Trend variants have Sharpe 0.24-0.49; all 9 LS-Council variants 0.07-0.25.
Doubled implicit costs: LS-Trend 0.04, LS-Council -0.20.

**Check of the futures data.** On 19,418 random contract-days, futures daily returns minus the stock's
return have median -0.03% (5th-95th percentile -0.56% to +0.59%), so the futures series are sound.

**Why the shorts lost.**
1. *The market rose.* The bottom-15 F&O stocks by momentum still returned +4.7% a year (F&O
   equal weight +14.0%). They lagged, but shorting something that rises loses money. Their lag
   relative to the F&O average (-0.50% a month) is not significant (t = -1.2).
2. *Rebounds.* Losers rallied hard in 2016 (+53%) and 2020; the short leg lost 21-24% of NAV in
   those years, which is the known momentum-crash pattern.
3. *Mismatched legs.* Longs are mid/small caps, shorts are F&O large caps, so a rupee-neutral book
   is net short the market (LS-Council's correlation with the Nifty is -0.46).
4. *Costs and margin.* The short leg turns over constantly and rolls monthly; the 20% cash buffer was
   breached ~180 times, each time forcing long sales.

Sizing: at Rs 2 crore a short position is about Rs 10.7 lakh, about 1.6 median stock-futures lots.

**Conclusion under the pre-set rules.** Shorting via futures did not help any book. The long-only
books remain the better ones. A beta-neutral book with both legs inside the F&O universe would be
a new hypothesis and needs its own rules written down first.
