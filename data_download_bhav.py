"""Download NSE equity bhavcopy (every listed stock, every day) 2010 -> today.
Old format up to Jul 2024 (cmDDMONYYYYbhav.csv.zip), new UDiFF format after."""
import os, time, concurrent.futures as cf
import pandas as pd, requests
import os as _os
if _os.path.exists("data/raw.pkl"):
    dates = pd.read_pickle("data/raw.pkl").index
else:   # paper-trading repo: weekdays over a rolling ~2-year window (holidays return 404 and are skipped)
    dates = pd.bdate_range(pd.Timestamp.today().normalize() - pd.Timedelta(days=760), pd.Timestamp.today().normalize())
dates = dates[dates >= "2010-01-01"]
# for daily (paper-trading) use, extend past the Yahoo calendar with weekdays up to today;
# NSE holidays simply return 404 and are skipped
dates = dates.union(pd.bdate_range(dates[-1] + pd.Timedelta(days=1), pd.Timestamp.today().normalize()))
H = {"User-Agent": "Mozilla/5.0"}
def urls(d):
    old = f"https://nsearchives.nseindia.com/content/historical/EQUITIES/{d.year}/{d.strftime('%b').upper()}/cm{d.strftime('%d%b%Y').upper()}bhav.csv.zip"
    new = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{d.strftime('%Y%m%d')}_F_0000.csv.zip"
    return [old, new] if d < pd.Timestamp("2024-07-08") else [new, old]
def get(d):
    out = f"data/bhav/raw/{d.strftime('%Y%m%d')}.zip"
    if os.path.exists(out) and os.path.getsize(out) > 1000:
        return "cached"
    for u in urls(d):
        for k in range(3):
            try:
                r = requests.get(u, headers=H, timeout=30)
                if r.status_code == 200 and len(r.content) > 1000:
                    open(out, "wb").write(r.content); return "ok"
                if r.status_code == 404: break
            except Exception:
                time.sleep(2)
            time.sleep(1)
    return "missing"
res = {}
with cf.ThreadPoolExecutor(6) as ex:
    for d, s in zip(dates, ex.map(get, dates)):
        res[s] = res.get(s, 0) + 1
print(res)
