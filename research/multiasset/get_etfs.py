"""Extract ETF rows (gold, gilt, liquid, index) from the raw NSE bhavcopy zips -> data/etf_raw.pkl.
Run from the history working copy."""
import zipfile, glob, os, pandas as pd
WANT = ["GOLDBEES", "NIFTYBEES", "LIQUIDBEES", "SETF10GILT", "LTGILTBEES", "GILT5YBEES", "JUNIORBEES", "BANKBEES",
        "SILVERBEES", "LIQUIDETF", "LIQUIDCASE", "LIQUIDIETF", "GOLDIETF", "MON100", "N100", "HNGSNGBEES"]
out = []
for f in sorted(glob.glob("data/bhav/raw/*.zip")):
    d = os.path.basename(f)[:8]
    try:
        z = zipfile.ZipFile(f); df = pd.read_csv(z.open(z.namelist()[0]))
    except Exception:
        continue
    df.columns = [c.strip() for c in df.columns]
    if "SYMBOL" in df.columns:
        cols = dict(sym="SYMBOL", series="SERIES", open="OPEN", high="HIGH", low="LOW", close="CLOSE", prev="PREVCLOSE", val="TOTTRDVAL")
    else:
        cols = dict(sym="TckrSymb", series="SctySrs", open="OpnPric", high="HghPric", low="LwPric", close="ClsPric", prev="PrvsClsgPric", val="TtlTrfVal")
    df["_s"] = df[cols["sym"]].astype(str).str.strip()
    x = df[df["_s"].isin(WANT)]
    for _, rw in x.iterrows():
        out.append(dict(date=pd.Timestamp(d), sym=rw["_s"], series=str(rw[cols["series"]]).strip(),
                        **{k: rw[v] for k, v in cols.items() if k not in ("sym", "series")}))
E = pd.DataFrame(out); E.to_pickle("data/etf_raw.pkl")
print(E.groupby("sym").agg(first=("date", "min"), last=("date", "max"), days=("date", "nunique"),
                           series=("series", lambda v: ",".join(sorted(set(v))))).sort_values("first").to_string())
