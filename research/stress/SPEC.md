# Stress tests of momentum + delivery before making it the primary (written 27 Nov 2026, BEFORE the run)

Rule under test: the live `paper_mdeliv_10L` rule (equal-weight rank z-scores of 12-1 momentum and 60-day mean
delivery %, band rule hold 20 / sell when out of the top 100, max 7.5%, min trade 1%). Engine `backtest.run`, Stage 2
(all fees, post-tax) unless stated. History Jul 2012 - 26 Nov 2026.

1. **Random halves (cross-sectional holdout).** 25 random splits of all stock ids into halves A and B. In each half,
   run the rule scaled to the half (hold 10, sell when out of the top 50) and the half's own equal-weight universe.
   *Pass:* the rule's Sharpe beats its half's equal-weight Sharpe in at least 90% of the 50 halves.
2. **Start-date windows.** From the full-period run, every rolling 12-, 24- and 36-month window starting at a
   month-end: share of windows in which the rule beats the equal-weight universe; worst relative window.
   *Pass:* beats the equal-weight universe in at least 75% of 36-month windows.
3. **Harsh costs.** Implicit costs (spread + impact) x2 and x3. *Pass:* Sharpe at x2 above the equal-weight
   universe's at x2.
4. **Drawdowns.** Five deepest drawdowns: depth, dates, months to recover; longest stretch below its previous
   relative peak against the equal-weight universe. *Reported, no pass/fail.*
5. **Capital.** Same rule at Rs 1L and Rs 50L. *Reported, no pass/fail.*

If 1-3 pass, the rule is proposed as the new primary test (Sunny decides), before its first live trade.
