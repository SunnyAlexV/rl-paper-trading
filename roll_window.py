"""Keep only the most recent WINDOW trading days of raw data in the repo (enough for every
feature, the 60-day liquidity ranks and the 250-day history rule), so the repo stays small."""
import glob, os
WINDOW = 500
for folder, ext in (("data/bhav/raw", "zip"), ("data/deliv", "csv"), ("data/fo", "csv")):
    files = sorted(glob.glob(f"{folder}/*.{ext}"))
    for f in files[:-WINDOW]:
        os.remove(f)
    print(folder, min(len(files), WINDOW), "days kept")
