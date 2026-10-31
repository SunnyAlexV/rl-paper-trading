"""Daily event-driven backtester for NSE cash equity delivery, long-only, all frictions.

Timeline for each trading day d:
  1. If d starts a new financial year, pay last FY's capital gains tax in cash.
  2. At d's open, execute the target weights decided at d-1's close:
       sells first (FIFO lots, explicit + implicit costs), then buys limited by cash.
  3. Credit dividends going ex on d to shares held before today's trades (taxed at 31.2%).
  4. Mark to close; record pre-tax NAV and post-tax NAV (NAV minus accrued FY tax).
  5. Ask the strategy for target weights using information up to d's close.
"""
from dataclasses import dataclass, field
import numpy as np, pandas as pd
from costs import explicit_costs, implicit_cost_frac, ZERODHA
from tax import TaxBook, fy_of

DIV_TAX = 0.30 * 1.04


@dataclass
class Config:
    capital: float = 100_000.0
    start: str = "2013-01-01"
    end: str = None
    max_weight: float = 0.20
    participation: float = 0.10
    impact_Y: float = 1.0
    implicit_mult: float = 1.0     # 2.0 for the stress test
    tax: bool = True
    fees: object = ZERODHA
    # Skip top-ups and trims smaller than this fraction of NAV on positions that stay open
    # (new entries and full exits always trade). 0 reproduces Stages 1-5, where every decision
    # re-targeted all holdings and generated many tiny trades.
    min_trade_frac: float = 0.0


@dataclass
class Result:
    nav: pd.Series
    nav_post_tax: pd.Series
    costs: dict
    turnover: float
    trades: int
    taxes_paid: list = field(default_factory=list)
    weights: pd.DataFrame = None


def run(market, strategy, cfg: Config):
    m = market
    dates = m.dates[(m.dates >= cfg.start) & ((m.dates <= cfg.end) if cfg.end else True)]
    loc = {d: i for i, d in enumerate(m.dates)}
    O, C = m.open.values, np.nan_to_num(m.close.values)   # unlisted days: price 0, never held
    TR = m.tradable.values
    SIG, SPR, MV = m.sigma.values, m.spread.values, m.medvol.values
    DIV = m.div.values
    n = m.n

    shares = np.zeros(n, dtype=np.int64)
    cash = cfg.capital
    book = TaxBook(n, enabled=cfg.tax)
    acc = dict(stt=0.0, exch_sebi_gst=0.0, stamp=0.0, dp=0.0, spread=0.0, impact=0.0,
               div_tax=0.0, cg_tax=0.0, dividends=0.0)
    traded_value = 0.0
    n_trades = 0
    target = None
    pending = None              # share targets still being worked (participation cap / halts)
    nav, navpt, wrec = [], [], []
    cur_fy = fy_of(dates[0])
    strategy.reset(m)

    for d in dates:
        t = loc[d]
        # 1. tax payment at FY boundary
        fy = fy_of(d)
        if fy != cur_fy:
            tax = book.close_year(cur_fy)
            cash -= tax
            acc["cg_tax"] += tax
            cur_fy = fy
        # 1b. delisted / permanently suspended stocks (bhavcopy universe only): exit at the last
        #     traded close with normal sell costs. An assumption: real delisting exits can be worse.
        DL = getattr(m, "delist_day", None)
        if DL is not None and t > 0:
            for i in np.where((DL == t - 1) & (shares > 0))[0]:
                q = shares[i]; px = C[t - 1, i] * (1 - SPR[t - 1, i] / 2 * cfg.implicit_mult)
                val = q * px
                ec = explicit_costs(val, "sell", cfg.fees)
                cash += val - ec["total"]; _acc_explicit(acc, ec)
                acc["spread"] += q * C[t - 1, i] * SPR[t - 1, i] / 2 * cfg.implicit_mult
                book.sell(i, d, q, px); shares[i] = 0
                traded_value += val; n_trades += 1
        held_before = shares.copy()

        # 2. execute yesterday's decision at today's open
        if (target is not None or pending is not None) and t > 0:
            p = O[t]
            ok = TR[t] & np.isfinite(p) & np.isfinite(MV[t - 1])
            mark = np.where(ok, p, C[t - 1])
            nav_open = cash + (shares * mark).sum()
            if target is not None:      # a fresh decision replaces any unfinished order
                want = np.floor(target * nav_open / np.where(ok, p, 1.0)).astype(np.int64)
            else:                       # keep working the unfilled remainder of the last order
                want = pending
            pending = want.copy()
            want = np.where(ok, want, shares)
            delta = (want - shares).astype(np.int64)
            cap = np.floor(cfg.participation * np.nan_to_num(MV[t - 1])).astype(np.int64)
            delta = np.clip(delta, -cap, cap)
            delta = np.where(ok, delta, 0)
            if cfg.min_trade_frac > 0:
                tiny = (delta != 0) & (want != 0) & (shares != 0) & \
                       (np.abs(delta) * np.where(ok, p, 0) < cfg.min_trade_frac * nav_open)
                delta = np.where(tiny, 0, delta)
                if pending is not None:
                    pending = np.where(tiny, shares, pending)

            def frac(q, idx):
                base = implicit_cost_frac(q, SPR[t - 1, idx], SIG[t - 1, idx], MV[t - 1, idx], cfg.impact_Y)
                return np.nan_to_num(base) * cfg.implicit_mult

            # sells
            for i in np.where(delta < 0)[0]:
                q = -delta[i]
                q = min(q, shares[i])
                if q <= 0:
                    continue
                f = frac(np.array([q]), np.array([i]))[0]
                half = SPR[t - 1, i] / 2 * cfg.implicit_mult
                fill = p[i] * (1 - f)
                val = q * fill
                ec = explicit_costs(val, "sell", cfg.fees)
                cash += val - ec["total"]
                acc["spread"] += q * p[i] * half
                acc["impact"] += q * p[i] * (f - half)
                _acc_explicit(acc, ec)
                book.sell(i, d, q, fill)
                shares[i] -= q
                traded_value += val
                n_trades += 1

            # buys, scaled to available cash
            buys = np.where(delta > 0)[0]
            if len(buys):
                q = delta[buys].astype(float)
                for _ in range(20):
                    qi = np.floor(q).astype(np.int64)
                    f = frac(qi, buys)
                    fills = p[buys] * (1 + f)
                    need = sum(qi[k] * fills[k] + explicit_costs(qi[k] * fills[k], "buy", cfg.fees)["total"]
                               for k in range(len(buys)))
                    if need <= cash or qi.sum() == 0:
                        break
                    q = q * min(0.999, cash / need)
                for k, i in enumerate(buys):
                    if qi[k] <= 0:
                        continue
                    val = qi[k] * fills[k]
                    ec = explicit_costs(val, "buy", cfg.fees)
                    cash -= val + ec["total"]
                    half = SPR[t - 1, i] / 2 * cfg.implicit_mult
                    acc["spread"] += qi[k] * p[i] * half
                    acc["impact"] += qi[k] * p[i] * (f[k] - half)
                    _acc_explicit(acc, ec)
                    book.buy(i, d, qi[k], fills[k])
                    shares[i] += qi[k]
                    traded_value += val
                    n_trades += 1

            if np.array_equal(shares, pending):
                pending = None
        # 3. dividends (ex-date: holders at previous close)
        dv = held_before * DIV[t]
        if dv.sum() > 0:
            gross = dv.sum()
            acc["dividends"] += gross
            acc["div_tax"] += gross * DIV_TAX if cfg.tax else 0.0
            cash += gross * (1 - (DIV_TAX if cfg.tax else 0.0))

        # 4. mark to close
        v = cash + (shares * C[t]).sum()
        nav.append(v)
        navpt.append(v - book.accrued(cur_fy))
        wrec.append(shares * C[t] / v)

        # 5. decide tomorrow
        w = strategy.decide(t, dict(weights=shares * C[t] / v, shares=shares.copy(), cash=cash, nav=v))
        if w is not None:
            w = np.clip(np.nan_to_num(w), 0, cfg.max_weight)
            if w.sum() > 1:
                w = w / w.sum()
        target = w

    nav = pd.Series(nav, index=dates)
    years = (dates[-1] - dates[0]).days / 365.25
    return Result(nav=nav, nav_post_tax=pd.Series(navpt, index=dates), costs=acc,
                  turnover=traded_value / nav.mean() / years / 2, trades=n_trades,
                  taxes_paid=book.paid, weights=pd.DataFrame(wrec, index=dates, columns=m.names))


def _acc_explicit(acc, ec):
    acc["stt"] += ec["stt"]
    acc["exch_sebi_gst"] += ec["exchange"] + ec["sebi"] + ec["gst"] + ec["brokerage"]
    acc["stamp"] += ec["stamp"]
    acc["dp"] += ec["dp"]


def metrics(nav, start=None, end=None):
    s = nav.loc[start:end]
    r = s.pct_change().dropna()
    yrs = (s.index[-1] - s.index[0]).days / 365.25
    cagr = (s.iloc[-1] / s.iloc[0]) ** (1 / yrs) - 1
    vol = r.std() * np.sqrt(252)
    dd = (s / s.cummax() - 1).min()
    var = r.quantile(0.05)
    cvar = r[r <= var].mean()
    return dict(CAGR=cagr, Vol=vol, Sharpe=r.mean() / r.std() * np.sqrt(252), MaxDD=dd, CVaR95=cvar)
