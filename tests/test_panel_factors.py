"""Corporate-action factors in alpha/bhav_panel.build(), on synthetic bhavcopies (new UDiFF format).

Covers: a recorded split, an unrecorded split, a weekend special session (ISSUES.md #1) and an ordinary fall."""
import io, os, zipfile
import numpy as np, pandas as pd
import pytest

DAYS = pd.bdate_range("2025-01-01", periods=300)   # 250 days of history are needed to enter the universe
K0 = 280
STOCKS = [f"S{i:02d}" for i in range(12)]        # S00 recorded split day 3; S01 unrecorded split day 4; S02 -10% day 2


def make_day(d, rows):
    df = pd.DataFrame(rows, columns=["TckrSymb", "SctySrs", "OpnPric", "HghPric", "LwPric", "ClsPric", "PrvsClsgPric",
                                     "TtlTradgVol", "TtlTrfVal", "ISIN"])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("bhav.csv", df.to_csv(index=False))
    return buf.getvalue()


@pytest.fixture()
def panel(tmp_path, monkeypatch):
    os.makedirs(tmp_path / "data/bhav/raw")
    last = {s: 100.0 for s in STOCKS}
    for k, d in enumerate(DAYS):
        rows = []
        for i, s in enumerate(STOCKS):
            close = last[s] * 1.001; prev = last[s]; opn = last[s]
            if s == "S00" and k == K0 + 3: close, prev, opn = last[s] / 2, last[s] / 2, last[s] / 2   # 1:2 split, PREVCLOSE adjusted
            if s == "S01" and k == K0 + 4: close, opn = last[s] / 2, last[s] / 2                       # 1:2 split, PREVCLOSE NOT adjusted
            if s == "S02" and k == K0 + 2: close, opn = last[s] * 0.90, last[s] * 0.95                 # an ordinary 10% fall
            if k == K0 + 6: prev = last[s] * 1.01                                                     # weekend session moved everything 1%
            rows.append([s, "EQ", opn, max(opn, close), min(opn, close), close, prev, 1e5, 1e9, f"INE{i:09d}"])
            last[s] = close
        (tmp_path / f"data/bhav/raw/{d:%Y%m%d}.zip").write_bytes(make_day(d, rows))
    monkeypatch.chdir(tmp_path)
    from alpha import bhav_panel
    return bhav_panel.build(cache=str(tmp_path / "panel.pkl"))


def test_recorded_split(panel):
    f = panel["factor"]; assert f.loc[DAYS[K0 + 3], "S00"] == pytest.approx(0.5)
    adj = panel["adj"]["close"]["S00"]
    assert adj.loc[DAYS[K0 + 3]] / adj.loc[DAYS[K0 + 2]] == pytest.approx(1.0, abs=0.01)   # no fake -50% day


def test_unrecorded_split_is_caught_by_the_gap_rule(panel):
    assert panel["factor"].loc[DAYS[K0 + 4], "S01"] == pytest.approx(0.5, abs=0.01)


def test_ordinary_fall_is_not_a_corporate_action(panel):
    assert panel["factor"].loc[DAYS[K0 + 2], "S02"] == 1.0


def test_weekend_session_is_not_a_corporate_action(panel):
    row = panel["factor"].loc[DAYS[K0 + 6]]
    assert len(row) == len(STOCKS) and (row == 1.0).all()      # not vacuous: every stock present
