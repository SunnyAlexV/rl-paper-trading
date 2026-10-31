"""Point-in-time market panel for the frozen 20-stock universe."""
import numpy as np, pandas as pd
from costs import abdi_ranaldo_spread

# Top 20 by median daily traded value 2010-2026 among Nifty 50 names listed for the whole sample
UNIVERSE = ["RELIANCE", "ICICIBANK", "SBIN", "INFY", "AXISBANK", "HDFCBANK", "TCS", "TATASTEEL",
            "MARUTI", "LT", "ITC", "BAJFINANCE", "BHARTIARTL", "KOTAKBANK", "SUNPHARMA",
            "HINDUNILVR", "HINDALCO", "M&M", "HCLTECH", "INDUSINDBK"]


class Market:
    def __init__(self, path="data/raw.pkl", universe=UNIVERSE, spread_tiers=False):
        raw = pd.read_pickle(path)
        raw = raw.loc[:, ~raw.columns.duplicated()]
        t = [u + ".NS" for u in universe]
        self.names = universe
        f = lambda k: raw[k][t].copy()
        self.open, self.high, self.low, self.close = f("Open"), f("High"), f("Low"), f("Close")
        self.adj, self.volume = f("Adj Close"), f("Volume").astype(float)
        self.div = f("Dividends").fillna(0.0)
        self.index_close = raw["Close"]["^NSEI"] if "^NSEI" in raw["Close"] else None
        # Data hygiene: a day is tradable for a stock only with a positive open and volume
        bad = (self.open <= 0) | self.open.isna() | (self.volume <= 0) | self.close.isna()
        self.tradable = ~bad
        self.close = self.close.ffill()
        self.adj = self.adj.ffill()
        self.dates = self.close.index
        # Point-in-time risk/liquidity estimates, known at each close
        r = np.log(self.adj).diff()
        self.sigma = np.sqrt((r ** 2).ewm(span=20, min_periods=10).mean())
        self.medvol = self.volume.where(self.volume > 0).rolling(20, min_periods=10).median()
        # Stage 0 named the Abdi-Ranaldo estimator, but on these mega-caps it returns zero on about
        # half of stock-days and swings 0-38 bp (see data_report / notebook check), so it is unusable.
        # Amended assumption: relative spread = max(5 bp, one Rs 0.05 tick / price), stressed at 2x.
        self.spread_ar = abdi_ranaldo_spread(self.high, self.low, self.close)
        self.spread = np.maximum(5e-4, 0.05 / self.close)
        if spread_tiers:
            # Nifty 500 mid/small caps: wider spreads by 60-day median traded value (Rs crore),
            # an assumption (no free NSE quote data): >=100: 5 bp, 20-100: 10 bp, 5-20: 20 bp, <5: 40 bp
            tv = (self.close * self.volume).rolling(60, min_periods=20).median() / 1e7
            tier = np.select([tv >= 100, tv >= 20, tv >= 5], [5e-4, 1e-3, 2e-3], 4e-3)
            self.spread = np.maximum(pd.DataFrame(tier, index=tv.index, columns=tv.columns), self.spread)
        self.adj_factor = self.adj / self.close          # converts raw opens to total-return opens
        self.n = len(universe)

    def data_report(self):
        r = np.log(self.adj).diff()
        return dict(
            days=len(self.dates), start=str(self.dates[0].date()), end=str(self.dates[-1].date()),
            untradable_stock_days=int((~self.tradable).sum().sum()),
            abs_daily_ret_gt_20pct=int((r.abs() > 0.20).sum().sum()),
            median_spread_bp=float((self.spread.median().median()) * 1e4),
        )
