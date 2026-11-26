"""Stock + NIFTY futures, nearest two expiries, every day -> data/fut/YYYYMMDD.csv; F&O ban list -> data/ban/YYYYMMDD.txt"""
import io, os, time, zipfile, concurrent.futures as cf, pandas as pd, requests
H = {"User-Agent": "Mozilla/5.0"}
os.makedirs("data/fut", exist_ok=True); os.makedirs("data/ban", exist_ok=True)
days = sorted(f[:8] for f in os.listdir("data/bhav/raw") if f[:8].isdigit())
def fetch(u):
    for _ in range(3):
        try:
            r = requests.get(u, headers=H, timeout=40)
            if r.status_code == 200 and len(r.content) > 20: return r.content
            if r.status_code == 404: return None
        except Exception: time.sleep(2)
        time.sleep(1)
    return None
def fut(d):
    out = f"data/fut/{d}.csv"
    if os.path.exists(out): return "cached"
    D = pd.Timestamp(d); mon = D.strftime("%b").upper()
    old = f"https://nsearchives.nseindia.com/content/historical/DERIVATIVES/{D.year}/{mon}/fo{D:%d}{mon}{D.year}bhav.csv.zip"
    new = f"https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{d}_F_0000.csv.zip"
    for u in ([old, new] if D < pd.Timestamp("2024-07-08") else [new, old]):
        c = fetch(u)
        if c is None: continue
        with zipfile.ZipFile(io.BytesIO(c)) as z: df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
        df.columns = [x.strip() for x in df.columns]
        if "INSTRUMENT" in df.columns:
            df = df[df.INSTRUMENT.isin(["FUTSTK", "FUTIDX"])]
            df = pd.DataFrame(dict(kind=df.INSTRUMENT.map({"FUTSTK": "stk", "FUTIDX": "idx"}), symbol=df.SYMBOL.str.strip(),
                exp=pd.to_datetime(df.EXPIRY_DT, format="mixed"), open=df.OPEN, close=df.CLOSE, settle=df.SETTLE_PR,
                oi=df.OPEN_INT, contracts=df.CONTRACTS, lot=pd.NA))
        else:
            df = df[df.FinInstrmTp.isin(["STF", "IDF"])]
            df = pd.DataFrame(dict(kind=df.FinInstrmTp.map({"STF": "stk", "IDF": "idx"}), symbol=df.TckrSymb.str.strip(),
                exp=pd.to_datetime(df.XpryDt), open=df.OpnPric, close=df.ClsPric, settle=df.SttlmPric,
                oi=df.OpnIntrst, contracts=df.TtlTradgVol, lot=df.NewBrdLotQty))
        df = df[(df.kind == "stk") | (df.symbol == "NIFTY")].sort_values(["symbol", "exp"])
        df = df.groupby("symbol").head(2)
        df.to_csv(out, index=False); return "ok"
    return "missing"
def ban(d):
    out = f"data/ban/{d}.txt"
    if os.path.exists(out): return "cached"
    c = fetch(f"https://nsearchives.nseindia.com/archives/fo/sec_ban/fo_secban_{d[6:]}{d[4:6]}{d[:4]}.csv")
    if c is None: return "missing"
    lines = c.decode("utf-8", "ignore").splitlines()[1:]
    open(out, "w").write("\n".join(l.split(",", 1)[1].strip() for l in lines if "," in l)); return "ok"
if __name__ == "__main__":
    for name, fn in (("ban", ban), ("fut", fut)):
        res = {}
        with cf.ThreadPoolExecutor(6) as ex:
            for r in ex.map(fn, days): res[r] = res.get(r, 0) + 1
        print(name, res, flush=True)
