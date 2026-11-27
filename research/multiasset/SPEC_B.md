# Multi-asset mix B: rules (chosen by Sunny on 27 Nov 2026 on principle, BEFORE any backtest of this mix)

**Mix:** 40% momentum + delivery equity sleeve (the primary rule: 20 stocks, band 100, scaled to 40% of NAV),
20% gold (GOLDBEES), 10% Nasdaq-100 (MON100), 30% cash.
**Why this mix:** not optimised. Gold is held because it is the asset least related to the equity sleeve (daily correlation
-0.02, 2012-2026) and the one a backtest-chosen mix dropped (it fell in 2013-15) just before it was needed; US tech adds a
second, loosely related equity market (0.24); cash damps everything.
**Rebalancing:** each asset back to its target at every month-end; between month-ends the equity sleeve follows the band
rule inside its 40%.

**Backtest (reported once, for information; no pass/fail):** Jul 2012 - Nov 2026, same simulator and costs as
`menu.py` (pre-tax; cash at 6.5%), compared with the equity sleeve alone and with mix A (E 40 / US 10 / C 50):
CAGR, Sharpe, max drawdown, worst calendar year, 2020-26 separately.

**Paper account (to be added in Jan 2027 under the 27 Nov safeguards):** `paper_multi_10L`, Rs 10L, these rules
unchanged; cash earns a liquid-fund rate through the engine's existing `cash_rate` (taxed at slab rate, as in
`research/timing`). Requires ETF support in `alpha/paper_trade.py`, built and checked before the amendment.

Engine support added and checked on 27 Nov 2026 (see the "Code, 27 Nov 2026" entry in PREREGISTRATION.md); config
`paper/config_multi_10L.json` (cash_rate 5.5%, as `paper_timed_10L`).
