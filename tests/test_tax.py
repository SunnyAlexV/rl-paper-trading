"""Capital gains tax (tax.py): rates, exemption, set-off and carry-forward."""
import pytest
import pandas as pd
from tax import TaxBook, fy_of


def settle(st, lt, cf_st=(), cf_lt=(), fy=2025):
    return TaxBook(1)._settle(fy, st, lt, list(cf_st), list(cf_lt))


def test_financial_year():
    assert fy_of(pd.Timestamp("2026-03-31")) == 2025 and fy_of(pd.Timestamp("2026-04-01")) == 2026


def test_short_term_rate_with_cess():
    assert settle(100_000, 0)[0] == pytest.approx(100_000 * 0.20 * 1.04)


def test_long_term_exemption():
    assert settle(0, 125_000)[0] == pytest.approx(0.0)
    assert settle(0, 225_000)[0] == pytest.approx(100_000 * 0.125 * 1.04)


def test_short_term_loss_offsets_long_term_gain():
    tax, cf_st, cf_lt = settle(-50_000, 300_000)
    assert tax == pytest.approx((250_000 - 125_000) * 0.125 * 1.04) and cf_st == [] and cf_lt == []


def test_long_term_loss_cannot_offset_short_term_gain():
    tax, cf_st, cf_lt = settle(100_000, -40_000)
    assert tax == pytest.approx(100_000 * 0.20 * 1.04) and cf_lt == [(2025, 40_000)]


def test_carry_forward_used_and_expires():
    tax, cf_st, _ = settle(30_000, 0, cf_st=[(2020, 50_000)])
    assert tax == 0.0 and cf_st == [(2020, 20_000)]
    tax, cf_st, _ = settle(30_000, 0, cf_st=[(2016, 50_000)])          # 9 years old: expired
    assert tax == pytest.approx(30_000 * 0.20 * 1.04) and cf_st == []


def test_fifo_and_holding_period():
    b = TaxBook(1)
    b.buy(0, pd.Timestamp("2024-01-10"), 10, 100.0)
    b.buy(0, pd.Timestamp("2025-01-10"), 10, 200.0)
    st, lt = b.sell(0, pd.Timestamp("2025-03-01"), 15, 300.0)          # first lot long-term, 5 of the second short-term
    assert lt == pytest.approx(10 * 200.0) and st == pytest.approx(5 * 100.0)
    assert list(b.lots[0])[0][1] == 5
