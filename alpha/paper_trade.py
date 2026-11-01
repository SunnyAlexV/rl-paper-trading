"""Forward paper-trading runner for the frozen system (pre-registered; no real orders).

Run once per NSE trading day after the bhavcopy is published (about 6-7 pm IST):
    python -m alpha.paper_trade --config paper/config.json [--date YYYY-MM-DD]

Each run, for trading day D:
  1. downloads D's bhavcopy (if missing) and rebuilds the point-in-time panel;
  2. credits cash dividends with ex-date in (D-1, D] to holdings at D-1's close, net of the
     30% + 4% cess slab tax (amended 1 Nov 2026, before the first paper-trading day), and
     applies corporate actions on D to holdings (shares / factor). NSE also adjusts PREVCLOSE for
     extraordinary dividends; when a factor matches a dividend (f ~ 1 - D / previous close) the
     dividend is credited as cash and the share count is left unchanged;
  3. fills the orders logged after D-1's close at D's open, with the full Stage 0 costs
     (STT, stamp, exchange, SEBI, GST, DP, spread, square-root impact) and FIFO tax lots;
  4. marks the book at D's close and appends to paper/nav.csv;
  5. computes the agent's decisions from data up to D's close and writes paper/orders_<D+1>.json
     BEFORE the next open; the file's hash is appended to paper/ledger.txt so nobody (including
     us) can quietly change a decision afterwards.
State lives in paper/state.json. The model, pool and agent weights are read from the frozen
config and never retrained during the paper-trading period.
"""
OUT = "paper"
import argparse, hashlib, json, os, subprocess, sys
from datetime import datetime, timezone
import numpy as np, pandas as pd
sys.path.insert(0, ".")
from costs import explicit_costs, implicit_cost_frac
from tax import TaxBook, fy_of


def load(p, default):
    return json.load(open(p)) if os.path.exists(p) else default


def main():
    global OUT
    ap = argparse.ArgumentParser(); ap.add_argument("--config", default="paper/config.json")
    ap.add_argument("--date"); ap.add_argument("--out", default="paper")
    ap.add_argument("--no-download", action="store_true"); a = ap.parse_args()
    OUT = a.out
    cfg = json.load(open(a.config)); os.makedirs(OUT, exist_ok=True)
    council = cfg.get("panel") == "council"
    if not a.no_download:
        subprocess.run([sys.executable, "data_download_bhav.py"], check=False)
        subprocess.run([sys.executable, "data_download_corpact.py"], check=False)
        caches = ["data/bhav/panel.pkl", "data/bhav/long.pkl"]
        if council:
            subprocess.run([sys.executable, "data_download_council.py"], check=False)
            caches += ["data/council_cache.pkl", "data/deliv.pkl", "data/fo.pkl"]
        if os.path.exists("roll_window.py"):
            subprocess.run([sys.executable, "roll_window.py"], check=False)
        for f in caches:
            if os.path.exists(f): os.remove(f)
    from alpha.bhav_panel import BhavPanel, build
    from alpha.signal import pool_score
    from alpha.agent_strategy import AgentStrategy
    if council:
        from alpha.council_panel import CouncilPanel, RESEARCHERS
        from alpha import grammar
        grammar.configure(sorted({f for fs in RESEARCHERS.values() for f in fs}))
        P = CouncilPanel()
    else:
        P = BhavPanel()
    b = build()
    D = pd.Timestamp(a.date) if a.date else P.dates[-1]
    t = P.dates.get_loc(D)
    st = load(f"{OUT}/state.json", dict(cash=cfg["capital"], shares={}, lots={}, entry={}, orders=None,
                                       st=0.0, lt=0.0, cf_st=[], cf_lt=[], fy=fy_of(D), last=None))
    if st["last"] and pd.Timestamp(st["last"]) >= D:
        print("already processed", D.date()); return
    names = P.names; ix = {s: i for i, s in enumerate(names)}
    raw_o, raw_c = b["raw_open"], b["raw_close"]; fac = b["factor"]
    book = TaxBook(1)
    # 0. new financial year: pay last year's tax
    if fy_of(D) != st["fy"]:
        tax, st["cf_st"], st["cf_lt"] = book._settle(st["fy"], st["st"], st["lt"], st["cf_st"], st["cf_lt"])
        st["cash"] -= tax; st["st"] = st["lt"] = 0.0; st["fy"] = fy_of(D)
    # 1a. cash dividends (ex-date in (previous trading day, D]) on holdings at the previous close
    div_cash, in_factor = 0.0, set()
    if st["shares"] and t > 0:
        from alpha.dividends import load_announcements
        from alpha.bhav_panel import parse_all, stitch_renames
        A = load_announcements()
        A = A[(A["ex"] > P.dates[t - 1]) & (A["ex"] <= D) & (A["amount"] > 0)]
        if len(A):
            lg = parse_all(); lg = lg[lg["isin"].astype(str).str.startswith("INE")]
            lg, _ = stitch_renames(lg)
            sym_of = lg[lg["date"] <= D].sort_values("date").groupby("id")["sym"].last()
            for s in list(st["shares"]):
                rows = A[A["symbol"] == sym_of.get(s, s)]
                if not len(rows):
                    continue
                amt = float(rows["amount"].sum())
                prev = float(raw_c[s].ffill().iloc[t - 1]); f = fac[s].iloc[t] if s in fac else 1.0
                y = amt / prev if prev > 0 else np.nan
                if not (y < 0.6):
                    continue                              # implausible parse, as in the backtest
                if f < 0.995 and y > 0.02 and abs(y - (1 - f)) < 0.25 * (1 - f):
                    in_factor.add(s)                      # price adjusted for this dividend
                div_cash += st["shares"][s] * amt
        st["cash"] += div_cash * (1 - 0.30 * 1.04)
    # 1b. corporate actions on holdings
    for s in list(st["shares"]):
        if s in in_factor:
            continue
        f = fac[s].iloc[t] if s in fac else 1.0
        if f != 1.0 and np.isfinite(f):
            st["shares"][s] = int(round(st["shares"][s] / f))
            st["lots"][s] = [[d, int(round(q / f)), p * f] for d, q, p in st["lots"][s]]
    # 2. fill yesterday's orders at today's open
    fills = []
    if st["orders"]:
        nav_open = st["cash"] + sum(q * raw_o[s].iloc[t] for s, q in st["shares"].items() if np.isfinite(raw_o[s].iloc[t]))
        for side in ("sell", "buy"):
            for s, w in st["orders"].items():
                p = raw_o[s].iloc[t] if s in raw_o else np.nan
                if not np.isfinite(p):
                    continue
                cur = st["shares"].get(s, 0)
                want = int(np.floor(w * nav_open / p)) if w > 0 else 0
                q = want - cur
                if (side == "sell" and q >= 0) or (side == "buy" and q <= 0):
                    continue
                if want > 0 and cur > 0 and abs(q) * p < cfg.get("min_trade_frac", 0.0) * nav_open:
                    continue
                i = ix[s]; sp = P.spread[t - 1, i]
                f = float(implicit_cost_frac(abs(q), sp, 0.02, max(1.0, float(np.nan_to_num(b["vol"][s].iloc[t - 20:t].median())))))
                fill = p * (1 - f) if q < 0 else p * (1 + f)
                val = abs(q) * fill; ec = explicit_costs(val, side)
                if side == "sell":
                    st["cash"] += val - ec["total"]; rem = -q
                    while rem > 0:
                        d0, q0, p0 = st["lots"][s][0]; take = min(rem, q0); g = take * (fill - p0)
                        if pd.Timestamp(d0) < D - pd.DateOffset(months=12): st["lt"] += g
                        else: st["st"] += g
                        st["lots"][s][0][1] -= take; rem -= take
                        if st["lots"][s][0][1] == 0: st["lots"][s].pop(0)
                else:
                    if val + ec["total"] > st["cash"]:
                        continue
                    st["cash"] -= val + ec["total"]; st["lots"].setdefault(s, []).append([str(D.date()), q, fill])
                    st["entry"].setdefault(s, str(D.date()))
                st["shares"][s] = cur + q
                if st["shares"][s] == 0:
                    st["shares"].pop(s); st["lots"].pop(s, None); st["entry"].pop(s, None)
                fills.append(dict(symbol=s, side=side, qty=int(abs(q)), price=round(fill, 2), costs=round(ec["total"], 2)))
    # 3. mark to close
    mv = sum(q * np.nan_to_num(raw_c[s].ffill().iloc[t]) for s, q in st["shares"].items())
    accrued = book._settle(st["fy"], st["st"], st["lt"], st["cf_st"], st["cf_lt"])[0]
    nav = st["cash"] + mv
    pd.DataFrame([dict(date=str(D.date()), nav=nav, nav_post_tax=nav - accrued, cash=st["cash"],
                       n_holdings=len(st["shares"]), fills=len(fills), dividends_gross=round(div_cash, 2))]).to_csv(
        f"{OUT}/nav.csv", mode="a", header=not os.path.exists(f"{OUT}/nav.csv"), index=False)
    # 4. decide for tomorrow (same rules as the backtests)
    sh = np.zeros(len(names), dtype=np.int64)
    for s_, q in st["shares"].items(): sh[ix[s_]] = q
    w_now = sh * np.nan_to_num(raw_c.ffill().values[t]) / nav
    score = pool_score(P, cfg["pool"])
    if cfg.get("rule") == "band":
        # band rule: hold k names; replace one only when it leaves the top `band`; new names share
        # the freed weight; skip names whose single share costs more than a slot
        k, band = cfg.get("k", 20), cfg.get("band", 100)
        sc = np.where(P.mask[t] & np.isfinite(score[t]), score[t], -np.inf)
        order = list(np.argsort(-sc))
        rank = {i: r for r, i in enumerate(order)}
        held = [i for i in np.where(sh > 0)[0]]
        keep = [i for i in held if rank[i] < band and np.isfinite(sc[i])]
        target = None
        if not (len(keep) == len(held) == k):
            slot = nav / k
            new = [i for i in order if i not in keep and np.isfinite(sc[i])
                   and raw_c.ffill().values[t, i] <= slot][: k - len(keep)]
            target = np.zeros(len(names))
            for i in keep: target[i] = w_now[i]
            freed = 1.0 - sum(w_now[i] for i in keep)
            for i in new: target[i] = max(freed, 0) / len(new) if new else 0
    else:
        agent = AgentStrategy(P, score, cfg["theta"], cfg.get("hyst", 0.0))
        agent.reset(None)
        agent.prev_shares = sh.copy()
        for s_, d0 in st["entry"].items():
            agent.entry_t[ix[s_]] = P.dates.get_loc(pd.Timestamp(d0)) if pd.Timestamp(d0) in P.dates else t
            agent.basis[ix[s_]] = sum(q * p for _, q, p in st["lots"].get(s_, []))
        target = agent.decide(t, dict(weights=w_now, shares=sh, cash=st["cash"], nav=nav))
    orders = None
    if target is not None:
        orders = {names[i]: float(target[i]) for i in np.where(np.abs(target - w_now) > 1e-9)[0]}
    st["orders"], st["last"] = orders, str(D.date())
    json.dump(st, open(f"{OUT}/state.json", "w"), indent=1, default=float)
    rec = dict(decided_after_close_of=str(D.date()), created_utc=datetime.now(timezone.utc).isoformat(),
               orders=orders or {}, fills_today=fills, nav=nav)
    fn = f"{OUT}/orders_after_{D.date()}.json"
    json.dump(rec, open(fn, "w"), indent=1, default=float)
    h = hashlib.sha256(open(fn, "rb").read()).hexdigest()
    open(f"{OUT}/ledger.txt", "a").write(f"{D.date()} {h} {fn}\n")
    print(f"{D.date()}: NAV Rs {nav:,.0f}, {len(fills)} fills, {len(orders or {})} orders for next open")


if __name__ == "__main__":
    main()
