"""Cash dividends from NSE corporate-action announcements, aligned to the bhavcopy panel.

Source: data/corpact/YYYY-MM.json (data_download_corpact.py), the NSE corporate-actions API.
Each announcement has a symbol, ISIN, face value, ex-date and a free-text "subject", e.g.
  "Annual General Meeting/Dividend - Rs 8 Per Share"
  "Interim Dividend - Re 0.50 Per Share (Purpose Revised)"
  "Final Dividend - Rs 10 Per Share And Special Dividend - Rs 5 Per Share"
  "Dividend - 40%"                         (old style: percent of face value)

Parsing: every "dividend" in the subject is paired with the first amount that follows it
(Rs/Re x, or x% of face value) before the next "dividend". Amounts of one announcement add up.
Duplicates: NSE re-posts an announcement when its purpose is revised. For one (symbol, ex-date)
the revised rows are used if any exist; otherwise identical rows count once.

Units: the engine holds shares in back-adjusted units (prices x m_t, m_t = product of later
corporate-action factors), so a raw dividend D paid on ex-date t is D x m_t per adjusted share.
Ex-date is the first trading day on or after the announced ex-date; holders at the previous
close receive it (the engine's existing step 3), taxed at slab rate (30% + 4% cess).
"""
import glob, json, re
import numpy as np, pandas as pd

AMT = re.compile(r"dividend(?P<body>.*?)(?=dividend|$)", re.I)
RS = re.compile(r"(?:\bR[se]\.?[\s:/-]*|[-\s])([0-9]+(?:\.[0-9]+)?)\s*(?:/-|/)?\s*Per\b|\bR[se]\.?[\s:/-]*([0-9]+(?:\.[0-9]+)?)", re.I)
PCT = re.compile(r"([0-9]+(?:\.[0-9]+)?)\s*%")


def parse_amount(subject, face):
    total, found = 0.0, False
    for m in AMT.finditer(subject):
        body = m.group("body")
        r, p = RS.search(body), PCT.search(body)
        if r and (not p or r.start() < p.start()):
            total += float(r.group(1) or r.group(2)); found = True
        elif p:
            try:
                total += float(p.group(1)) / 100 * float(face); found = True
            except ValueError:
                pass
    return total if found else np.nan


def load_announcements():
    rows = sum([json.load(open(f)) for f in sorted(glob.glob("data/corpact/*.json"))], [])
    df = pd.DataFrame(rows)
    df = df[(df["series"] == "EQ") & df["subject"].str.contains("dividend", case=False)].copy()
    df["ex"] = pd.to_datetime(df["exDate"], format="%d-%b-%Y", errors="coerce")
    df["amount"] = [parse_amount(s, f) for s, f in zip(df["subject"], df["faceVal"])]
    df["revised"] = df["subject"].str.contains("revised", case=False)
    df = df.dropna(subset=["ex"])
    out = []
    for (sym, ex), g in df.groupby(["symbol", "ex"]):
        if g["revised"].any():
            g = g[g["revised"]]
        g = g.drop_duplicates(["subject"])
        amt = g["amount"].sum(min_count=1)
        out.append(dict(symbol=sym, isin=g["isin"].iloc[0], ex=ex, amount=amt,
                        subject=" | ".join(g["subject"]), unparsed=g["amount"].isna().any()))
    return pd.DataFrame(out)


def dividend_panel(P, ann=None):
    """dates x names DataFrame of dividend cash per back-adjusted share, on panel ex-dates."""
    from .bhav_panel import build, parse_all, stitch_renames
    ann = load_announcements() if ann is None else ann
    b = build()
    long = parse_all()
    long = long[long["isin"].astype(str).str.startswith("INE")]
    long, _ = stitch_renames(long)
    key = long[["date", "sym", "id"]].drop_duplicates(["date", "sym"]).sort_values("date")
    dates = P.dates
    ann = ann.dropna(subset=["amount"])
    ann = ann[ann["amount"] > 0]
    pos = np.searchsorted(dates.values, ann["ex"].values)          # first trading day >= ex-date
    ann = ann.assign(t=pos)[pos < len(dates)]
    ann["date"] = dates[ann["t"].values]
    # symbol -> id as traded on (or just before) the ex-date
    k = pd.merge_asof(ann.sort_values("date"), key.rename(columns={"sym": "symbol"}),
                      on="date", by="symbol", direction="backward")
    k = k.dropna(subset=["id"])
    k = k[k["id"].isin(P.names)]
    f = b["factor"].reindex(index=dates, columns=P.names).fillna(1.0)
    mult = f[::-1].cumprod()[::-1].shift(-1).fillna(1.0)
    # NSE adjusts PREVCLOSE for extraordinary dividends (as it does for splits), so the price
    # factor already removes the drop; crediting cash as well would count the dividend twice.
    # Such events are recognised by f_t ~ 1 - D / raw previous close. Yields above 60% with no
    # matching factor are parse errors (e.g. "Rs.0125") and are dropped.
    raw_prev = b["raw_close"].reindex(columns=P.names).ffill().shift(1).reindex(dates)
    k = k.copy()
    k["factor"] = [f.at[d, i] for d, i in zip(k["date"], k["id"])]
    k["raw_yield"] = [a / raw_prev.at[d, i] if raw_prev.at[d, i] > 0 else np.nan
                      for a, d, i in zip(k["amount"], k["date"], k["id"])]
    drop_f = 1 - k["factor"]
    k["in_price_factor"] = (k["factor"] < 0.995) & (k["raw_yield"] > 0.02) & \
        ((k["raw_yield"] - drop_f).abs() < 0.25 * drop_f)
    k["implausible"] = ~k["in_price_factor"] & ~(k["raw_yield"] < 0.6)
    k["credited"] = ~k["in_price_factor"] & ~k["implausible"]
    D = pd.DataFrame(0.0, index=dates, columns=P.names)
    for _, r in k[k["credited"]].iterrows():
        D.at[r["date"], r["id"]] += r["amount"] * mult.at[r["date"], r["id"]]
    return D, k
