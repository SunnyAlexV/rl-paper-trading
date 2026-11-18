"""Research-only download of NSE daily files 2015 -> 2026-11-17 into /home/claude/sentdata (NOT the trading repo).
Per day, compact CSVs:
  eq/YYYYMMDD.csv   : symbol, open, high, low, close, prev, qty, val           (EQ series; prev is NSE's CA-adjusted prev close)
  fo/YYYYMMDD.csv   : symbol, kind(stk|idx), fut_close, fut_oi, fut_oi_chg, call_oi, put_oi, opt_vol
  dl/YYYYMMDD.csv   : symbol, traded_qty, deliv_qty
  ix/YYYYMMDD.csv   : index, close    (Nifty 50, Nifty 500, India VIX, Nifty Bank)
"""
import io, os, sys, time, zipfile, concurrent.futures as cf
import pandas as pd, requests

BASE = "/home/claude/sentdata"; H = {"User-Agent": "Mozilla/5.0"}
for k in ("eq", "fo", "dl", "ix"): os.makedirs(f"{BASE}/{k}", exist_ok=True)
start, end = sys.argv[1], sys.argv[2]
dates = pd.bdate_range(start, end)
NEW = pd.Timestamp("2024-07-08")

def fetch(u):
    for _ in range(4):
        try:
            r = requests.get(u, headers=H, timeout=40)
            if r.status_code == 200 and len(r.content) > 300: return r.content
            if r.status_code == 404: return None
        except Exception: pass
        time.sleep(2)
    return None

def unzip_csv(c):
    with zipfile.ZipFile(io.BytesIO(c)) as z: df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
    df.columns = [x.strip() for x in df.columns]; return df

def eq(d):
    out = f"{BASE}/eq/{d:%Y%m%d}.csv"
    if os.path.exists(out): return "cached"
    mon = d.strftime("%b").upper()
    old = f"https://nsearchives.nseindia.com/content/historical/EQUITIES/{d.year}/{mon}/cm{d:%d}{mon}{d.year}bhav.csv.zip"
    new = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{d:%Y%m%d}_F_0000.csv.zip"
    for u in ([old, new] if d < NEW else [new, old]):
        c = fetch(u)
        if c is None: continue
        df = unzip_csv(c)
        if "SYMBOL" in df.columns:
            df = df[df.SERIES.str.strip() == "EQ"]
            o = pd.DataFrame({"symbol": df.SYMBOL, "open": df.OPEN, "high": df.HIGH, "low": df.LOW, "close": df.CLOSE,
                              "prev": df.PREVCLOSE, "qty": df.TOTTRDQTY, "val": df.TOTTRDVAL})
        else:
            df = df[df.SctySrs.astype(str).str.strip() == "EQ"]
            o = pd.DataFrame({"symbol": df.TckrSymb, "open": df.OpnPric, "high": df.HghPric, "low": df.LwPric, "close": df.ClsPric,
                              "prev": df.PrvsClsgPric, "qty": df.TtlTradgVol, "val": df.TtlTrfVal})
        o.to_csv(out, index=False); return "ok"
    return "missing"

def fo(d):
    out = f"{BASE}/fo/{d:%Y%m%d}.csv"
    if os.path.exists(out): return "cached"
    mon = d.strftime("%b").upper()
    old = f"https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{d.year}/{mon}/fo{d:%d}{mon}{d.year}bhav.csv.zip"
    new = f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{d:%Y%m%d}_F_0000.csv.zip"
    for u in ([old, new] if d < NEW else [new, old]):
        c = fetch(u)
        if c is None: continue
        df = unzip_csv(c)
        if "INSTRUMENT" in df.columns:
            df = df.rename(columns={"INSTRUMENT": "inst", "SYMBOL": "symbol", "EXPIRY_DT": "exp", "OPTION_TYP": "otype",
                                    "CLOSE": "close", "OPEN_INT": "oi", "CHG_IN_OI": "doi", "CONTRACTS": "vol"})
            m = {"FUTSTK": ("stk", "fut"), "OPTSTK": ("stk", "opt"), "FUTIDX": ("idx", "fut"), "OPTIDX": ("idx", "opt")}
        else:
            df = df.rename(columns={"FinInstrmTp": "inst", "TckrSymb": "symbol", "XpryDt": "exp", "OptnTp": "otype",
                                    "ClsPric": "close", "OpnIntrst": "oi", "ChngInOpnIntrst": "doi", "TtlTradgVol": "vol"})
            m = {"STF": ("stk", "fut"), "STO": ("stk", "opt"), "IDF": ("idx", "fut"), "IDO": ("idx", "opt")}
        df["inst"] = df["inst"].astype(str).str.strip()
        df = df[df.inst.isin(m)].copy()
        df["kind"] = df.inst.map(lambda x: m[x][0]); df["typ"] = df.inst.map(lambda x: m[x][1])
        df["exp"] = pd.to_datetime(df["exp"], format="mixed", errors="coerce")
        df["symbol"] = df.symbol.astype(str).str.strip()
        fut = df[df.typ == "fut"].sort_values("exp"); g = fut.groupby(["symbol", "kind"])
        res = pd.DataFrame({"fut_close": g.close.first(), "fut_oi": g.oi.sum(), "fut_oi_chg": g.doi.sum()})
        opt = df[df.typ == "opt"]; ot = opt.otype.astype(str).str.strip().str.upper()
        res = res.join(opt[ot == "CE"].groupby(["symbol", "kind"]).oi.sum().rename("call_oi"), how="outer")
        res = res.join(opt[ot == "PE"].groupby(["symbol", "kind"]).oi.sum().rename("put_oi"), how="outer")
        res = res.join(opt.groupby(["symbol", "kind"]).vol.sum().rename("opt_vol"), how="outer")
        res.reset_index().to_csv(out, index=False); return "ok"
    return "missing"

def dl(d):
    out = f"{BASE}/dl/{d:%Y%m%d}.csv"
    if os.path.exists(out): return "cached"
    c = fetch(f"https://nsearchives.nseindia.com/archives/equities/mto/MTO_{d:%d%m%Y}.DAT")
    if c is None: return "missing"
    rows = []
    for line in c.decode("latin-1").splitlines():
        p = line.split(",")
        if len(p) >= 6 and p[0] == "20" and p[3].strip() == "EQ":
            try: rows.append((p[2].strip(), float(p[4]), float(p[5])))
            except ValueError: pass
    pd.DataFrame(rows, columns=["symbol", "traded_qty", "deliv_qty"]).to_csv(out, index=False); return "ok"

KEEP = ["Nifty 50", "Nifty 500", "India VIX", "Nifty Bank"]
def ix(d):
    out = f"{BASE}/ix/{d:%Y%m%d}.csv"
    if os.path.exists(out): return "cached"
    c = fetch(f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{d:%d%m%Y}.csv")
    if c is None: return "missing"
    try:
        df = pd.read_csv(io.BytesIO(c)); df.columns = [x.strip() for x in df.columns]
        df = df[df["Index Name"].str.strip().str.lower().isin([k.lower() for k in KEEP])]
        pd.DataFrame({"index": df["Index Name"].str.strip(), "close": df["Closing Index Value"]}).to_csv(out, index=False)
        return "ok"
    except Exception: return "bad"

if __name__ == "__main__":
    for name, fn in (("ix", ix), ("eq", eq), ("dl", dl), ("fo", fo)):
        res = {}
        with cf.ThreadPoolExecutor(8) as ex:
            for r in ex.map(fn, dates): res[r] = res.get(r, 0) + 1
        print(name, start, end, res, flush=True)
