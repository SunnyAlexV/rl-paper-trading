# Robustness of climbing-protection stops with intraday execution (written 27 Nov 2026, BEFORE the run; run once)

Same simulator and rules as `SPEC_INTRADAY.md`, rest variant.
1. **Other slack settings, pre-tax:** m = 1.5 and m = 3.
2. **With tax:** base and m = 2, with capital gains tax added to the simulator: each sale's gain = proceeds - (purchase
   value + buy costs); held under 1 year = short-term 20%, otherwise long-term 12.5% above Rs 1.25 lakh per financial year,
   both plus 4% cess (as `tax.py`); short-term losses offset any gain, long-term losses only long-term gains; net losses
   carried forward; the year's tax is paid from cash on the first trading day of the next financial year; NAV is reported
   net of tax accrued so far.

Pass bar for each run (as before): max drawdown at least 20% smaller than the matching base, and Sharpe no more than
0.05 below it.
**The add-on is robust if m = 2 passes with tax and at least one of m = 1.5 / 3 passes pre-tax.**
