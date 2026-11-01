# Dividends in the backtest (1 Nov 2026)

`data_download_corpact_full.py` downloads NSE corporate actions for 2012 onwards, one month per request.
`alpha/dividends.py` parses the cash dividend from each announcement and aligns it to the panel.
The results are 13,684 dividend events on panel stocks; 5 were already priced in by NSE's PREVCLOSE
adjustment and 1 was an implausible parse ("Rs.0125"). Amounts match Yahoo exactly for ITC,
COALINDIA, TCS and HINDZINC (2019-26). HDFCBANK is 2x Yahoo, as expected: Yahoo back-adjusts for
the 2025 1:1 bonus.

`div_eval.py` runs in the research repository, whose `BhavMarket(P, dividends=True)` loads the
panel. The results are in `div_eval.csv` (post-tax, band rule, Rs 1,00,000, all costs) and
`dividends_matched.csv` (every matched event and how it was treated).
