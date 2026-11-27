# Wick long-short: rules (written 27 Nov 2026, BEFORE the run; run once)

Sunny's hypothesis: a high lower-wick share signals a long, a high upper-wick share signals a short.

Engine and book exactly as `research/pods/SPEC_LS.md` (Rs 2 crore; long leg 80% of NAV in 20 cash stocks, sell when
out of the top 100; short leg 80% notional in 15 stock futures, cover when out of the top 45 by short score; F&O ban
respected; 20% cash buffer; month-end re-equalisation; futures STT 0.05% on sells; pre-tax), with:
- **long score** = 20-day mean of the lower-wick share (min(open, close) - low) / (high - low);
- **short score** = 20-day mean of the upper-wick share (high - max(open, close)) / (high - low), highest shorted,
  among F&O stocks.
Period: 2 Jul 2012 - 26 Nov 2026. Comparators in the same simulator: long-only wick (100% invested, 20 names),
equal-weight universe, Nifty 50. Also reported: the short leg's own P&L.

Pass only if all hold (as in `SPEC_LS.md`): Sharpe >= 0.8 over the whole period and >= 0.5 in 2022-26; max drawdown
no worse than -25%; positive in at least two thirds of calendar years; daily correlation with the Nifty 50 within
+-0.4; with implicit costs doubled, Sharpe >= 0.6.
