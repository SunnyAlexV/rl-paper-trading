# Stop-losses on momentum + delivery: results (27 Nov 2026)

Rules: `SPEC.md` (committed before the run). Rs 10L, Stage 2 (all fees, post-tax), Jul 2012 - Nov 2026 (`stops_metrics.csv`).
Pass bar: max drawdown -25.6% or better **and** Sharpe >= 1.33, at the 15% setting and one other.

| Book | CAGR | Sharpe | Max DD | 2022-26 CAGR | Turnover/yr | Stop events |
|---|---|---|---|---|---|---|
| Base (no stop) | 26.7% | 1.38 | -31.8% | 21.9% | 1.8 | |
| Fixed 10% / **15%** / 20% | 26.3 / **27.1** / 27.3% | 1.40 / **1.44** / 1.43 | -30.9 / **-33.4** / -34.1% | 23.7 / 22.8 / 25.7% | 2.5 / 2.2 / 1.8 | 285 / 159 / 90 |
| Trailing 10% / **15%** / 20% | 17.3 / **25.2** / 23.1% | 1.01 / **1.35** / 1.27 | -34.7 / **-36.9** / -32.8% | 12.5 / 18.0 / 17.5% | 6.4 / 3.6 / 2.6 | 1,577 / 717 / 380 |
| Portfolio 10% / **15%** / 20% | 23.1 / **26.0** / 25.8% | 1.35 / **1.44** / 1.39 | -27.2 / **-28.4** / -29.3% | 15.4 / 21.1 / 22.4% | 2.3 / 2.0 / 1.9 | 19 / 8 / 5 |

**Verdict: no stop passes.** None cut the maximum drawdown by 20%.
- **Fixed stops** did not reduce drawdown (slightly worse at 15-20%), though they nudged Sharpe up (1.44 at 15%).
- **Trailing stops** hurt: they sold strong stocks on normal pullbacks (717 stop events over the period at 15%, 1,577 at 10%), raising
  turnover and lowering returns; drawdowns got worse.
- **Portfolio stops** helped a little: drawdown -31.8% -> -28.4% (11% better, short of the 20% bar) with Sharpe 1.44, but
  the 10% version cost 3.6 points a year (in-and-out whipsaw).

Why: the deepest falls were market-wide and fast (COVID: -32% in five weeks). Stock-level stops swap one falling
stock for another falling stock, so the book stays fully invested; a portfolio stop reacts only after most of the
fall has happened, and overnight gaps fill exits at the next open.
