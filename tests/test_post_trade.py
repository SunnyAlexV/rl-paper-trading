"""FIFO round trips in post_trade.round_trips, on synthetic order files."""
import json
import post_trade


def _day(acc, d, fills):
    (acc / f"orders_after_{d}.json").write_text(json.dumps({"orders": {}, "fills_today": fills}))


def test_fifo_partial_exits_and_open_positions(tmp_path):
    acc = tmp_path / "a"; acc.mkdir()
    _day(acc, "2026-01-02", [dict(symbol="X", side="buy", qty=10, price=100.0, costs=10.0)])
    _day(acc, "2026-01-05", [dict(symbol="X", side="buy", qty=10, price=120.0, costs=12.0)])
    _day(acc, "2026-01-09", [dict(symbol="X", side="sell", qty=15, price=130.0, costs=15.0)])
    C, O = post_trade.round_trips(str(acc))
    c = C.set_index("entry")
    assert c.loc["2026-01-02", "qty"] == 10 and c.loc["2026-01-05", "qty"] == 5          # oldest lot first
    assert c.loc["2026-01-02", "entry_px"] == 100.0 and c.loc["2026-01-02", "exit_px"] == 130.0
    assert abs(c.loc["2026-01-02", "costs"] - (10 * 1.0 + 10 * 1.0)) < 1e-9             # buy and sell costs per share
    assert len(O) == 1 and O.iloc[0]["qty"] == 5 and O.iloc[0]["entry_px"] == 120.0


def test_no_fills_no_trades(tmp_path):
    acc = tmp_path / "b"; acc.mkdir(); _day(acc, "2026-01-02", [])
    C, O = post_trade.round_trips(str(acc))
    assert len(C) == 0 and len(O) == 0
