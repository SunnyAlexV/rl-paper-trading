"""Post-trade analysis: a case file for every completed trade and a running learning ledger (analysis only).

    python3 -W ignore post_trade.py --account paper_mdeliv_10L

Writes, for the account:
  <acc>/trades/cases.csv     one row per closed trade (FIFO round trips from the fills): entry and exit, return,
                             the market's return over the same days, excess, worst and best point while held,
                             symptoms at entry and at exit, and a diagnosis;
  <acc>/trades/open.csv      positions still held, with the same measures so far;
  <acc>/trades/LEARNINGS.md  what the cases have in common: results by diagnosis and by each symptom at entry,
                             with sample sizes; patterns with n >= 30 and |t| >= 2 are listed as CANDIDATE HYPOTHESES.

Rule: nothing here changes a running account. A candidate hypothesis can only become a new, pre-registered paper
account (PREREGISTRATION.md, 27 Nov 2026 safeguards).

Symptoms are cross-sectional percentiles (0-100) over the universe on the day: 12-1 momentum, 60-day delivery %,
delivery trend (20-day minus 120-day mean), 20-day lower-wick share, 20-day volatility, size (60-day median traded
value), 20-day return. Diagnoses (first that applies):
  stock-specific crash  a day of -10% or worse while the universe fell less than 1% that day;
  market-driven         |stock return| < 2 x |market return| and the same sign (the market explains most of it);
  winner                excess return >= +5%;
  delivery faded        delivery percentile fell by 25+ points between entry and exit;
  momentum faded        momentum percentile fell by 25+ points;
  stock-specific drift  anything else.
"""
import argparse, glob, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")

SYMPTOMS = ["momentum", "delivery", "delivery_trend", "lower_wick", "volatility", "size", "return_20d"]


def round_trips(acc):
    """FIFO round trips from the fills in orders_after_<date>.json (fills happen on the date of the file)."""
    lots, closed = {}, []
    for f in sorted(glob.glob(f"{acc}/orders_after_*.json")):
        d = os.path.basename(f)[13:23]
        for x in json.load(open(f)).get("fills_today", []):
            s, q, p, c = x["symbol"], int(x["qty"]), float(x["price"]), float(x["costs"])
            if x["side"] == "buy":
                lots.setdefault(s, []).append([d, q, p, c / max(q, 1)])
            else:
                rem, sell_cost = q, c / max(q, 1)
                while rem > 0 and lots.get(s):
                    lot = lots[s][0]; take = min(rem, lot[1])
                    closed.append(dict(symbol=s, entry=lot[0], exit=d, qty=take, entry_px=lot[2], exit_px=p,
                                       costs=take * (lot[3] + sell_cost)))
                    lot[1] -= take; rem -= take
                    if lot[1] == 0: lots[s].pop(0)
    # merge partial lots of the same trade (same symbol, entry and exit dates)
    C = pd.DataFrame(closed, columns=["symbol", "entry", "exit", "qty", "entry_px", "exit_px", "costs"])
    if len(C):
        C["v_in"] = C.qty * C.entry_px; C["v_out"] = C.qty * C.exit_px
        C = C.groupby(["symbol", "entry", "exit"], as_index=False).agg(qty=("qty", "sum"), v_in=("v_in", "sum"), v_out=("v_out", "sum"), costs=("costs", "sum"))
        C["entry_px"] = C.v_in / C.qty; C["exit_px"] = C.v_out / C.qty
    O = pd.DataFrame([dict(symbol=s, entry=l[0], qty=l[1], entry_px=l[2]) for s, ls in lots.items() for l in ls],
                     columns=["symbol", "entry", "qty", "entry_px"])
    return C, O


def symptom_panel():
    from alpha.council_panel import CouncilPanel, RESEARCHERS
    from alpha import grammar
    grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
    from alpha.bhav_panel import build
    P = CouncilPanel(); D = P.dates
    F = lambda k: pd.DataFrame(P.feat[k], index=D, columns=P.names)
    c, o, h, l = F("close").ffill(), F("open"), F("high"), F("low"); dp = F("deliv_pct")
    tv = build()["tv"].reindex(index=D, columns=P.names).rolling(60, min_periods=40).median()
    raw = {"momentum": c.shift(21) / c.shift(252) - 1, "delivery": dp.rolling(60, min_periods=36).mean(),
           "delivery_trend": dp.rolling(20, min_periods=12).mean() - dp.rolling(120, min_periods=80).mean(),
           "lower_wick": ((np.minimum(o, c) - l) / (h - l).where(h > l)).rolling(20, min_periods=12).mean(),
           "volatility": c.pct_change().rolling(20, min_periods=15).std(), "size": np.log(tv), "return_20d": c / c.shift(20) - 1}
    mask = pd.DataFrame(P.mask, index=D, columns=P.names)
    pct = {k: v.replace([np.inf, -np.inf], np.nan).where(mask).rank(axis=1, pct=True) * 100 for k, v in raw.items()}
    ret = c.pct_change(); mkt = ret.where(mask).mean(axis=1)
    return dict(c=c, pct=pct, ret=ret, mkt=mkt, D=D)


def measure(row, S, exit_date=None):
    D, c, ret, mkt = S["D"], S["c"], S["ret"], S["mkt"]
    s = row["symbol"]; e = pd.Timestamp(row["entry"]); x = pd.Timestamp(exit_date or row["exit"])
    out = {}
    if s not in c.columns or e not in D or x not in D:
        return out
    path = c[s].loc[e:x]
    if len(path) and path.iloc[0] > 0:
        rel = path / path.iloc[0] - 1
        out["worst_point_pct"] = round(float(rel.min() * 100), 1); out["best_point_pct"] = round(float(rel.max() * 100), 1)
    m = (1 + mkt.loc[e:x].iloc[1:]).prod() - 1
    out["market_pct"] = round(float(m * 100), 1)
    r_ = ret[s].loc[e:x].iloc[1:]; mk = mkt.loc[e:x].iloc[1:]
    out["crash_day"] = bool(((r_ <= -0.10) & (mk > -0.01)).any())
    # symptoms as seen when each decision was made: the close before the entry fill and before the exit fill
    e_dec = D[max(D.get_loc(e) - 1, 0)]; x_dec = x if exit_date else D[max(D.get_loc(x) - 1, 0)]
    for k in SYMPTOMS:
        v0 = S["pct"][k].at[e_dec, s]
        v1 = S["pct"][k].at[x_dec, s]
        out[f"{k}_entry"] = round(float(v0), 0) if np.isfinite(v0) else np.nan
        out[f"{k}_exit"] = round(float(v1), 0) if np.isfinite(v1) else np.nan
    return out


def diagnose(r):
    ret, m = r["return_pct"], r.get("market_pct", np.nan)
    if r.get("crash_day"): return "stock-specific crash"
    if np.isfinite(m) and m != 0 and np.sign(ret) == np.sign(m) and abs(ret) < 2 * abs(m): return "market-driven"
    if r["excess_pct"] >= 5: return "winner"
    if r.get("delivery_entry", np.nan) - r.get("delivery_exit", np.nan) >= 25: return "delivery faded"
    if r.get("momentum_entry", np.nan) - r.get("momentum_exit", np.nan) >= 25: return "momentum faded"
    return "stock-specific drift"


def learnings(C, acc):
    L = [f"# Learning ledger: {acc}\n",
         f"_{len(C)} closed trades. Analysis only: patterns here are hypotheses, never changes to this account._\n"]
    if not len(C):
        return "\n".join(L + ["No closed trades yet."])
    t = lambda v: v.mean() / (v.std(ddof=1) / np.sqrt(len(v))) if len(v) > 2 and v.std(ddof=1) > 0 else np.nan
    L.append(f"Overall: {(C.excess_pct > 0).mean() * 100:.0f}% beat the market; mean return {C.return_pct.mean():+.1f}%, "
             f"mean excess {C.excess_pct.mean():+.1f}% (t {t(C.excess_pct):.1f}); median holding {C.days.median():.0f} days.\n")
    L.append("## By diagnosis\n\n| Diagnosis | Trades | Mean return | Mean excess | Mean worst point |\n|---|---|---|---|---|")
    for dname, g in C.groupby("diagnosis"):
        L.append(f"| {dname} | {len(g)} | {g.return_pct.mean():+.1f}% | {g.excess_pct.mean():+.1f}% | {g.worst_point_pct.mean():+.1f}% |")
    L.append("\n## By symptom at entry (top vs bottom half of the universe)\n\n| Symptom at entry | High: n / mean excess | Low: n / mean excess | Difference (t) |\n|---|---|---|---|")
    cands = []
    for k in SYMPTOMS:
        v = C[f"{k}_entry"]
        hi, lo = C.excess_pct[v >= 50], C.excess_pct[v < 50]
        if len(hi) and len(lo):
            diff = hi.mean() - lo.mean()
            se = np.sqrt(hi.var(ddof=1) / max(len(hi), 1) + lo.var(ddof=1) / max(len(lo), 1)) if len(hi) > 1 and len(lo) > 1 else np.nan
            tt = diff / se if se and np.isfinite(se) and se > 0 else np.nan
            L.append(f"| {k.replace('_', ' ')} | {len(hi)} / {hi.mean():+.1f}% | {len(lo)} / {lo.mean():+.1f}% | {diff:+.1f} pts ({tt:.1f}) |")
            if len(hi) + len(lo) >= 30 and np.isfinite(tt) and abs(tt) >= 2:
                cands.append(f"- Trades entered with **{k.replace('_', ' ')} {'high' if diff > 0 else 'low'}** did better by "
                             f"{abs(diff):.1f} points (t {abs(tt):.1f}, n = {len(hi) + len(lo)}).")
    L.append("\n## Candidate hypotheses (n >= 30 and |t| >= 2)\n")
    L += cands if cands else ["None yet. With fewer than 30 trades or |t| < 2, differences above are most likely noise."]
    L.append("\nA candidate becomes a test only through a dated, pre-registered new paper account (27 Nov 2026 safeguards), "
             "counted in research/TRIALS.md; the running accounts never change. Several symptoms are checked at once, so "
             "about 1 in 3 accounts would show a |t| >= 2 pattern by chance alone.")
    return "\n".join(L)


def case_notes(C, acc, n=30):
    """Plain-language case file for each closed trade, newest first."""
    L = [f"# Trade case files: {acc}\n", "_Newest first. Symptoms are percentiles in the universe (0 = lowest, 100 = highest), "
         "read at the close before each decision._\n"]
    if not len(C):
        return "\n".join(L + ["No closed trades yet."])
    def change(k, r):
        a_, b_ = r.get(f"{k}_entry"), r.get(f"{k}_exit")
        return f"{k.replace('_', ' ')} {a_:.0f} -> {b_:.0f}" if np.isfinite(a_) and np.isfinite(b_) else f"{k.replace('_', ' ')} n/a"
    for _, r in C.sort_values(["exit", "entry"], ascending=False).head(n).iterrows():
        moved = sorted(SYMPTOMS, key=lambda k: -abs((r.get(f"{k}_exit") or 0) - (r.get(f"{k}_entry") or 0)))[:3]
        L.append(f"## {r.symbol}: {r.entry} -> {r.exit} ({r.days} days), {r.return_pct:+.1f}% "
                 f"(market {r.get('market_pct', float('nan')):+.1f}%, excess {r.excess_pct:+.1f}%), Rs {r.pnl_rs:+,.0f}\n")
        L.append(f"- **History (why bought):** momentum {r.momentum_entry:.0f}, delivery {r.delivery_entry:.0f}, delivery trend "
                 f"{r.delivery_trend_entry:.0f}, lower wick {r.lower_wick_entry:.0f}, volatility {r.volatility_entry:.0f}, size {r.size_entry:.0f}.")
        L.append(f"- **Course:** worst point {r.get('worst_point_pct', float('nan')):+.1f}%, best point {r.get('best_point_pct', float('nan')):+.1f}%"
                 + ("; **a stock-specific crash day** while the market was calm." if r.get("crash_day") else "."))
        L.append(f"- **What changed by the exit:** " + "; ".join(change(k, r) for k in moved) + ".")
        L.append(f"- **Diagnosis:** {r.diagnosis}.\n")
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--account", required=True); a = ap.parse_args(); acc = a.account
    C, O = round_trips(acc)
    os.makedirs(f"{acc}/trades", exist_ok=True)
    S = symptom_panel() if (len(C) or len(O)) else None
    rows = []
    for _, r in C.iterrows():
        m = measure(r, S)
        ret = (r.exit_px * r.qty - r.entry_px * r.qty - r.costs) / (r.entry_px * r.qty) * 100
        row = dict(symbol=r.symbol, entry=r.entry, exit=r.exit, days=(pd.Timestamp(r.exit) - pd.Timestamp(r.entry)).days,
                   qty=int(r.qty), entry_px=round(r.entry_px, 2), exit_px=round(r.exit_px, 2), return_pct=round(ret, 1),
                   pnl_rs=round(r.exit_px * r.qty - r.entry_px * r.qty - r.costs, 0), **m)
        row["excess_pct"] = round(row["return_pct"] - row.get("market_pct", 0.0), 1)
        row["diagnosis"] = diagnose(row); rows.append(row)
    C2 = pd.DataFrame(rows); C2.to_csv(f"{acc}/trades/cases.csv", index=False)
    last = None
    navf = f"{acc}/nav.csv"
    if os.path.exists(navf): last = pd.read_csv(navf)["date"].iloc[-1]
    orows = []
    for _, r in O.iterrows():
        m = measure(r, S, exit_date=last) if (S is not None and last) else {}
        px = S["c"][r.symbol].loc[pd.Timestamp(last)] if (S is not None and last and r.symbol in S["c"].columns) else np.nan
        orows.append(dict(symbol=r.symbol, entry=r.entry, qty=int(r.qty), entry_px=round(r.entry_px, 2),
                          return_so_far_pct=round((px / r.entry_px - 1) * 100, 1) if np.isfinite(px) else np.nan, **m))
    pd.DataFrame(orows).to_csv(f"{acc}/trades/open.csv", index=False)
    open(f"{acc}/trades/LEARNINGS.md", "w").write(learnings(C2, acc))
    open(f"{acc}/trades/CASES.md", "w").write(case_notes(C2, acc))
    print(f"[{acc}] {len(C2)} closed trades, {len(orows)} open positions -> {acc}/trades/")


if __name__ == "__main__":
    main()
