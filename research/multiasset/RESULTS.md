# Multi-asset menu: results (27 Nov 2026)

Rules: `SPEC.md` (committed before the run). Pre-tax; E = momentum + delivery sleeve, G = gold (GOLDBEES),
US = Nasdaq-100 (N100/MON100), C = cash at 6.5%. Mixes chosen on Jul 2012 - Dec 2019, tested on Jan 2020 - Nov 2026
(`menu.csv`; all ~300 mixes in `menu_all_mixes.csv`).

| Worst-fall limit | Mix chosen on 2012-19 | 2012-19 CAGR / max DD | **2020-26 CAGR / Sharpe / max DD (unseen)** | Within limit in 2020-26? |
|---|---|---|---|---|
| 10% | E 40 / US 10 / C 50 | 14.9% / -8.5% | 18.4% / 1.88 / **-15.5%** | No |
| 15% | E 60 / US 20 / C 20 | 20.1% / -14.8% | 25.5% / 1.63 / **-24.4%** | No |
| 20% and 25% | E 70 / US 30 | 23.6% / -18.6% | 30.2% / 1.55 / **-29.9%** | No |
| none | E 70 / US 30 | same | same | - |

Single assets, Jul 2012 - Nov 2026: E 26.8% (max DD -33.5%), US 23.4% (-36.6%), gold 9.2% (-31.7%), cash 6.4%.
Daily correlations: E-gold -0.02, E-US 0.24, gold-US 0.07.

**Findings.**
1. **Every mix fell further in 2020-26 than its 2012-19 limit**, by about 1.5-1.6 times: COVID was worse than anything in the
   design period. A worst-fall limit set from history needs a safety margin; to stay within 15% live, plan for about
   10% historically.
2. **Diversification works**: the momentum sleeve, gold and US tech barely move together, so mixes cut drawdowns sharply
   (e.g. the 10%-limit mix: -15.5% in COVID-era 2020-26 vs -33.5% for E alone) while keeping strong returns.
3. **Gold was not picked on 2012-19** because it fell three years running (2013-15), but with hindsight it is part of
   most of the best full-period mixes (e.g. E 30 / G 40 / US 30 for a 20% limit). Choosing by recent past
   undervalues a diversifier just before it is needed.
4. Data note: SETF10GILT shows a -27.6% drawdown, implausible for a 10-year gilt fund (likely a bad print in thin
   trading); it was not used for selection.
