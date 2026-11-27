# Factor attribution of the primary (written 27 Nov 2026, BEFORE the run; run once)

Question (review committee): how much of momentum + delivery's return is known factor exposure, and is anything left?

**Factors**, built from the point-in-time universe, equal-weighted, rebalanced monthly, Jul 2012 - Nov 2026:
- **MKT**: equal-weight universe return minus cash (6.5% a year);
- **SIZE**: smallest third minus largest third by 60-day median traded value (proxy: no market capitalisation in the data);
- **MOM**: top third minus bottom third by 12-1 momentum;
- **LOWVOL**: lowest third minus highest third by 250-day volatility;
- **DELIV** (reported separately): top third minus bottom third by 60-day mean delivery %.
No value factor (no book values in the data) - a stated gap.

**Regression:** monthly excess returns (strategy minus cash) of the primary (momentum + delivery, `backtest.run`, Rs 10L,
all fees, pre-tax NAV) on MKT, SIZE, MOM, LOWVOL; Newey-West standard errors (3 lags). Reported: annualised alpha with t,
betas, R-squared. Also with DELIV added (does delivery explain the rest?), and for comparison the momentum-only book and the
frozen council.

Reading fixed in advance: alpha t >= 2 = return beyond the four known factors; alpha t < 2 with DELIV making it vanish =
the extra return is the delivery effect, a factor rather than skill; alpha near zero without DELIV = mostly known factors.
