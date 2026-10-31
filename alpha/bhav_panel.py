"""Survivorship-free panel from NSE bhavcopy (every listed stock, every day, 2010 onward).

Universe ("Liquid 500"): at each month-end, the 500 EQ-series stocks with the highest 60-day
median traded value (price >= Rs 20, >= 250 trading days of history, >= 40 trading days in the
last 60) become the members for the next month. Stocks later delisted, suspended or merged are
included for as long as they traded, so no future information decides who is in the universe.

Prices: NSE adjusts PREVCLOSE on corporate-action ex-dates (splits, bonuses, rights), so
f_t = PREVCLOSE_t / CLOSE_(t-1) is the adjustment factor; prices are back-adjusted by the product
of later factors. Ordinary dividends are not in bhavcopy, so returns here are price returns
(about 1-1.5% a year below total return for this universe; all strategies are affected alike).

Symbol renames are stitched by ISIN: when a symbol stops and a new symbol starts within 5 trading
days carrying the same ISIN, they are treated as one stock.
"""
import glob, io, os, zipfile
import numpy as np, pandas as pd

OLD = {"SYMBOL": "sym", "SERIES": "ser", "OPEN": "open", "HIGH": "high", "LOW": "low", "CLOSE": "close",
       "PREVCLOSE": "prev", "TOTTRDQTY": "vol", "TOTTRDVAL": "val", "ISIN": "isin"}
NEW = {"TckrSymb": "sym", "SctySrs": "ser", "OpnPric": "open", "HghPric": "high", "LwPric": "low",
       "ClsPric": "close", "PrvsClsgPric": "prev", "TtlTradgVol": "vol", "TtlTrfVal": "val", "ISIN": "isin"}


def parse_all(folder="data/bhav/raw", out="data/bhav/long.pkl"):
    if os.path.exists(out):
        return pd.read_pickle(out)
    frames = []
    for f in sorted(glob.glob(f"{folder}/*.zip")):
        d = pd.Timestamp(os.path.basename(f)[:8])
        with zipfile.ZipFile(f) as z:
            df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
        df.columns = [c.strip() for c in df.columns]
        m = OLD if "SYMBOL" in df.columns else NEW
        df = df[[c for c in m if c in df.columns]].rename(columns=m)
        df = df[df["ser"].astype(str).str.strip() == "EQ"].drop(columns="ser")
        df["date"] = d
        frames.append(df)
    long = pd.concat(frames, ignore_index=True)
    long["sym"] = long["sym"].astype(str).str.strip()
    long.to_pickle(out)
    return long


def stitch_renames(long):
    """Map renamed symbols onto one id using ISIN continuity."""
    first = long.groupby("sym")["date"].min(); last = long.groupby("sym")["date"].max()
    isin_first = long.sort_values("date").groupby("sym")["isin"].first()
    isin_last = long.sort_values("date").groupby("sym")["isin"].last()
    days = np.sort(long["date"].unique()); pos = {d: i for i, d in enumerate(days)}
    by_isin_first = {}
    for s, i in isin_first.items():
        by_isin_first.setdefault(i, []).append(s)
    parent = {}
    for s, i in isin_last.items():
        for t in by_isin_first.get(i, []):
            if t != s and 0 < pos[first[t]] - pos[last[s]] <= 5:
                parent[t] = s
    def root(s):
        while s in parent: s = parent[s]
        return s
    long = long.copy()
    long["id"] = long["sym"].map(lambda s: root(s))
    return long, len(parent)


def build(cache="data/bhav/panel.pkl", n_univ=500):
    if os.path.exists(cache):
        return pd.read_pickle(cache)
    long = parse_all()
    long = long[long["isin"].astype(str).str.startswith("INE")]       # company shares only (drops ETFs, INF*)
    long, n_renames = stitch_renames(long)
    long = long.sort_values(["id", "date"]).drop_duplicates(["id", "date"], keep="last")
    wide = {k: long.pivot(index="date", columns="id", values=k) for k in ("open", "high", "low", "close", "prev", "vol", "val")}
    close = wide["close"]
    # corporate-action factors: f_t = prev_t / last traded close before t
    last_close = close.ffill().shift(1)
    f = (wide["prev"] / last_close).where(close.notna())
    f = f.where((f > 0.01) & (f < 100)).fillna(1.0)
    f[(f - 1).abs() < 0.005] = 1.0                           # rounding noise is not an action
    # Older bhavcopies do not always adjust PREVCLOSE (e.g. TITAN's 2011 split shows factor 1).
    # NSE price bands cap genuine one-day moves well below 35% for almost all stocks, so an
    # overnight gap beyond 35% with no recorded factor is treated as an unrecorded corporate
    # action: the factor becomes open_t / last close, i.e. the gap itself is removed.
    gap = wide["open"] / last_close
    unrec = (f == 1.0) & ((gap < 0.65) | (gap > 1.0 / 0.65)) & gap.notna()
    f = f.mask(unrec, gap)
    n_unrec = int(unrec.sum().sum())
    mult = f[::-1].cumprod()[::-1].shift(-1).fillna(1.0)     # product of factors after t
    adj = {k: wide[k] * mult for k in ("open", "high", "low", "close")}
    # liquidity universe, decided at each month-end for the following month
    tv = (wide["val"]).rolling(60, min_periods=40).median() / 1e7      # Rs crore
    hist = close.notna().cumsum()
    elig = (close.ffill() >= 20) & (hist >= 250) & tv.notna()
    month_end = close.index.to_series().groupby(close.index.to_period("M")).max()
    member = pd.DataFrame(False, index=close.index, columns=close.columns)
    me_list = list(month_end.values)
    for k, d in enumerate(me_list):
        row = tv.loc[d].where(elig.loc[d])
        top = row.dropna().nlargest(n_univ).index
        nxt = me_list[k + 1] if k + 1 < len(me_list) else close.index[-1] + pd.Timedelta(days=1)
        span = (close.index > d) & (close.index <= nxt)
        member.loc[span, top] = True
    ever = member.any()
    keep = ever[ever].index
    out = dict(adj={k: v[keep] for k, v in adj.items()}, raw_close=close[keep], raw_open=wide["open"][keep],
               vol=wide["vol"][keep], tv=tv[keep], member=member[keep], factor=f[keep],
               n_renames=n_renames, n_ever=len(keep), n_unrecorded_actions=n_unrec)
    pd.to_pickle(out, cache)
    return out


class BhavPanel:
    """Same interface as alpha.panel.Panel, built from bhavcopy with a point-in-time universe."""
    def __init__(self, min_tv_cr=5.0, min_price=20.0):
        from .panel import SPLITS
        self.SPLITS = SPLITS
        b = build()
        o, h, l, c = (b["adj"][k] for k in ("open", "high", "low", "close"))
        v = b["vol"].where(b["vol"] > 0)
        bad = (b["raw_open"] <= 0) | o.isna() | v.isna()
        o, h, l, c, v = (x.mask(bad) for x in (o, h, l, c, v))
        self.dates, self.names = c.index, list(c.columns)
        self.feat = {"open": o.values, "high": h.values, "low": l.values, "close": c.values,
                     "volume": v.values, "vwap": ((h + l + c) / 3).values,
                     "ret": (c / c.ffill().shift(1) - 1).where(c.notna()).values}
        to = np.log(o)
        self.target = (to.shift(-2) - to.shift(-1)).values
        self.targets = {hh: (to.shift(-1 - hh) - to.shift(-1)).values for hh in (1, 5, 20)}
        tv = b["tv"]
        self.spread = np.select([tv.values >= 100, tv.values >= 20, tv.values >= 5], [5e-4, 1e-3, 2e-3], 4e-3)
        self.mask = (b["member"] & (tv >= min_tv_cr) & (b["raw_close"] >= min_price) & c.notna()).values
        # engine prices are the back-adjusted series (share counts are in adjusted units)
        self.raw_close, self.raw_open, self.raw_volume = c, o, v
        self.adj = c
        self.n_renames, self.n_ever = b["n_renames"], b["n_ever"]
        self.n_unrecorded_actions = b.get("n_unrecorded_actions")

    def idx(self, split):
        a, z = self.SPLITS[split]
        return np.where((self.dates >= a) & (self.dates <= z))[0]

    def report(self):
        m = pd.Series(self.mask.sum(1), index=self.dates)
        return {k: int(m.iloc[self.idx(k)].median()) for k in self.SPLITS}


class BhavMarket:
    """Engine-facing market (same attributes as market.Market) on the bhavcopy panel."""
    def __init__(self, P):
        import bottleneck as bn
        self.names, self.dates, self.n = P.names, P.dates, len(P.names)
        self.open = P.raw_open
        self.close = P.raw_close.ffill()
        self.volume = P.raw_volume
        self.tradable = P.raw_open.notna() & (P.raw_volume > 0)
        self.div = pd.DataFrame(0.0, index=P.dates, columns=P.names)
        r = np.log(self.close).diff()
        self.sigma = np.sqrt((r ** 2).ewm(span=20, min_periods=10).mean())
        self.medvol = self.volume.rolling(20, min_periods=10).median()
        self.spread = pd.DataFrame(np.maximum(P.spread, 0.05 / self.close.values), index=P.dates, columns=P.names)
        self.adj_factor = pd.DataFrame(1.0, index=P.dates, columns=P.names)
        self.index_close = None
        last = P.raw_close.apply(lambda s: s.last_valid_index())
        pos = {d: i for i, d in enumerate(P.dates)}
        # last trading day per stock, unless it is still trading at the end of the data
        self.delist_day = np.array([pos[d] if d is not None and d < P.dates[-5] else -1 for d in last])
