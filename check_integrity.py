"""Daily integrity check of every paper account in paper/fleet.json (read-only; changes nothing).

    python3 -W ignore check_integrity.py        (exit code 1 and a list of problems if any check fails)

For each account: every orders_after_<date>.json is hashed in ledger.txt; nav.csv dates are unique and increasing; the
latest nav date, orders file and state.json 'last' agree; tax lots add up to share counts; and the latest NAV equals cash
plus holdings at that day's close (stocks from the panel, ETFs from the stored last close) to within Rs 1.
"""
import glob, hashlib, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")


def check(acc, raw_c):
    p = []
    ledger = open(f"{acc}/ledger.txt").read() if os.path.exists(f"{acc}/ledger.txt") else ""
    for f in sorted(glob.glob(f"{acc}/orders_after_*.json")):
        h = hashlib.sha256(open(f, "rb").read()).hexdigest()
        if f"{h} {f}" not in ledger: p.append(f"{f}: SHA-256 not in ledger.txt")
    nav = pd.read_csv(f"{acc}/nav.csv", parse_dates=["date"])
    if not nav["date"].is_monotonic_increasing or nav["date"].duplicated().any(): p.append("nav.csv dates not unique and increasing")
    st = json.load(open(f"{acc}/state.json")); D = nav["date"].iloc[-1]
    if st.get("last") != str(D.date()): p.append(f"state last {st.get('last')} != nav.csv last {D.date()}")
    if not os.path.exists(f"{acc}/orders_after_{D.date()}.json"): p.append(f"no orders file for {D.date()}")
    for s, q in st["shares"].items():
        if q <= 0 or int(q) != q: p.append(f"{s}: share count {q}")
        if sum(l[1] for l in st["lots"].get(s, [])) != q: p.append(f"{s}: lots {sum(l[1] for l in st['lots'].get(s, []))} != shares {q}")
    etf = st.get("etf_last", {}); mv = 0.0
    for s, q in st["shares"].items():
        if s in etf: mv += q * etf[s]
        elif s in raw_c.columns and D in raw_c.index: mv += q * float(np.nan_to_num(raw_c[s].ffill().loc[D]))
        else: p.append(f"{s}: no price on {D.date()}")
    if abs(st["cash"] + mv - nav["nav"].iloc[-1]) > 1.0:
        p.append(f"NAV {nav['nav'].iloc[-1]:,.2f} != cash + holdings {st['cash'] + mv:,.2f}")
    return p


if __name__ == "__main__":
    from alpha.bhav_panel import build
    raw_c = build()["raw_close"]
    bad = 0
    for a in json.load(open("paper/fleet.json"))["accounts"]:
        if not os.path.exists(f"{a['out']}/nav.csv"):
            print(f"[{a['out']}] not started yet"); continue
        probs = check(a["out"], raw_c)
        bad += len(probs)
        print(f"[{a['out']}] " + ("OK" if not probs else "PROBLEMS: " + "; ".join(probs)))
    sys.exit(1 if bad else 0)
