"""ETF prices from the raw bhavcopy (alpha/etf_prices.py)."""
import io, zipfile
import pandas as pd
from alpha.etf_prices import etf_day


def test_reads_etf_rows_and_ignores_others(tmp_path):
    df = pd.DataFrame([["GOLDBEES", "EQ", 100.5, 101.2], ["MON100", "EQ", 300.0, 301.0], ["GOLDBEES", "BL", 1.0, 1.0],
                       ["RELIANCE", "EQ", 1400.0, 1410.0]], columns=["TckrSymb", "SctySrs", "OpnPric", "ClsPric"])
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z: z.writestr("b.csv", df.to_csv(index=False))
    (tmp_path / "20261126.zip").write_bytes(buf.getvalue())
    out = etf_day(pd.Timestamp("2026-11-26"), ["GOLDBEES", "MON100", "SILVERBEES"], folder=str(tmp_path))
    assert out == {"GOLDBEES": (100.5, 101.2), "MON100": (300.0, 301.0)}


def test_missing_day_gives_nothing(tmp_path):
    assert etf_day(pd.Timestamp("2026-11-27"), ["GOLDBEES"], folder=str(tmp_path)) == {}
