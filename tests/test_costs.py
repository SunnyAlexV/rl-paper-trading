"""Explicit-cost engine: statutory charges for one scrip, one side, one day (costs.py)."""
import pytest
from costs import explicit_costs, CRORE
from alpha.etf_prices import ETF_FEES


def test_buy_one_lakh():
    c = explicit_costs(100_000, "buy")
    assert c["stt"] == 100.0                                   # 0.1%, rounded to the rupee
    assert c["stamp"] == pytest.approx(15.0)                   # 0.015%, buy side only
    assert c["dp"] == 0.0
    assert c["exchange"] == pytest.approx((306.99 + 0.01) / CRORE * 1e5)
    assert c["gst"] == pytest.approx(0.18 * (c["exchange"] + c["sebi"] + c["brokerage"]))
    assert c["total"] == pytest.approx(sum(v for k, v in c.items() if k != "total"))


def test_sell_has_dp_and_no_stamp():
    c = explicit_costs(100_000, "sell")
    assert c["dp"] == pytest.approx(15.34) and c["stamp"] == 0.0 and c["stt"] == 100.0


def test_stt_rounding_half_up():
    assert explicit_costs(1_500, "buy")["stt"] == 2.0          # 1.50 -> 2
    assert explicit_costs(1_400, "buy")["stt"] == 1.0          # 1.40 -> 1


def test_zero_value_costs_nothing():
    assert explicit_costs(0, "sell")["total"] == 0.0


def test_etf_stt_is_tiny_and_unrounded():
    c = explicit_costs(100_000, "sell", ETF_FEES)
    assert c["stt"] == pytest.approx(1.0) and c["dp"] == pytest.approx(15.34)
