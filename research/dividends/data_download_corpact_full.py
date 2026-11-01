"""Download NSE corporate actions (equities), one month per request (a 2017Q3 quarterly request returned 2 rows instead of ~1,480), 2012-today.
Saved raw as data/corpact/YYYYQ.json. Uses the public NSE API (cookie from the home page first)."""
import json, os, time, requests, pandas as pd
H = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Referer": "https://www.nseindia.com/companies-listing/corporate-filings-actions"}
s = requests.Session(); s.headers.update(H)
try: s.get("https://www.nseindia.com", timeout=20)
except Exception: pass
for q in pd.period_range("2012-01", pd.Timestamp.today().to_period("M"), freq="M"):
    out = f"data/corpact/{q}.json"
    if os.path.exists(out) and q != pd.Timestamp.today().to_period("M"):
        continue
    a, b = q.start_time.strftime("%d-%m-%Y"), q.end_time.strftime("%d-%m-%Y")
    url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&from_date={a}&to_date={b}"
    for k in range(4):
        try:
            r = s.get(url, timeout=60); r.raise_for_status(); d = r.json(); break
        except Exception as e:
            time.sleep(3 * (k + 1)); d = None
    if d is None:
        print("FAILED", q); continue
    json.dump(d, open(out, "w")); print(q, len(d), flush=True); time.sleep(1)
