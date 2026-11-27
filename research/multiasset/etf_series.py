"""Split-adjusted daily close series for the ETFs (adjustment factor = PREVCLOSE / previous close, as the stock panel).
N100 and MON100 are the same fund (symbol change Jun 2021). Run from the history working copy -> data/etf_adj.pkl"""
import pandas as pd, numpy as np
E = pd.read_pickle("data/etf_raw.pkl").sort_values("date").drop_duplicates(["date", "sym"])
E.loc[E.sym == "N100", "sym"] = "MON100"
E = E.sort_values("date").drop_duplicates(["date", "sym"], keep="last")
out = {}
for sym, q in E.groupby("sym"):
    q = q.set_index("date").sort_index()
    # Only genuine unit splits are adjustments. Small prev/close mismatches come from weekend special sessions
    # (Budget days, Muhurat trading) missing from the weekday download; the close-to-close chain already covers them.
    f = (q["prev"] / q["close"].shift(1)).fillna(1.0)
    gap = (q["open"] / q["close"].shift(1)).fillna(1.0)
    f = f.where((f - 1).abs() >= 0.20, 1.0)
    # unrecorded split: snap last close / today's close to the nearest standard split ratio (split-day opens are erratic)
    jump = (q["close"].shift(1) / q["close"]).fillna(1.0)
    RAT = np.array([2, 4, 5, 10, 20, 25, 50, 100.0])
    snap = jump.apply(lambda x: RAT[np.argmin(np.abs(np.log(RAT / x)))] if x > 1.5 else 1.0)
    f = f.mask((f == 1.0) & ((gap < 0.65) | (gap > 1 / 0.65)) & (snap > 1), 1 / snap)
    mult = f[::-1].cumprod()[::-1].shift(-1).fillna(1.0)
    out[sym] = q["close"] * mult
    jumps = f[(f - 1).abs() >= 0.02]
    if len(jumps): print(sym, "adjustments:", {str(k.date()): round(v, 4) for k, v in jumps.items()})
A = pd.DataFrame(out); A.to_pickle("data/etf_adj.pkl")
Y = A.resample("YE").last().pct_change() * 100
print(Y[["GOLDBEES", "NIFTYBEES", "MON100", "HNGSNGBEES", "SETF10GILT", "LIQUIDBEES"]].round(1).to_string())
