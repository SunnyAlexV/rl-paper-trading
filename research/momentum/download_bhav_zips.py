import os, sys, time, concurrent.futures as cf, pandas as pd, requests
H = {"User-Agent": "Mozilla/5.0"}; OUT = "/home/claude/bt12/data/bhav/raw"
# only days we know traded (from the compact eq files)
days = [pd.Timestamp(f[:8]) for f in sorted(os.listdir("/home/claude/sentdata/eq"))]
def get(d):
    out = f"{OUT}/{d:%Y%m%d}.zip"
    if os.path.exists(out) and os.path.getsize(out) > 1000: return "cached"
    mon = d.strftime("%b").upper()
    old = f"https://nsearchives.nseindia.com/content/historical/EQUITIES/{d.year}/{mon}/cm{d:%d}{mon}{d.year}bhav.csv.zip"
    new = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{d:%Y%m%d}_F_0000.csv.zip"
    for u in ([old, new] if d < pd.Timestamp("2024-07-08") else [new, old]):
        for _ in range(4):
            try:
                r = requests.get(u, headers=H, timeout=40)
                if r.status_code == 200 and len(r.content) > 1000: open(out, "wb").write(r.content); return "ok"
                if r.status_code == 404: break
            except Exception: pass
            time.sleep(2)
    return "missing"
res = {}
with cf.ThreadPoolExecutor(10) as ex:
    for s in ex.map(get, days): res[s] = res.get(s, 0) + 1
print(res)
