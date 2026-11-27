# Known issues

## 1. Weekend special sessions are treated as corporate actions (found 27 Nov 2026; FIXED 27 Nov 2026)

**Fixed** in `alpha/bhav_panel.py` (fix (b), market-wide rule), see the "Fix, 27 Nov 2026 (data)" entry in PREREGISTRATION.md.

`data_download_bhav.py` downloads weekdays only, so special weekend sessions (Budget days on a weekend, Diwali Muhurat
trading, exchange test sessions) are missing. The next weekday's bhavcopy carries that session's close as PREVCLOSE, so
`alpha/bhav_panel.py` sees PREVCLOSE / last close != 1 for most stocks and records a "corporate-action factor"
(any mismatch of 0.5% or more).

Effects:
- **Research panel:** that session's price move is removed from back-adjusted prices (a handful of days since 2011,
  e.g. 2 Mar 2015, 3 Feb 2020, 29 Oct 2019, 21 May 2024, 2 Feb 2026). Small effect on backtests.
- **Live paper trader (`alpha/paper_trade.py`, step 1b):** share counts of holdings are divided by that factor. On
  9 Nov 2026 (after Muhurat trading on Sunday 8 Nov) 77% of stocks showed a mismatch of 0.5% or more; the primary's
  holdings were small enough that rounding left every count unchanged (checked against its state on 6 and 9 Nov),
  and the Rs 10L accounts started on 16 Nov. **No live damage so far**, but a future weekend session would wrongly
  change share counts in the larger accounts.

Possible fixes (Sunny to decide; a fix to trading code is a separate dated commit, per PREREGISTRATION.md):
(a) download every calendar day (non-trading days return 404 and are skipped), so weekend sessions are ordinary
trading days; or (b) only accept a factor that is confirmed by an NSE corporate-action record or is a large split-like
jump. Next known risk date: any weekend special session announced by NSE.
