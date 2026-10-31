"""Capital gains tax for a resident individual on STT-paid listed equity (Stage 0 rules).

- FIFO lots per stock; long-term if sold more than 12 months after purchase.
- Short-term 20%, long-term 12.5% on gains above Rs 1.25 lakh per FY, both plus 4% cess.
- Same-year: ST loss offsets ST then LT gains; LT loss offsets LT gains only.
- Unused losses carried forward 8 FYs (ST carry-forward may offset ST or LT; LT only LT).
- Tax for an FY is paid in cash on the first trading day of the next FY (Indian FY: Apr–Mar).
"""
from collections import deque
import pandas as pd

STCG_RATE, LTCG_RATE, CESS, LTCG_EXEMPT, CF_YEARS = 0.20, 0.125, 0.04, 125_000.0, 8


def fy_of(date):
    """Indian financial year label, e.g. 2024 for Apr 2024 – Mar 2025."""
    return date.year if date.month >= 4 else date.year - 1


class TaxBook:
    def __init__(self, n_stocks, enabled=True):
        self.lots = [deque() for _ in range(n_stocks)]   # each lot: [buy_date, qty, cost_per_share]
        self.enabled = enabled
        self.st = 0.0          # net short-term gain in current FY
        self.lt = 0.0          # net long-term gain in current FY
        self.cf_st = []        # [(fy, amount>0)] carried-forward ST losses
        self.cf_lt = []
        self.paid = []         # (fy, tax)

    def buy(self, i, date, qty, price):
        if qty > 0:
            self.lots[i].append([date, int(qty), float(price)])

    def sell(self, i, date, qty, price):
        """Consume FIFO lots; return realised (st_gain, lt_gain)."""
        st = lt = 0.0
        q = int(qty)
        cutoff = date - pd.DateOffset(months=12)
        while q > 0:
            lot = self.lots[i][0]
            take = min(q, lot[1])
            g = take * (price - lot[2])
            if lot[0] < cutoff:          # held more than 12 months
                lt += g
            else:
                st += g
            lot[1] -= take
            q -= take
            if lot[1] == 0:
                self.lots[i].popleft()
        self.st += st
        self.lt += lt
        return st, lt

    def _settle(self, fy, st, lt, cf_st, cf_lt):
        """Pure function: tax for one FY and the new carry-forward lists."""
        cf_st = [(y, a) for y, a in cf_st if fy - y <= CF_YEARS]
        cf_lt = [(y, a) for y, a in cf_lt if fy - y <= CF_YEARS]
        # same-year set-off
        if st < 0 and lt > 0:
            use = min(-st, lt); lt -= use; st += use
        new_st_loss = -st if st < 0 else 0.0
        new_lt_loss = -lt if lt < 0 else 0.0
        st, lt = max(st, 0.0), max(lt, 0.0)
        # carried ST losses: ST gains first, then LT gains (oldest first)
        out_st = []
        for y, a in sorted(cf_st):
            use = min(a, st); st -= use; a -= use
            use = min(a, lt); lt -= use; a -= use
            if a > 0: out_st.append((y, a))
        out_lt = []
        for y, a in sorted(cf_lt):
            use = min(a, lt); lt -= use; a -= use
            if a > 0: out_lt.append((y, a))
        if new_st_loss > 0: out_st.append((fy, new_st_loss))
        if new_lt_loss > 0: out_lt.append((fy, new_lt_loss))
        tax = (STCG_RATE * st + LTCG_RATE * max(lt - LTCG_EXEMPT, 0.0)) * (1 + CESS)
        return tax, out_st, out_lt

    def accrued(self, fy):
        """Tax that would be due if the FY ended now (for post-tax NAV and rewards)."""
        if not self.enabled:
            return 0.0
        return self._settle(fy, self.st, self.lt, self.cf_st, self.cf_lt)[0]

    def close_year(self, fy):
        """Settle the FY: returns tax to pay and resets the year."""
        tax, self.cf_st, self.cf_lt = self._settle(fy, self.st, self.lt, self.cf_st, self.cf_lt)
        if not self.enabled:
            tax = 0.0
        self.paid.append((fy, tax))
        self.st = self.lt = 0.0
        return tax
