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

## Stops executed intraday like real stop orders (rules `SPEC_INTRADAY.md`; `intraday_metrics.csv`)

Value-based simulator, pre-tax, all cash costs; fills at the stop price when the day's low reaches it, at the open on a gap
below it, none while locked at the lower circuit. Pass bar: drawdown at least 20% smaller than this simulator's base
(-36.4% -> -29.1% or better) and Sharpe at least 1.37.

| Book | CAGR | Sharpe | Max DD | Stops | Filled at a gap open | Days blocked at lower circuit |
|---|---|---|---|---|---|---|
| Base (no stop), this simulator | 25.3% | 1.42 | -36.4% | | | |
| Fixed 15% | 29.1% | 1.53 | -32.7% | 218 | 26 | 5 |
| Trailing 15% | 23.0% | 1.30 | -33.6% | 981 | 102 | 17 |
| **Climbing pins m=2, rest** | **24.0%** | **1.40** | **-27.3%** | 377 | 44 | 3 |
| Climbing pins m=2, reinvest | 21.9% | 1.24 | -32.3% | 445 | 49 | 5 |

**Climbing pins with rest: Pass** (drawdown 25% smaller, Sharpe 1.40 vs 1.42). **Fixed 15%:** more return and a higher
Sharpe, but the drawdown is only 10% smaller (fails the drawdown bar). Trailing and climb-reinvest: fail.

Why this differs from the close-based tests: a resting order sells during the day at the trigger instead of waiting
for the next open, which avoids the overnight continuation of a falling stock. About 1 in 8 stops still filled
below the trigger at a gap open, and a few were blocked at the lower circuit.

Caveats: a new simulator (pre-tax, fractional shares, no weight trimming); its base differs from `backtest.run`'s
(25.3% pre-tax, -36.4% vs 26.7% post-tax, -31.8%), so only comparisons within this table are like for like. Only m = 2 was
pre-declared; m = 1.5 and 3 are untested here. Fills at exactly the trigger assume a liquid market in the stock.

## Robustness of climbing stops with intraday execution (rules `SPEC_ROBUST.md`; `robust_metrics.csv`)

| Book | CAGR | Sharpe | Max DD | 2022-26 CAGR | Stops | vs bar |
|---|---|---|---|---|---|---|
| Pre-tax base | 25.3% | 1.42 | -36.4% | 25.7% | | bar: DD <= -29.1%, Sharpe >= 1.37 |
| Pre-tax climb m=1.5, rest | 17.2% | 1.12 | -28.3% | 9.0% | 596 | **fail** (Sharpe) |
| Pre-tax climb m=2, rest | 24.0% | 1.40 | -27.3% | 22.9% | 377 | pass (earlier run) |
| Pre-tax climb m=3, rest | 23.4% | 1.39 | -27.8% | 22.1% | 189 | **pass** |
| With tax: base | 22.0% | 1.24 | -37.2% | 20.3% | | bar: DD <= -29.8%, Sharpe >= 1.19 |
| **With tax: climb m=2, rest** | 20.8% | 1.20 | -29.6% | 19.3% | 377 | **pass** |
| With tax: climb m=1.5, rest (extra) | 15.2% | 0.98 | -28.4% | 7.7% | 592 | fail |
| With tax: climb m=3, rest (extra) | 21.6% | 1.26 | -29.0% | 22.9% | 189 | pass |

**Verdict: robust.** m = 2 passes with tax, and m = 3 passes pre-tax (and with tax). m = 1.5 fails: pins that tight
are hit by normal swings (596 stops) and cost 8 points a year. With slack of 2-3 times the stock's normal one-month
swing, the worst fall drops from about -37% to -29% for about 1 point of return a year.

Next: a candidate for the next exploratory paper account (earliest slot Jan 2027 under the 27 Nov safeguards). It needs
the paper engine to place and fill intraday stop orders (a code change to test before any amendment).

## Pessimistic stop fills (addendum to `SPEC_ROBUST.md`; `fill_metrics.csv`), m = 2, rest, with tax

| Fill assumption | CAGR | Sharpe | Max DD | vs bar (DD <= -29.8%, Sharpe >= 1.19) |
|---|---|---|---|---|
| Base, no stops | 22.0% | 1.24 | -37.2% | |
| At the trigger | 20.8% | 1.20 | -29.6% | pass |
| 1% below the trigger | 19.7% | 1.14 | -30.4% | **fail** (both, narrowly) |
| Halfway to the day's low | 19.6% | 1.13 | -30.3% | **fail** (both, narrowly) |

The drawdown cut survives worse fills (about -37% -> -30%), but its price rises from about 1 to about 2.3 points of
return a year, and the result no longer clears the pre-set bar. **The verdict depends on real fill quality**, which daily
data cannot settle: it needs intraday data or real stop orders. Upgrade "robust" above to "promising, fill-sensitive".
