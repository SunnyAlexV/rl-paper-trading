"""Council data: NSE security-wise delivery (MTO files) and F&O bhavcopy, 2010 -> today.

Delivery  -> data/deliv/YYYYMMDD.csv : symbol, traded_qty, deliv_qty           (EQ series only)
F&O       -> data/fo/YYYYMMDD.csv    : symbol, fut_close (nearest expiry), fut_oi (all expiries),
                                       fut_oi_chg, call_oi, put_oi, opt_volume (stock F&O only)
Only these compact per-stock summaries are kept, not the raw F&O files (~1 MB/day).
"""
import io, os, time, zipfile, concurrent.futures as cf
import pandas as pd, requests

H = {"User-Agent": "Mozilla/5.0"}
import os as _os
if _os.path.exists("data/raw.pkl"):
    dates = pd.read_pickle("data/raw.pkl").index
else:   # paper-trading repo: weekdays over a rolling ~2-year window (holidays return 404 and are skipped)
    dates = pd.bdate_range(pd.Timestamp.today().normalize() - pd.Timedelta(days=760), pd.Timestamp.today().normalize())
dates = dates[dates >= "2010-01-01"]
# for daily (paper-trading) use, extend past the Yahoo calendar with weekdays up to today;
# NSE holidays simply return 404 and are skipped
dates = dates.union(pd.bdate_range(dates[-1] + pd.Timedelta(days=1), pd.Timestamp.today().normalize()))
os.makedirs("data/deliv", exist_ok=True); os.makedirs("data/fo", exist_ok=True)


def fetch(u):
    for _ in range(3):
        try:
            r = requests.get(u, headers=H, timeout=40)
            if r.status_code == 200 and len(r.content) > 500:
                return r.content
            if r.status_code == 404:
                return None
        except Exception:
            time.sleep(2)
        time.sleep(1)
    return None


def deliv(d):
    out = f"data/deliv/{d:%Y%m%d}.csv"
    if os.path.exists(out):
        return "cached"
    c = fetch(f"https://nsearchives.nseindia.com/archives/equities/mto/MTO_{d:%d%m%Y}.DAT")
    if c is None:
        return "missing"
    rows = []
    for line in c.decode("latin-1").splitlines():
        p = line.split(",")
        if len(p) >= 6 and p[0] == "20" and p[3].strip() == "EQ":
            try:
                rows.append((p[2].strip(), float(p[4]), float(p[5])))
            except ValueError:
                pass
    pd.DataFrame(rows, columns=["symbol", "traded_qty", "deliv_qty"]).to_csv(out, index=False)
    return "ok"


def fo(d):
    out = f"data/fo/{d:%Y%m%d}.csv"
    if os.path.exists(out):
        return "cached"
    mon = d.strftime("%b").upper()
    old = f"https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{d.year}/{mon}/fo{d:%d}{mon}{d.year}bhav.csv.zip"
    new = f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{d:%Y%m%d}_F_0000.csv.zip"
    for u in ([old, new] if d < pd.Timestamp("2024-07-08") else [new, old]):
        c = fetch(u)
        if c is None:
            continue
        with zipfile.ZipFile(io.BytesIO(c)) as z:
            df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
        df.columns = [x.strip() for x in df.columns]
        if "INSTRUMENT" in df.columns:
            df = df.rename(columns={"INSTRUMENT": "inst", "SYMBOL": "symbol", "EXPIRY_DT": "exp", "OPTION_TYP": "otype",
                                    "CLOSE": "close", "OPEN_INT": "oi", "CHG_IN_OI": "doi", "CONTRACTS": "vol"})
            df["inst"] = df["inst"].map({"FUTSTK": "fut", "OPTSTK": "opt"})
        else:
            df = df.rename(columns={"FinInstrmTp": "inst", "TckrSymb": "symbol", "XpryDt": "exp", "OptnTp": "otype",
                                    "ClsPric": "close", "OpnIntrst": "oi", "ChngInOpnIntrst": "doi", "TtlTradgVol": "vol"})
            df["inst"] = df["inst"].map({"STF": "fut", "STO": "opt"})
        df = df[df["inst"].notna()].copy()
        df["exp"] = pd.to_datetime(df["exp"], format="mixed", dayfirst=False, errors="coerce")
        fut = df[df.inst == "fut"].sort_values("exp")
        g = fut.groupby("symbol")
        res = pd.DataFrame({"fut_close": g["close"].first(), "fut_oi": g["oi"].sum(), "fut_oi_chg": g["doi"].sum()})
        opt = df[df.inst == "opt"]
        res["call_oi"] = opt[opt.otype.astype(str).str.upper() == "CE"].groupby("symbol")["oi"].sum()
        res["put_oi"] = opt[opt.otype.astype(str).str.upper() == "PE"].groupby("symbol")["oi"].sum()
        res["opt_volume"] = opt.groupby("symbol")["vol"].sum()
        res.reset_index().to_csv(out, index=False)
        return "ok"
    return "missing"


if __name__ == "__main__":
    for name, fn in (("delivery", deliv), ("fo", fo)):
        res = {}
        with cf.ThreadPoolExecutor(6) as ex:
            for r in ex.map(fn, dates):
                res[r] = res.get(r, 0) + 1
        print(name, res, flush=True)
