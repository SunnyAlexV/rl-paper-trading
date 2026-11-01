"""Refresh NSE corporate-action announcements (equities) for the last three months, one month per
request, into data/corpact/YYYY-MM.json. Used by the paper trader to credit cash dividends.
(Research copy downloads 2012 onwards; a quarterly request once returned 2 rows instead of ~1,480,
hence monthly.)"""
import json, os, time, requests, pandas as pd
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json",
     "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-actions"}
os.makedirs("data/corpact", exist_ok=True)
s = requests.Session(); s.headers.update(H)
try: s.get("https://www.nseindia.com", timeout=20)
except Exception: pass
today = pd.Timestamp.today().to_period("M")
for q in pd.period_range(today - 2, today, freq="M"):
    a, b = q.start_time.strftime("%d-%m-%Y"), q.end_time.strftime("%d-%m-%Y")
    url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={a}&to_date={b}"
    d = None
    for k in range(4):
        try:
            r = s.get(url, timeout=60); r.raise_for_status(); d = r.json(); break
        except Exception:
            time.sleep(3 * (k + 1))
    if d is None:
        print("corpact FAILED", q); continue
    json.dump(d, open(f"data/corpact/{q}.json", "w")); print("corpact", q, len(d), flush=True); time.sleep(1)
