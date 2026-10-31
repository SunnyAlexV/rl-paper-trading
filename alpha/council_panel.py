"""Council panel: the Stage 4 point-in-time universe plus the extra data each researcher sees.

Added inputs (all known at the close of day t):
  value       traded value, Rs (split-invariant; preferred to share volume)
  volume      share volume adjusted for splits/bonuses (raw volume / adjustment multiplier),
              fixing the Stage 4 artefact where a split made a stock look "high volume"
  deliv_pct   deliverable quantity / traded quantity (NSE security-wise delivery files)
  deliv_val   deliverable value, Rs
  basis       nearest stock-future close / spot close - 1   (F&O stocks only)
  oi_chg      change in total stock-futures open interest / open interest
  pcr         put open interest / call open interest (stock options)
  fut_oi_val  futures open interest x spot price, Rs
Non-F&O stocks have no derivatives data; their values are missing and rank as neutral.
"""
import glob, os
import numpy as np, pandas as pd
from .bhav_panel import BhavPanel, build, parse_all, stitch_renames

RESEARCHERS = {
    "pricevol": ["open", "high", "low", "close", "volume", "vwap", "ret", "value"],
    "delivery": ["close", "ret", "value", "deliv_pct", "deliv_val"],
    "derivs": ["close", "ret", "value", "basis", "oi_chg", "pcr", "fut_oi_val"],
}


def _daily(folder, cols):
    cache = f"{folder}.pkl"
    if os.path.exists(cache):
        return pd.read_pickle(cache)
    fr = []
    for f in sorted(glob.glob(f"{folder}/*.csv")):
        df = pd.read_csv(f)
        if len(df):
            df["date"] = pd.Timestamp(os.path.basename(f)[:8]); fr.append(df)
    out = pd.concat(fr, ignore_index=True)
    out.to_pickle(cache)
    return out


CACHE = "data/council_cache.pkl"


class CouncilPanel(BhavPanel):
    """Built once and cached: building it needs ~3 GB, so two parallel builds exhaust the
    machine's memory (this killed the first real-market researcher runs)."""
    def __init__(self, **kw):
        if os.path.exists(CACHE):
            self.__dict__.update(pd.read_pickle(CACHE))
            return
        super().__init__(**kw)
        self._build()
        pd.to_pickle({k: v for k, v in self.__dict__.items()}, CACHE)

    def _build(self):
        b = build()
        long = parse_all()
        long = long[long["isin"].astype(str).str.startswith("INE")]
        long, _ = stitch_renames(long)
        key = long[["date", "sym", "id"]].drop_duplicates(["date", "sym"])
        idx, cols = self.dates, self.names
        f = b["factor"]
        mult = f[::-1].cumprod()[::-1].shift(-1).fillna(1.0)[cols]
        # build()["raw_close"] is the unadjusted close; adjusted prices live in build()["adj"]
        spot_raw = b["raw_close"][cols]
        vol_raw = b["vol"][cols]
        self.feat["volume"] = (vol_raw / mult).where(vol_raw > 0).values
        val = (spot_raw * vol_raw).where(vol_raw > 0)
        self.feat["value"] = val.values

        def to_wide(df, field):
            d = df.merge(key, left_on=["date", "symbol"], right_on=["date", "sym"], how="inner")
            w = d.pivot_table(index="date", columns="id", values=field, aggfunc="last")
            return w.reindex(index=idx, columns=cols)

        dl = _daily("data/deliv", None)
        tq, dq = to_wide(dl, "traded_qty"), to_wide(dl, "deliv_qty")
        self.feat["deliv_pct"] = (dq / tq).where(tq > 0).values
        self.feat["deliv_val"] = (dq * spot_raw).values
        fo = _daily("data/fo", None)
        fc, oi, doi = to_wide(fo, "fut_close"), to_wide(fo, "fut_oi"), to_wide(fo, "fut_oi_chg")
        co, po = to_wide(fo, "call_oi"), to_wide(fo, "put_oi")
        self.feat["basis"] = (fc / spot_raw - 1).where((fc > 0) & (spot_raw > 0)).values
        self.feat["oi_chg"] = (doi / oi).where(oi > 0).values
        self.feat["pcr"] = (po / co).where(co > 0).values
        self.feat["fut_oi_val"] = (oi * spot_raw).where(oi > 0).values
        self.coverage = {k: float(np.isfinite(self.feat[k])[self.mask].mean()) for k in
                         ("deliv_pct", "basis", "oi_chg", "pcr")}
