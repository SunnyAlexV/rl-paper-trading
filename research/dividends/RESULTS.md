# Dividends in the backtests (27 Nov 2026)

NSE corporate-action announcements Jun 2011 - Nov 2026 (183 monthly API pulls, none failed) parsed by
`alpha/dividends.py` (the live trader's parser): 14,439 dividend announcements matched to the panel, 14,387 credited,
3 already removed by NSE's price adjustment (extraordinary dividends), 49 dropped as implausible parses. Credited at
ex-date to holders at the previous close, taxed at 31.2% (as the live trader). Stage 2, post-tax, Rs 10L,
Jul 2012 - Nov 2026 (`with_dividends.csv`).

| Book | Price only: CAGR / Sharpe | With dividends: CAGR / Sharpe | Change |
|---|---|---|---|
| Momentum + delivery (primary) | 26.7% / 1.38 | **27.4% / 1.42** | +0.7 pts |
| Momentum only | 20.0% / 0.87 | 19.8% / 0.86 | -0.3 pts (path change) |
| Council (frozen) | 19.4% / 1.20 | 20.3% / 1.25 | +0.9 pts |
| Equal-weight universe | 13.3% / 0.79 | **14.4% / 0.84** | +1.1 pts |

After tax, dividends add about 1 point a year to the benchmark and 0.7 to the primary; the primary's lead over the
equal-weight universe moves from 13.4 to 13.0 points. **No conclusion changes.** (Momentum only falls slightly because
the extra cash changes which stocks the band rule buys later; a path effect, not a loss.) The live trader has credited
dividends since the 1 Nov 2026 amendment.
