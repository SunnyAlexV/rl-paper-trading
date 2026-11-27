"""Runs check_integrity on the real accounts when panel data is present (skipped otherwise)."""
import json, os
import pytest
import check_integrity

HAS_DATA = os.path.exists("data/bhav/raw") and len(os.listdir("data/bhav/raw")) > 0


@pytest.mark.skipif(not HAS_DATA, reason="no bhavcopy data in data/bhav/raw")
def test_every_running_account_is_consistent():
    from alpha.bhav_panel import build
    raw_c = build()["raw_close"]
    for a in json.load(open("paper/fleet.json"))["accounts"]:
        if os.path.exists(f"{a['out']}/nav.csv"):
            assert check_integrity.check(a["out"], raw_c) == [], a["out"]


def _account(tmp_path, nav_value=10_500.0, tamper=False, lots_qty=10):
    import hashlib
    acc = tmp_path / "acct"; acc.mkdir()
    (acc / "nav.csv").write_text("date,nav,nav_post_tax,cash\n2026-11-25,10000,10000,10000\n2026-11-26,%s,%s,9500\n" % (nav_value, nav_value))
    (acc / "state.json").write_text(json.dumps(dict(cash=9500.0, shares={"ABC": 10}, lots={"ABC": [["2026-11-26", lots_qty, 100.0]]},
                                                    last="2026-11-26")))
    f = acc / "orders_after_2026-11-26.json"; f.write_text('{"orders": {}}')
    h = hashlib.sha256(f.read_bytes()).hexdigest()
    (acc / "ledger.txt").write_text(f"2026-11-26 {h} {acc}/orders_after_2026-11-26.json\n")
    if tamper: f.write_text('{"orders": {"XYZ": 0.05}}')          # changed after hashing
    import pandas as pd
    raw_c = pd.DataFrame({"ABC": [99.0, 100.0]}, index=pd.to_datetime(["2026-11-25", "2026-11-26"]))
    return str(acc), raw_c


def test_clean_synthetic_account_passes(tmp_path):
    acc, raw_c = _account(tmp_path)
    assert check_integrity.check(acc, raw_c) == []


def test_detects_tampered_decision_file(tmp_path):
    acc, raw_c = _account(tmp_path, tamper=True)
    assert any("not in ledger" in p for p in check_integrity.check(acc, raw_c))


def test_detects_wrong_nav(tmp_path):
    acc, raw_c = _account(tmp_path, nav_value=10_600.0)
    assert any("NAV" in p for p in check_integrity.check(acc, raw_c))


def test_detects_lots_not_matching_shares(tmp_path):
    acc, raw_c = _account(tmp_path, lots_qty=9)
    assert any("lots" in p for p in check_integrity.check(acc, raw_c))
