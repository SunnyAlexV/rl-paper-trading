"""Cost engine — NSE cash equity delivery, Zerodha resident individual.

Every rate is frozen in Stage 0 (doc: "RL Trading Engine — Stage 0: Frozen Assumptions"),
sourced 31 Oct 2026. The current schedule is applied to the whole history (a "today's costs"
counterfactual), which is stated in every report.
"""
from dataclasses import dataclass
import numpy as np

CRORE = 1e7


@dataclass(frozen=True)
class FeeSchedule:
    brokerage_rate: float = 0.0            # Zerodha equity delivery: Rs 0
    stt_rate: float = 0.001                # 0.1% buy and sell, rounded to nearest rupee
    exch_rate: float = 306.99 / CRORE      # NSE/FA/73061, from 1 Mar 2026, each side
    ipft_rate: float = 0.01 / CRORE        # NSE IPFT contribution, each side (+GST)
    sebi_rate: float = 10.0 / CRORE        # SEBI turnover fee, each side
    gst_rate: float = 0.18                 # on brokerage + SEBI + exchange (+IPFT)
    stamp_rate: float = 0.00015            # buy side only
    dp_charge: float = 15.34               # per scrip per sell day, incl. GST
    round_stt: bool = True


ZERODHA = FeeSchedule()


def explicit_costs(value, side, fees: FeeSchedule = ZERODHA):
    """Explicit charges for one scrip, one side, one day.

    value : traded value in rupees (>= 0)
    side  : 'buy' or 'sell'
    Returns a dict of charges in rupees (each a float), plus 'total'.
    """
    if value <= 0:
        return dict(brokerage=0.0, stt=0.0, exchange=0.0, sebi=0.0, gst=0.0,
                    stamp=0.0, dp=0.0, total=0.0)
    brokerage = fees.brokerage_rate * value
    stt = fees.stt_rate * value
    if fees.round_stt:
        stt = float(np.floor(stt + 0.5))              # nearest rupee, half up
    exchange = (fees.exch_rate + fees.ipft_rate) * value
    sebi = fees.sebi_rate * value
    gst = fees.gst_rate * (brokerage + sebi + exchange)
    stamp = fees.stamp_rate * value if side == "buy" else 0.0
    dp = fees.dp_charge if side == "sell" else 0.0
    out = dict(brokerage=brokerage, stt=stt, exchange=exchange, sebi=sebi,
               gst=gst, stamp=stamp, dp=dp)
    out["total"] = sum(out.values())
    return out


def implicit_cost_frac(qty, spread, sigma, volume, Y=1.0):
    """Half-spread + square-root impact, as a fraction of price.

    c(Q) = s/2 + Y * sigma * sqrt(Q / V)
    """
    qty = np.abs(np.asarray(qty, dtype=float))
    part = np.where(volume > 0, qty / np.maximum(volume, 1.0), 0.0)
    return np.where(qty > 0, spread / 2.0 + Y * sigma * np.sqrt(part), 0.0)


def abdi_ranaldo_spread(high, low, close, window=20, floor=1e-4):
    """Abdi–Ranaldo (2017) two-day spread estimator from daily close/high/low.

    s^2 = 4 (c_t - eta_t)(c_t - eta_{t+1}), with c = log close and eta = log mid of H/L.
    The estimate for days (t, t+1) is only known at t+1's close, so it is shifted to stay
    point-in-time; negative products are set to zero, the window mean is taken, then sqrt.
    Inputs are pandas DataFrames (dates x stocks). Returns relative spread, known at each close.
    """
    c = np.log(close)
    eta = (np.log(high) + np.log(low)) / 2.0
    prod = 4.0 * (c.shift(1) - eta.shift(1)) * (c.shift(1) - eta)   # known at t
    s2 = prod.clip(lower=0.0).rolling(window, min_periods=10).mean()
    return np.sqrt(s2).clip(lower=floor)
