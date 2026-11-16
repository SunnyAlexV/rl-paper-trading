"""Daily closes of benchmark indices from NSE's ind_close_all files -> data/indices/closes.csv.

Fetches every trading day (dates taken from the bhavcopy files in data/bhav/raw) from START on
that is not already stored. Price indices (no dividends); used only for comparison, never for trading.
"""
import os, io, time
import pandas as pd, requests

START = "2026-10-30"
KEEP = ["Nifty 50", "Nifty 500", "Nifty Midcap 150", "Nifty Smallcap 250"]
OUT = "data/indices/closes.csv"
H = {"User-Agent": "Mozilla/5.0"}

os.makedirs("data/indices", exist_ok=True)
have = pd.read_csv(OUT, dtype={"date": str}) if os.path.exists(OUT) else pd.DataFrame(columns=["date"] + KEEP)
done = set(pd.to_datetime(have["date"]).dt.date)
days = sorted(pd.to_datetime(f[:8]).date() for f in os.listdir("data/bhav/raw") if f[:8].isdigit())
rows = []
for d in days:
    if str(d) < START or d in done:
        continue
    u = f"https://nsearchives.nseindia.com/content/indices/ind_close_all_{d.strftime('%d%m%Y')}.csv"
    for attempt in range(3):
        try:
            r = requests.get(u, headers=H, timeout=30)
            if r.ok:
                df = pd.read_csv(io.StringIO(r.text))
                df = df[df["Index Name"].isin(KEEP)].set_index("Index Name")["Closing Index Value"]
                rows.append({"date": str(d), **{k: float(df[k]) for k in KEEP if k in df}})
            break
        except Exception:
            time.sleep(2)
if rows:
    have = pd.concat([have, pd.DataFrame(rows)]).sort_values("date")
    have["date"] = pd.to_datetime(have["date"]).dt.strftime("%Y-%m-%d")
    have.to_csv(OUT, index=False)
print("indices", {"new": len(rows), "total": len(have)})
