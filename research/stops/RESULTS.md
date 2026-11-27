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

## Climbing-protection stops (rules `SPEC_CLIMB.md`; `climb_metrics.csv`)

| Book | CAGR | Sharpe | Max DD | 2022-26 CAGR | Turnover/yr | Stops |
|---|---|---|---|---|---|---|
| Base (no stop) | 26.7% | 1.38 | -31.8% | 21.9% | 1.8 | |
| Climb m=1.5, rest | 21.4% | 1.34 | **-22.3%** | 18.2% | 2.8 | 458 |
| **Climb m=2, rest (judged)** | 21.4% | 1.30 | -26.9% | 20.3% | 2.4 | 294 |
| Climb m=3, rest | 21.2% | 1.32 | -24.7% | 20.1% | 1.9 | 141 |
| Climb m=1.5 / 2 / 3, reinvest | 23.5 / 23.4 / 26.6% | 1.26 / 1.26 / 1.42 | -35.9 / -32.3 / -31.5% | | | |
| *Diagnostic: base held at 80%, 20% cash, no stops* | 22.7% | 1.38 | -27.3% | | | |

**Verdict: Fail, narrowly.** At the judged setting (m = 2, rest) the drawdown is -26.9% (bar -25.6%) and Sharpe 1.30 (bar
1.33). m = 1.5 with rest would pass on its own (-22.3%, 1.34), but the judged setting does not.

What it shows: the protection comes from **resting in cash after a stop**, not from where the pins sit (the reinvest versions
do not cut drawdown). Resting costs about 5 points a year, and the result is close to simply keeping 20% in cash
(22.7% a year, Sharpe 1.38, -27.3%). The climbing rule trades a smaller drawdown for a lower return at about the same
risk-adjusted rate; it is not a free improvement.

## Bad-news exit (rules `SPEC_NEWS.md`; `news_exit_metrics.csv`)

Sell a holding that falls X% or more in a day while the market is calm (universe down less than 1%); no rebuy for 63 days.

| Book | CAGR | Sharpe | Max DD | Exits in 14 years |
|---|---|---|---|---|
| Base (no exit rule) | 26.72% | 1.382 | -31.8% | |
| Bad-news exit 10% | 26.49% | 1.363 | -33.2% | 27 |
| **Bad-news exit 15% (judged)** | **27.25%** | **1.409** | -30.2% | 14 |
| Bad-news exit 20% | 26.69% | 1.385 | -30.7% | 5 |

**Verdict: Fail, by a hair.** The judged 15% version meets the bar (more return and higher Sharpe than the base), but
the second setting must too: 20% matches Sharpe and misses CAGR by 0.03 points; 10% is slightly worse.

Reading: the rule does what it was meant to do, costing essentially nothing, but it matters little because
stock-specific crashes were rare among these holdings (14 exits in 14 years at 15%). The book's large drawdowns were
market-wide, which this rule deliberately ignores.
