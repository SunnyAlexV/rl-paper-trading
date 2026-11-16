"""Fleet scoreboard: every paper account's post-tax return since its start vs the indices over
the same dates. Writes paper/fleet_report.md and prints it.  python3 fleet_report.py"""
import json
import pandas as pd

IX = pd.read_csv("data/indices/closes.csv", parse_dates=["date"]).set_index("date")
accts = json.load(open("paper/fleet.json"))["accounts"]


def chg(col, a, z):
    s = IX[col].dropna()
    s = s[(s.index >= a) & (s.index <= z)]
    return s.iloc[-1] / s.iloc[0] - 1 if len(s) > 1 and s.index[0] == a else float("nan")


rows = []
for a in accts:
    try:
        n = pd.read_csv(f"{a['out']}/nav.csv", parse_dates=["date"])
    except FileNotFoundError:
        continue
    d0, d1 = n["date"].iloc[0], n["date"].iloc[-1]
    cap = n["nav"].iloc[0]; ret = n["nav_post_tax"].iloc[-1] / cap - 1
    nf = chg("Nifty 50", d0, d1)
    peak = n["nav_post_tax"].cummax(); dd = (n["nav_post_tax"] / peak - 1).min()
    rows.append(dict(account=a["out"], capital=cap, start=d0.date(), days=len(n) - 1,
                     nav_post_tax=n["nav_post_tax"].iloc[-1], ret=ret, nifty50=nf, vs_nifty=ret - nf,
                     nifty500=chg("Nifty 500", d0, d1), max_dd=dd, fills=int(n["fills"].sum())))
R = pd.DataFrame(rows)
pct = lambda x: "n/a" if pd.isna(x) else f"{x:+.2%}"
lines = [f"# Fleet scoreboard, as of {pd.read_csv('paper/nav.csv')['date'].iloc[-1]}", "",
         "Post-tax return since each account's start vs Nifty 50 / Nifty 500 (price indices) over the same dates.", "",
         "| Account | Capital | Start | Days | Post-tax NAV | Return | Nifty 50 | vs Nifty 50 | Nifty 500 | Max DD | Fills |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    lines.append(f"| {r['account']} | {r['capital']:,.0f} | {r['start']} | {r['days']} | {r['nav_post_tax']:,.0f} | {pct(r['ret'])} | "
                 f"{pct(r['nifty50'])} | {pct(r['vs_nifty'])} | {pct(r['nifty500'])} | {pct(r['max_dd'])} | {r['fills']} |")
open("paper/fleet_report.md", "w").write("\n".join(lines) + "\n")
R.to_csv("paper/fleet_report.csv", index=False)
print("\n".join(lines))
