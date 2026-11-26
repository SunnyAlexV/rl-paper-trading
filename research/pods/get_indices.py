"""All NSE index closes (incl. India VIX), every trading day in data/bhav/raw -> data/indices/all_long.csv"""
import os, io, time, concurrent.futures as cf, pandas as pd, requests
H = {"User-Agent": "Mozilla/5.0"}
os.makedirs("data/indices/daily", exist_ok=True)
days = sorted(f[:8] for f in os.listdir("data/bhav/raw") if f[:8].isdigit())
def get(d):
    out = f"data/indices/daily/{d}.csv"
    if os.path.exists(out): return "cached"
    u = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{d[6:]}{d[4:6]}{d[:4]}.csv"
    for _ in range(3):
        try:
            r = requests.get(u, headers=H, timeout=30)
            if r.ok and len(r.content) > 200:
                df = pd.read_csv(io.StringIO(r.text)); df.columns = [c.strip() for c in df.columns]
                df[["Index Name", "Closing Index Value"]].assign(date=d).to_csv(out, index=False); return "ok"
            if r.status_code == 404: return "missing"
        except Exception: time.sleep(2)
        time.sleep(1)
    return "missing"
res = {}
with cf.ThreadPoolExecutor(6) as ex:
    for s in ex.map(get, days): res[s] = res.get(s, 0) + 1
print(res)
L = pd.concat([pd.read_csv(f"data/indices/daily/{f}") for f in sorted(os.listdir("data/indices/daily"))])
L.to_csv("data/indices/all_long.csv", index=False); print(L.shape)
