# Pods research: rebuilding the full NSE history

The trading repo keeps only a rolling 500-day window in `data/`. Pod research needs 2011 onwards, so
it runs in a separate working copy and never touches `data/` here.

```
mkdir -p /home/claude/history && cd /home/claude/rl-paper-trading
tar --exclude=.git --exclude='./paper*' -cf - . | (cd /home/claude/history && tar xf -)
cd /home/claude/history && rm -f data/*.pkl data/bhav/*.pkl
python3 -c "import pandas as pd; pd.DataFrame(index=pd.bdate_range('2011-01-03', pd.Timestamp.today())).to_pickle('data/raw.pkl')"
python3 -W ignore data_download_bhav.py        # ~6 min, ~3,900 days
python3 -W ignore data_download_council.py     # ~15 min (rerun until no 'ok' left)
python3 -W ignore research/pods/get_indices.py # ~6 min, all NSE index closes incl. India VIX
```

`data/raw.pkl` only supplies the calendar; holidays return 404 and are skipped. Building the
council panel takes ~40 s and ~1 GB. Index names change over time
(S&P CNX Nifty -> CNX Nifty -> Nifty 50; S&P CNX 500 -> CNX 500 -> Nifty 500); India VIX starts
May 2014, Midcap 150 / Smallcap 250 in Apr 2016.

Check of the 26 Nov 2026 rebuild against `research/momentum/` (18 Nov): monthly return correlation
0.961 (council), 0.971 (momentum), 0.997 (null). Single calendar years can differ by up to ~35 points
because a 20-stock book is path-dependent; see the robustness criterion in `SPEC.md`.
