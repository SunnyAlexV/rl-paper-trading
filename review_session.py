"""Post-session review (analysis only; never trades, never touches state, config or signal files).

    python3 -W ignore review_session.py [--account paper] [--date YYYY-MM-DD]

Writes <account>/reviews/<date>.md explaining the session:
  1. the day's P&L by holding, against the Nifty indices and the equal-weight universe;
  2. every fill: price vs open/close, what the trade gained or cost vs not trading, and
     (for exits) the round-trip result of the position;
  3. why each new order was chosen: the stock's council rank and which researchers'
     formulas pushed it up, recomputed from the same frozen pool the trader uses;
  4. the record since the start: winners, losers, hit rate, costs and tax, and the gap to the
     Nifty 50 split into size/style, stock selection, and costs+tax;
  5. watch-list: largest weights, holdings closest to the band exit.
"""
import argparse, glob, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, ".")


def pct(x): return f"{x*100:+.2f}%"
def rs(x): return f"Rs {x:+,.0f}"


def load_fills(acc):
    rows = []
    for f in sorted(glob.glob(f"{acc}/orders_after_*.json")):
        j = json.load(open(f)); d = os.path.basename(f)[13:23]
        for x in j.get("fills_today", []): rows.append(dict(date=d, **x))
    return pd.DataFrame(rows, columns=["date", "symbol", "side", "qty", "price", "costs"])


def score_breakdown(cfg):
    """Per-researcher contribution to the blended council score, last day only."""
    from alpha.council_panel import CouncilPanel, RESEARCHERS
    from alpha import grammar
    from alpha.grammar import evaluate
    from alpha.scoring import zrank
    grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
    P = CouncilPanel()
    pool = json.load(open(f"results/alpha_{cfg['pool']}.json"))
    parts, forms = {}, []
    for a in pool["alphas"]:
        z = zrank(evaluate(a["seq"], P.feat), P.mask)[-1] * a["weight"]
        parts[a["researcher"]] = parts.get(a["researcher"], 0) + z
        forms.append((a["formula"], a["researcher"], z))
    tot = sum(parts.values())
    m = P.mask[-1]
    s = np.where(m, tot, np.nan); mu, sd = np.nanmean(s), np.nanstd(s)
    scale = sd if sd > 0 else 1
    names = list(P.names)
    rank = pd.Series(np.where(m, tot, -np.inf), index=names).rank(ascending=False, method="first")
    return dict(names=names, idx={n: i for i, n in enumerate(names)}, rank=rank,
                score=(tot - mu) / scale, parts={k: v / scale for k, v in parts.items()},
                forms=[(f, r, z / scale) for f, r, z in forms], date=P.dates[-1], n=int(m.sum()))


def explain(sym, B):
    i = B["idx"].get(sym)
    if i is None: return "not in panel"
    p = sorted(((k, v[i]) for k, v in B["parts"].items()), key=lambda kv: -abs(kv[1]))
    f = sorted(((fm, r, z[i]) for fm, r, z in B["forms"]), key=lambda x: -x[2])[:3]
    top = "; ".join(f"`{fm}` ({r}) {z:+.2f}" for fm, r, z in f)
    return (f"rank {int(B['rank'][sym])} of {int(np.isfinite(B['score']).sum())}, score {B['score'][i]:+.2f} "
            f"= " + ", ".join(f"{k} {v:+.2f}" for k, v in p) + f". Strongest formulas: {top}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--account", default="paper"); ap.add_argument("--date")
    a = ap.parse_args(); acc = a.account
    cfgp = json.load(open("paper/fleet.json"))
    cfgfile = next(x["config"] for x in cfgp["accounts"] if x["out"] == acc)
    cfg = json.load(open(cfgfile))
    p = pd.read_pickle("data/bhav/panel.pkl")
    C, O, A, M, TV = p["raw_close"], p["raw_open"], p["adj"]["close"], p["member"].astype(bool), p["tv"]
    nav = pd.read_csv(f"{acc}/nav.csv", index_col=0, parse_dates=True)
    D = pd.Timestamp(a.date) if a.date else nav.index[-1]
    Dm1 = nav.index[nav.index.get_loc(D) - 1]
    ix = pd.read_csv("data/indices/closes.csv", index_col=0, parse_dates=True)
    st = json.load(open(f"{acc}/state.json"))
    j = json.load(open(f"{acc}/orders_after_{D.date()}.json"))
    jprev = json.load(open(f"{acc}/orders_after_{Dm1.date()}.json"))
    F = load_fills(acc)
    L = []; w = L.append
    n1, n0 = nav.at[D, "nav"], nav.at[Dm1, "nav"]
    w(f"# Session review: {acc}, {D.date()}\n")
    w(f"_Analysis only. The trading rule is frozen (PREREGISTRATION.md); nothing here changes it._\n")

    # 1. the day
    r_ix = ix.loc[D] / ix.loc[Dm1] - 1
    ret = A.loc[D] / A.loc[Dm1] - 1; u = ret[M.loc[D]]
    w("## 1. The day\n")
    w(f"Portfolio {pct(n1/n0-1)} pre-tax ({rs(n1-n0)}); post-tax NAV Rs {nav.at[D,'nav_post_tax']:,.0f}. "
      f"Nifty 50 {pct(r_ix['Nifty 50'])}, Nifty 500 {pct(r_ix['Nifty 500'])}, Midcap 150 {pct(r_ix['Nifty Midcap 150'])}, "
      f"Smallcap 250 {pct(r_ix['Nifty Smallcap 250'])}; equal-weight universe {pct(u.mean())} ({(u>0).mean()*100:.0f}% of stocks up).\n")
    bought = {f["symbol"]: f for f in j["fills_today"] if f["side"] == "buy"}
    rows = []
    for s, q in st["shares"].items():
        c1 = C.at[D, s]; base = bought[s]["price"] if s in bought else C.at[Dm1, s]
        q0 = q - (bought[s]["qty"] if s in bought else 0)
        pnl = q0 * (c1 - C.at[Dm1, s]) + (q - q0) * (c1 - base) if s in bought else q * (c1 - base)
        rows.append((s, c1 / (C.at[Dm1, s]) - 1, pnl, q * c1 / n1, (ret[s] - u.mean()) / u.std()))
    for f in j["fills_today"]:
        if f["side"] == "sell":
            rows.append((f["symbol"] + " (sold at open)", f["price"] / C.at[Dm1, f["symbol"]] - 1,
                         f["qty"] * (f["price"] - C.at[Dm1, f["symbol"]]), 0.0, np.nan))
    T = pd.DataFrame(rows, columns=["sym", "ret", "pnl", "w", "z"]).sort_values("pnl", ascending=False)
    w("Move z = (stock's day return - universe average) / universe standard deviation that day. "
      "|z| > 2 is an unusual, stock-specific move; |z| < 1 is ordinary market noise.\n")
    w("| Holding | Day | Move z | P&L | Weight |\n|---|---|---|---|---|")
    for _, x in T.iterrows():
        zs = "" if np.isnan(x.z) else f"{x.z:+.2f}" + (" **unusual**" if abs(x.z) > 2 else "")
        w(f"| {x.sym} | {pct(x.ret)} | {zs} | {rs(x.pnl)} | {x.w*100:.1f}% |")
    costs_today = sum(f["costs"] for f in j["fills_today"])
    w(f"\nCosts today {rs(-costs_today)}. Best: {T.iloc[0].sym}; worst: {T.iloc[-1].sym}.\n")

    # 2. each fill
    w("## 2. Today's fills\n")
    if not j["fills_today"]: w("No fills.\n")
    for f in j["fills_today"]:
        s = f["symbol"]; o, c = O.at[D, s], C.at[D, s]
        slip = (f["price"] / o - 1) * (1 if f["side"] == "buy" else -1)
        if f["side"] == "sell":
            vs = f["qty"] * (f["price"] - c)
            g = F[F.symbol == s]; b_ = g[g.side == "buy"]; s_ = g[g.side == "sell"]
            inv = (b_.qty * b_.price).sum()
            rt = (s_.qty * s_.price).sum() - inv - g.costs.sum()
            held = (D - pd.Timestamp(b_.date.min())).days
            w(f"- **SELL {s}** {f['qty']} @ {f['price']:.2f} (open {o:.2f}, close {c:.2f}; cost {f['costs']:.2f}, "
              f"slippage {slip*100:.2f}%). Selling at the open vs holding to the close: {rs(vs)}. "
              f"Round trip since {b_.date.min()} ({held} days): {rs(rt)} ({pct(rt/inv)}) "
              f"→ **{'success' if rt > 0 else 'failure'}**. Exit reason: fell out of the top {cfg.get('band','?')}.")
        else:
            vs = f["qty"] * (c - f["price"])
            w(f"- **BUY {s}** {f['qty']} @ {f['price']:.2f} (open {o:.2f}, close {c:.2f}; cost {f['costs']:.2f}, "
              f"slippage {slip*100:.2f}%). First-day mark: {rs(vs)}. "
              f"Target weight was {jprev['orders'].get(s, 0)*100:.1f}%, actual {f['qty']*c/n1*100:.1f}%.")
    w("")

    # 3. why tomorrow's orders
    w("## 3. Orders for the next open, and why\n")
    try:
        B = score_breakdown(cfg) if cfg.get("pool") else None
    except Exception as e:
        B = None; w(f"_(score breakdown unavailable: {e})_\n")
    if not cfg.get("pool"):
        w(f"_This account ranks stocks by {cfg.get('signal', 'plain 12-1 momentum (return from 12 months to 1 month ago)')}, not the council, so there is no per-formula breakdown._\n")
    for s, tw in j["orders"].items():
        act = "SELL ALL" if tw == 0 else ("BUY" if s not in st["shares"] else "RESIZE")
        why = explain(s, B) if B else ""
        w(f"- **{act} {s}** → target {tw*100:.1f}%. {why}")
    if not j["orders"]: w("No orders: every holding is still inside the band.")
    if "exposure" in j: w(f"\nTiming-agent exposure: {j['exposure']}.")
    w("")
    if B:
        zs = pd.Series(B["score"], index=B["names"]).sort_values(ascending=False).dropna()
        k, band = cfg.get("k", 20), cfg.get("band", 100)
        w(f"**Council z-scores of current holdings.** Each of the 17 formulas is turned into a cross-sectional "
          f"rank z-score (0 = average stock, +1 = one standard deviation better), weighted, summed, and re-standardised. "
          f"Today a stock needs z >= {zs.iloc[k-1]:+.2f} to be in the top {k} (buy line) and is sold below "
          f"z = {zs.iloc[band-1]:+.2f} (rank {band}, sell line).\n")
        res = list(B["parts"])
        w("| Holding | Rank | z-score | " + " | ".join(res) + " | Cushion to sell line |\n|" + "---|" * (len(res) + 4))
        hold = sorted(st["shares"], key=lambda s: B["rank"].get(s, 9999))
        for s in hold:
            i = B["idx"].get(s)
            if i is None: continue
            w(f"| {s} | {int(B['rank'][s])} | {B['score'][i]:+.2f} | " + " | ".join(f"{B['parts'][r][i]:+.2f}" for r in res)
              + f" | {B['score'][i]-zs.iloc[band-1]:+.2f} |")
        w("")

    # 4. record since start
    start = nav.index[0]
    w(f"## 4. Record since {start.date()}\n")
    out = []
    for s, g in F.groupby("symbol"):
        b_ = g[g.side == "buy"]; s_ = g[g.side == "sell"]; q = st["shares"].get(s, 0)
        inv = (b_.qty * b_.price).sum()
        pnl = (s_.qty * s_.price).sum() - inv - g.costs.sum() + q * C.at[D, s]
        out.append((s, "open" if q else "closed", inv, pnl))
    R = pd.DataFrame(out, columns=["sym", "status", "inv", "pnl"]).sort_values("pnl")
    R["ret"] = R.pnl / R.inv
    hit = (R.pnl > 0).mean()
    w(f"{len(R)} positions so far, {hit*100:.0f}% profitable. Total costs {rs(-F.costs.sum())}; "
      f"tax provision {rs(nav.at[D,'nav_post_tax']-nav.at[D,'nav'])}.\n")
    w("Worst: " + ", ".join(f"{x.sym} {pct(x.ret)} ({rs(x.pnl)}, {x.status})" for _, x in R.head(3).iterrows()))
    w("\nBest: " + ", ".join(f"{x.sym} {pct(x.ret)} ({rs(x.pnl)}, {x.status})" for _, x in R.tail(3)[::-1].iterrows()) + "\n")
    r = A.loc[start:D].pct_change().iloc[1:]
    ew = (1 + r.where(M.loc[r.index]).mean(axis=1)).prod() - 1
    n50 = ix.at[D, "Nifty 50"] / ix.at[start, "Nifty 50"] - 1
    pre = nav.at[D, "nav"] / nav.iloc[0]["nav"] - 1; post = nav.at[D, "nav_post_tax"] / nav.iloc[0]["nav_post_tax"] - 1
    cost_pts = F.costs.sum() / nav.iloc[0]["nav"]
    w("| Gap to Nifty 50 | pts |\n|---|---|")
    w(f"| Size/style: equal-weight universe {pct(ew)} vs Nifty 50 {pct(n50)} | {(ew-n50)*100:+.2f} |")
    w(f"| Stock selection (pre-cost) | {(pre+cost_pts-ew)*100:+.2f} |")
    w(f"| Trading costs | {-cost_pts*100:+.2f} |")
    w(f"| Tax provision | {(post-pre)*100:+.2f} |")
    w(f"| **Total: post-tax {pct(post)} vs Nifty 50** | **{(post-n50)*100:+.2f}** |\n")

    # 5. watch-list
    w("## 5. Watch-list\n")
    wts = {s: q * C.at[D, s] / n1 for s, q in st["shares"].items()}
    big = sorted(wts.items(), key=lambda x: -x[1])[:3]
    w("Largest weights: " + ", ".join(f"{s} {v*100:.1f}%" for s, v in big) + f". Cash {st['cash']/n1*100:.1f}%.")
    tv = TV.iloc[-60:].median(); lr = tv[M.iloc[-1]].rank(ascending=False)
    lq = sorted(int(lr[s]) for s in st["shares"] if s in lr)
    if lq: w(f"\nLiquidity rank of holdings in the 500 universe: median {int(np.median(lq))} (1 = most traded).")
    w("\n## 6. Notes from Sunny\n\n_(add your observations here)_\n")
    os.makedirs(f"{acc}/reviews", exist_ok=True)
    path = f"{acc}/reviews/{D.date()}.md"
    open(path, "w").write("\n".join(L))
    print("review written", path)


if __name__ == "__main__":
    main()
