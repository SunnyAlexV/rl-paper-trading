"""ETF prices for one day from the raw NSE bhavcopy zip (the stock panel excludes ETFs, ISIN INF*).
Used only by accounts with "rule": "multi" (added 27 Nov 2026, research/multiasset/SPEC_B.md)."""
import os, zipfile
import pandas as pd
from costs import FeeSchedule

# ETF units: STT 0.001% on equity-ETF sells and none on gold ETFs (taken as 0.001% for both, conservatively);
# other charges as for shares (exchange, SEBI, GST, stamp 0.015% on buys, DP charge on sell days).
ETF_FEES = FeeSchedule(stt_rate=0.00001, round_stt=False)
ETF_HALF_SPREAD = 0.0005          # liquid ETFs: about 5 basis points each way


def etf_day(D, symbols, folder="data/bhav/raw"):
    """{symbol: (open, close)} for the trading day D; symbols missing that day are left out."""
    f = os.path.join(folder, f"{pd.Timestamp(D):%Y%m%d}.zip")
    if not os.path.exists(f):
        return {}
    z = zipfile.ZipFile(f); df = pd.read_csv(z.open(z.namelist()[0])); df.columns = [c.strip() for c in df.columns]
    if "SYMBOL" in df.columns:
        s, o, c, ser = "SYMBOL", "OPEN", "CLOSE", "SERIES"
    else:
        s, o, c, ser = "TckrSymb", "OpnPric", "ClsPric", "SctySrs"
    df["_s"] = df[s].astype(str).str.strip()
    df = df[df["_s"].isin(symbols) & (df[ser].astype(str).str.strip() == "EQ")]
    return {r["_s"]: (float(r[o]), float(r[c])) for _, r in df.iterrows()}
