"""Builds the design-review PDF. Text uses only characters available in the standard PDF fonts."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, Image,
                                PageBreak, KeepTogether, NextPageTemplate)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "NSE_paper_trading_design_review.pdf")
NAVY = colors.HexColor("#1f4e79"); GREY = colors.HexColor("#5f6b76"); LIGHT = colors.HexColor("#eef3f8")
LINE = colors.HexColor("#c9d3de"); GOOD = colors.HexColor("#2e7d32"); BAD = colors.HexColor("#b23b3b")

base = dict(fontName="Helvetica", fontSize=10.5, leading=14.5, textColor=colors.HexColor("#1d1d1d"))
S = {
    "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=26, leading=31, textColor=NAVY, spaceAfter=10),
    "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=13.5, leading=18, textColor=GREY, spaceAfter=24),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=16, leading=20, textColor=NAVY, spaceBefore=6, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=NAVY, spaceBefore=10, spaceAfter=4),
    "body": ParagraphStyle("body", spaceAfter=6, **base),
    "bullet": ParagraphStyle("bullet", leftIndent=14, bulletIndent=3, spaceAfter=3, **base),
    "caption": ParagraphStyle("caption", fontName="Helvetica-Oblique", fontSize=9, leading=12, textColor=GREY, spaceAfter=10),
    "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=9, leading=11.5),
    "cellb": ParagraphStyle("cellb", fontName="Helvetica-Bold", fontSize=9, leading=11.5, textColor=colors.white),
    "box": ParagraphStyle("box", fontName="Helvetica", fontSize=10.5, leading=14.5, textColor=colors.HexColor("#1d1d1d")),
    "meta": ParagraphStyle("meta", fontName="Helvetica", fontSize=10.5, leading=15, textColor=GREY),
}


def P(t, s="body"): return Paragraph(t, S[s])
def B(items): return [Paragraph(i, S["bullet"], bulletText="•") for i in items]


def T(rows, widths, hl_rows=()):
    data = [[Paragraph(str(c), S["cellb"] if r == 0 else S["cell"]) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    st = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LINEBELOW", (0, 0), (-1, -1), 0.4, LINE), ("TOPPADDING", (0, 0), (-1, -1), 3.5),
          ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5), ("LEFTPADDING", (0, 0), (-1, -1), 5), ("RIGHTPADDING", (0, 0), (-1, -1), 5)]
    for r in range(1, len(rows)):
        if r % 2 == 0: st.append(("BACKGROUND", (0, r), (-1, r), LIGHT))
    for r in hl_rows: st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#fff4d6")))
    t.setStyle(TableStyle(st)); return t


def box(text, color=NAVY):
    t = Table([[Paragraph(text, S["box"])]], colWidths=[16.6 * cm])
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1, color), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f9fc")),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


def img(name, w=16.6):
    from PIL import Image as PI
    im = PI.open(os.path.join(HERE, name)); r = im.size[1] / im.size[0]
    return Image(os.path.join(HERE, name), width=w * cm, height=w * r * cm)


def on_page(c, doc):
    c.saveState(); c.setFont("Helvetica", 8.5); c.setFillColor(GREY)
    c.drawString(2.2 * cm, 1.3 * cm, "NSE paper-trading system: design review, 27 November 2026")
    c.drawRightString(A4[0] - 2.2 * cm, 1.3 * cm, f"Page {doc.page}")
    c.setStrokeColor(LINE); c.line(2.2 * cm, 1.65 * cm, A4[0] - 2.2 * cm, 1.65 * cm); c.restoreState()


def on_cover(c, doc):
    c.saveState(); c.setFillColor(NAVY); c.rect(0, A4[1] - 1.2 * cm, A4[0], 1.2 * cm, fill=1, stroke=0); c.restoreState()


doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2.0 * cm, bottomMargin=2.2 * cm,
                      title="NSE Paper-Trading System: Design Review", author="Prepared for Sunny Alex")
frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="cover", frames=frame, onPage=on_cover), PageTemplate(id="main", frames=frame, onPage=on_page)])
s = []

# ---------------- cover
s += [Spacer(1, 3.2 * cm), P("NSE Paper-Trading System", "title"), P("Design review: what was built, what the evidence says, and what is still unproven", "subtitle"),
      P("Prepared 27 November 2026 for Sunny Alex", "meta"), P("Repository: SunnyAlexV/rl-paper-trading", "meta"), Spacer(1, 1.2 * cm),
      box("<b>Paper trading only.</b> No real money is traded. All backtest figures describe the past under stated assumptions; "
          "they are not forecasts. Live results so far cover a few weeks for the older accounts and none yet for the "
          "current primary test, which places its first trades on 30 November 2026."),
      Spacer(1, 1.0 * cm), P("<b>Contents</b>", "body")]
s += B(["1. Executive summary", "2. The system at a glance", "3. Design", "4. How we got here: the research journey",
        "5. Evidence for the primary strategy", "6. Risk: staying afloat", "7. Machine learning and reinforcement learning",
        "8. What is good", "9. What is weak or unproven", "10. Bugs found and fixed", "11. Plan and decision points",
        "Appendix A: glossary &nbsp;&nbsp; Appendix B: where to find things"])
s += [NextPageTemplate("main"), PageBreak()]

# ---------------- 1 executive summary
s += [P("1. Executive summary", "h1"),
      P("This project runs a fleet of paper-trading accounts on NSE equities every trading evening, with decisions written down "
        "and cryptographically fingerprinted before the next market open. It began as an attempt to build a reinforcement-learning "
        "trading agent. Two days of disciplined research (27 November 2026) replaced the original 17-formula \"research council\" "
        "with a simpler primary strategy, <b>momentum + delivery</b>: hold the 20 stocks that rank best on an equal blend of their "
        "12-month price trend and the share of traded shares taken into delivery."),
      box("<b>Bottom line.</b> A well-run research process around a well-understood <b>factor portfolio</b>: the Indian market, plus "
          "momentum, plus an India-specific delivery factor. It is not an unexplained stock-picking edge, and it is not an RL agent. "
          "The backtest is strong and survived every stress test we could design, but backtests flatter; the live paper test that "
          "begins on 30 November 2026 is what will decide. A diversified version (mix B) is ready for the stated goal of staying "
          "afloat first."), Spacer(1, 8)]
s += [T([["Measure", "Result", "Meaning"],
         ["Primary backtest, Jul 2012 - Nov 2026", "27.4% a year after fees, tax and dividends; Sharpe 1.42; worst fall -32%", "Strong, but chosen partly with hindsight"],
         ["Average universe stock, same period", "14.4% a year; Sharpe 0.84; worst fall -47%", "The fair benchmark"],
         ["Unseen 2012-15 period (holdout)", "26.2% a year vs 11.2% for the average stock", "The rule worked on data it never saw"],
         ["50 random halves of the stock list", "Beat its half's average stock in 50 of 50", "Not a fluke of a few stocks"],
         ["Every 3-year window since 2012", "Ahead of the average stock in 137 of 137", "But behind in 15% of 12-month windows"],
         ["Factor attribution", "Leftover alpha 1.9% a year, t 0.72 (not significant)", "Return = market + momentum + delivery factor"],
         ["Probability the edge is real (deflated Sharpe)", "58% to 95% depending on how many trials are counted", "Plausible, not proven"],
         ["Mix B (40% strategy, 20% gold, 10% US tech, 30% cash)", "17.4% a year; worst fall -16.5%; worst year -5% (before tax)", "Half the drawdown; ready for Jan 2027"],
         ["Live: original council account (Rs 1L)", "+0.71% after 16 trading days vs Nifty 50 +10.4%", "Too short to judge; signal had faded"],
         ["Live: momentum + delivery (primary)", "No trades yet; first fills 30 Nov 2026", "The real test starts now"]],
        [4.6, 6.6, 5.4])]
s += [Spacer(1, 6), P("<b>Strongest points:</b> pre-registration and hashed decisions; realistic Indian costs and tax; every test written "
                      "down before it ran, including the many that failed; independent lines of evidence converging on momentum and delivery; "
                      "a tested engine with a nightly integrity check."),
      P("<b>Weakest points:</b> no live track record yet; heavy multiple testing in a short time; a backtest sample that is mostly a "
        "bull market with no 2008-type crash; free data with no book values, market caps or intraday prices; and a project name "
        "(\"RL agent\") that no longer describes what works."), PageBreak()]

# ---------------- 2 at a glance
s += [P("2. The system at a glance", "h1"),
      P("<b>Scope.</b> NSE cash equities (and, in research and one planned account, gold and Nasdaq-100 ETFs). Daily decisions after "
        "the close, filled at the next open on paper. Data comes only from free NSE archives: daily price files (bhavcopy), "
        "security-wise delivery files, F&amp;O files, index closes, F&amp;O ban lists and corporate-action announcements."),
      P("<b>Universe.</b> Each month, the 500 most-traded NSE stocks with at least 250 days of history and a share price of Rs 20 or more; "
        "a stock is tradable only if its 60-day median traded value is at least Rs 5 crore (in practice about 330 stocks on a given day)."),
      P("<b>The fleet.</b> Eleven paper accounts run nightly on the same data; one more is built and waiting for its January slot.", "body"),
      T([["Account", "What it tests", "Capital", "Started"],
         ["<b>paper_mdeliv_10L</b>", "<b>PRIMARY</b> since the 27 Nov amendment: momentum + delivery, band rule 20/100", "Rs 10L", "Fills from 30 Nov 2026"],
         ["paper", "Original frozen council (17 formulas), now a comparison; downloads the day's data", "Rs 1L", "2 Nov 2026"],
         ["paper_10L", "Same council rule at Rs 10L (fairer read of the council)", "Rs 10L", "16 Nov 2026"],
         ["paper_hi / paper_lo", "More and less turnover versions of the band rule", "Rs 10L each", "16 Nov 2026"],
         ["paper_daily_10L / _1L", "Maximum turnover: daily top-20 equal weight", "Rs 10L / 1L", "16 Nov 2026"],
         ["paper_null_10L", "Null control: same rule on a council built from a no-edge market", "Rs 10L", "16 Nov 2026"],
         ["paper_timed_10L", "Council + RL timing agent setting exposure to 100 / 50 / 0%", "Rs 10L", "16 Nov 2026"],
         ["paper_mom_10L", "Plain 12-1 momentum", "Rs 10L", "18 Nov 2026"],
         ["paper_integ_10L", "Momentum + low volatility + delivery", "Rs 10L", "Fills from 30 Nov 2026"],
         ["paper_multi_10L (planned)", "Mix B: 40% strategy, 20% gold, 10% Nasdaq-100, 30% cash", "Rs 10L", "Earliest Jan 2027"]],
        [3.9, 7.6, 2.2, 2.9], hl_rows=(1,)), PageBreak()]

# ---------------- 3 design
s += [P("3. Design", "h1"), P("3.1 Data pipeline", "h2"),
      P("Every evening the first account downloads that day's NSE files, rebuilds a point-in-time panel (each value is only what "
        "was knowable on that date) and trims raw files to a rolling 500-day window. Prices are back-adjusted for splits and bonuses "
        "using NSE's own previous-close figures, with a rule for splits NSE did not record and, since 27 November, a rule that stops "
        "weekend special sessions (Budget days, Muhurat trading) being mistaken for corporate actions."),
      P("3.2 Signal", "h2"),
      P("Each day, every universe stock gets two cross-sectional rank z-scores (how it ranks against the others, standardised): "
        "<b>12-1 momentum</b> (return from 12 months ago to 1 month ago) and <b>delivery share</b> (60-day average of delivered / traded "
        "quantity). The score is their simple average. Nothing is fitted; there are no weights to tune."),
      P("3.3 Trading rule", "h2")]
s += B(["<b>Band rule:</b> hold 20 stocks; sell a holding only when it drops out of the top 100; new names share the freed money equally. "
        "The band keeps turnover low (about 1.8 times a year).",
        "<b>Execution model:</b> decide after the close, fill at the next open with a modelled spread and square-root market impact; "
        "whole shares only; trims and top-ups smaller than 1% of NAV are skipped; at most 7.5% in one stock (backtests).",
        "<b>Costs (Zerodha, today's schedule):</b> STT 0.1% on buys and sells, exchange and SEBI charges, GST, stamp duty 0.015% on buys, "
        "Rs 15.34 DP charge per stock per sell day.",
        "<b>Tax:</b> first-in-first-out lots; 20% short-term and 12.5% long-term (above Rs 1.25 lakh a year) plus 4% cess; losses set off "
        "and carried forward eight years; dividends credited and taxed at 31.2%."])
s += [P("3.4 Governance", "h2")]
s += B(["<b>Pre-registration</b> (PREREGISTRATION.md): the rules of every account are fixed in dated commits before trading; changes "
        "are separate, dated amendments that explain why.",
        "<b>Tamper-evident decisions:</b> each evening's orders file is hashed (SHA-256) into a ledger and committed before the next open.",
        "<b>Safeguards against overfitting</b> (27 Nov 2026): frozen accounts are never tweaked (a changed idea is a new account); every "
        "backtest is logged in research/TRIALS.md; rules and pass/fail criteria are committed before each study; at most 12 accounts and "
        "one new account per quarter; no verdicts before 12 months except pre-set 6-month checks; a strict live bar (t at least 2.8 for "
        "10 exploratory accounts) before anything counts as better; and no real money before that bar is met.",
        "<b>Two-stage evaluation:</b> Stage 1 counts only spread and impact (is there a real pattern?); Stage 2 adds every fee and tax "
        "(can it be traded profitably?)."])
s += [KeepTogether([P("3.5 Nightly operations (8:45 pm IST, weekdays)", "h2"),
      T([["Step", "What happens"],
         ["1. Trade", "All accounts fill yesterday's orders, mark NAV and write tomorrow's orders, each hashed into its ledger"],
         ["2. Check", "check_integrity.py (ledger hashes, dates, lots vs shares, NAV = cash + holdings to the rupee) and 25 unit tests"],
         ["3. Review", "Per-account session review: day P&amp;L by holding, z-scores, each fill, why each order was chosen"],
         ["4. Post-trade", "A doctor-style case file for every closed trade and a learning ledger of patterns (hypotheses only)"],
         ["5. Committee", "Five roles (statistician, risk manager, microstructure, doctor, skeptic) write a verdict for the primary"],
         ["6. Commit and notify", "Everything committed to the repository; a summary is sent to the phone, problems first"]],
        [3.0, 13.6])]), Spacer(1, 14)]

# ---------------- 4 research journey
s += [P("4. How we got here: the research journey", "h1"),
      P("Every study below had its rules and pass/fail criteria committed before it ran, and each result was published whether it "
        "passed or failed. Rebuilt history: NSE data from June 2011, cross-checked against an earlier rebuild (monthly returns "
        "correlated 0.96 to 0.997)."),
      T([["Study", "Idea", "Result", "Verdict"],
         ["Signal health", "Does the council still predict?", "Blend near zero for the past year; members cancel; momentum strongest", "Council faded"],
         ["Pods round 1", "Trend, contrarian, defensive pods", "Trend 22.5% a year; contrarian 0.7%; defensive lagged in 2022-26", "Trend only"],
         ["Long-short (futures)", "Short the worst via stock futures", "Best 5.0% a year; shorts lost in a rising market", "Fail"],
         ["Integrated score", "Momentum + low vol + delivery", "Sharpe 1.23, worst fall -28%, but trailed in 2022-26", "Fail (best Sharpe)"],
         ["Walk-forward agent", "No-hindsight formula search", "6-10% a year after costs; patterns real but too fast", "Fail"],
         ["Agent v2 (batter/doctor)", "Trade only confident setups", "The pickier, the worse; rediscovered momentum + delivery", "Fail"],
         ["Candle wicks", "Lower vs upper wicks", "Lower wick real (IC 0.031, t 4.2) but too small to trade", "Fail as strategy"],
         ["Holdout 2012-15", "Momentum + delivery on unseen years", "26.2% a year vs 11.2%", "Pass"],
         ["Stress tests", "Random halves, windows, costs x3", "50/50 halves, 137/137 windows, Sharpe 1.33 at costs x3", "Pass"],
         ["Stops (five kinds)", "Cut drawdowns with stop-losses", "Only climbing pins + rest with intraday orders helped; fill-sensitive", "Promising"],
         ["Universe choice", "Bigger / calmer / F&amp;O-only universes", "All worse; current universe best", "No change"],
         ["Multi-asset menu", "Add gold, US tech, cash", "Drawdowns halved; every mix broke its limit 1.5x after 2019", "Lesson"],
         ["Factor attribution", "Alpha or factors?", "Market + momentum + delivery; alpha 1.9% (t 0.72)", "Factors"],
         ["Neural nets", "Do deeper models help?", "Deeper fits the past better, the future worse", "Shallow at most"]],
        [3.2, 3.9, 6.8, 2.7]), Spacer(1, 6),
      P("Three independent lines of evidence point at the same thing: the backtests, the unseen 2012-15 period, and blind agents that "
        "were given no hints yet kept selecting delivery data and rediscovered momentum + delivery on their own."), Spacer(1, 14)]

# ---------------- 5 evidence
s += [P("5. Evidence for the primary strategy", "h1"), img("c1_growth.png"),
      P("Figure 1. Momentum + delivery against the average universe stock (both after all fees and tax, price returns) and the Nifty 50 "
        "price index. Backtest; the rule was chosen partly after seeing this period.", "caption"), img("c2_drawdowns.png"),
      P("Figure 2. Falls from previous peaks. Deepest: -32% (COVID, recovered in 5 months), -28% (Sep 2024 to Feb 2025, 22 months to "
        "recover), -26% (2018, 25 months).", "caption"),
      P("5.1 What the return is made of", "h2"),
      T([["Component (monthly regression, 172 months)", "Exposure", "t-statistic"],
         ["Market (equal-weight universe)", "1.03", "19.3"], ["Momentum factor", "0.40", "6.4"], ["Delivery factor (India-specific)", "0.53", "5.5"],
         ["Size (traded value)", "0.03", "0.3"], ["Leftover alpha", "1.9% a year", "0.72 (not significant)"]], [8.6, 4.0, 4.0]),
      Spacer(1, 4),
      P("The strategy is a factor portfolio. The delivery factor (high-delivery minus low-delivery stocks) earned 6.4% a year in 2012-26 and "
        "behaves defensively (correlation 0.85 with low volatility). It is not a standard published factor; whether it is a reward for "
        "risk or an inefficiency is open, and without book values a value tilt cannot be ruled out."),
      ]
s += [KeepTogether([P("5.2 What to expect live", "h2")] + B(["Backtests chosen with hindsight shrink live. The honest no-hindsight agents earned 6-10% a year against 18-28% for hindsight-picked rules.",
        "Normal bad luck for this rule: behind the average stock in 15% of 12-month windows (once by 25 points); an outright loss in 14% of them.",
        "A warning sign: still behind after 24 months (historically 1% of windows)."])), Spacer(1, 14)]

# ---------------- 6 risk
s += [P("6. Risk: staying afloat", "h1"),
      P("The stated goal is to survive any market first and seek returns second. The research tested every lever available:"),
      T([["Approach", "What happened", "Verdict"],
         ["Fixed or trailing price stops (checked at the close)", "Sold normal dips; 6 in 10 stopped stocks recovered within a month", "Cost money"],
         ["Climbing pins with slack, rest after a stop (intraday stop orders)", "Worst fall -37% to -30% after tax; return -1 to -2.3 pts; verdict flips if fills are 1% worse", "Promising, fill-sensitive"],
         ["Bad-news exit (stock crashes 15% on a calm market day)", "Costs nothing; fired only 14 times in 14 years", "Free but rare"],
         ["Safer universe (bigger, calmer, F&amp;O only)", "Lower return and Sharpe, no smaller drawdown", "Worse"],
         ["Diversify across assets (gold, US tech, cash)", "Drawdowns halved with a strong return", "Best lever"]],
        [5.6, 7.6, 3.4]), Spacer(1, 8),
      box("<b>The 1.5x lesson.</b> Mixes chosen on 2012-19 to stay within a 10%, 15% or 20% fall all fell about 1.5 times further in 2020-26. "
          "The next crisis is usually worse than the last one planned for: to stay within a 15% fall live, design for about 10% on history. "
          "Mix B was chosen on principle (always hold a diversifier) rather than optimised, because the optimised mix dropped gold just "
          "before gold rose 72%.", BAD),
      Spacer(1, 8), img("c3_mixb.png", 15.0),
      P("Figure 3. Mix B (40% momentum + delivery, 20% gold, 10% Nasdaq-100, 30% cash at 6.5%, monthly rebalance) against the equity strategy "
        "alone, before tax. 17.4% vs 26.8% a year; worst fall -16.5% vs -33.5%; worst calendar year -5.0% vs -18.1%. In 2025, when the equity "
        "strategy lost 9.2%, gold's rise kept mix B at +11.3%.", "caption"), PageBreak()]

# ---------------- 7 ML / RL
s += [P("7. Machine learning and reinforcement learning", "h1"),
      P("<b>Why the system is not RL.</b> Reinforcement learning means an agent that learns its own decision rule from rewards through trial "
        "and error. The primary is a fixed formula that never updates from its outcomes. Every learning component tried here either failed "
        "or added nothing: the RL timing account, the walk-forward agents, online weight learning and the confidence-gated batter agent."),
      P("<b>Why RL struggled.</b> About 3,500 noisy trading days are far too few for RL; rewards are mostly luck; the market keeps changing; "
        "and there is no simulator in which to practise without overfitting the one history we have. RL tends to work in trading where data "
        "is abundant (high-frequency) or in narrow jobs such as order execution."), img("c4_nn.png"),
      P("Figure 4. Same 12 inputs, trained on 2013-19 and scored on unseen 2020-26. The 5-layer network looked best in training and was worst "
        "on unseen years (73% of its skill vanished). Ridge and a 1-layer network kept the most and slightly beat the untrained blend.", "caption"),
      P("<b>Where ML fits.</b> Shallow models as challengers, shrunk towards the momentum + delivery baseline and promoted only on live "
        "shadow results; deep learning for reading text (NSE corporate announcements); RL only for sequential jobs such as tax-aware "
        "rebalancing or allocating between mix B's sleeves, always against a rule-based baseline."), PageBreak()]

# ---------------- 8 good
s += [P("8. What is good", "h1")]
s += B(["<b>Honest process.</b> Pre-registration, hashed decisions committed before the open, frozen accounts and a trials ledger. Failures "
        "(contrarian, long-short, wicks, agents, stops) were kept, not buried.",
        "<b>Realistic costs.</b> Actual Indian charges, STT, DP charges, spread and impact, FIFO capital-gains tax, F&amp;O ban lists, "
        "futures STT at the 2026 rate, whole shares and dividends.",
        "<b>Convergent evidence.</b> Holdout, 50 random halves, 137 of 137 three-year windows, costs tripled, and independent blind agents "
        "all point to momentum + delivery.",
        "<b>Understood return.</b> The factor attribution says what the strategy is, which sets honest expectations.",
        "<b>Low turnover and simplicity.</b> Two ingredients, no fitted weights, about 1.8 portfolio turnovers a year; costs barely dent it.",
        "<b>A survival plan.</b> Mix B halves drawdowns, built and tested in the engine, waiting for its slot.",
        "<b>Engineering discipline.</b> Fixes are replay-verified against every account; 25 unit tests; a nightly integrity check reconciles "
        "every account to the rupee.",
        "<b>Learning loop.</b> Daily reviews, a five-role committee and doctor-style case files, with a rule that learning produces "
        "hypotheses, never silent changes.",
        "<b>Zero cost.</b> Free NSE data and the existing scheduled task; no paid APIs."])
s += [P("9. What is weak or unproven", "h1")]
s += B(["<b>No live record.</b> The primary has not traded yet. Everything about it is backtest.",
        "<b>Multiple testing.</b> Thirty-plus studies in two days. Momentum + delivery was partly found after the fact; the deflated Sharpe "
        "gives 58-95% odds the edge is real.",
        "<b>Factors, not skill.</b> Factor premia can go years without paying. Momentum crashes; the defensive delivery factor lags in "
        "strong bull markets.",
        "<b>A kind sample.</b> 2012-26 was mostly a rising market with a mid-cap boom. No 2008-type crash is in the data.",
        "<b>Free-data limits.</b> No book values (no value factor), no market capitalisation (size proxied by trading value), no intraday "
        "prices (stop fills are modelled), no history of total-return indices.",
        "<b>Paper fills.</b> Open-auction slippage in mid-caps and real stop-order fills are modelled, not measured.",
        "<b>Assumptions.</b> Today's cost schedule is applied to all history; cash earns an assumed rate; the 2012-16 debt proxy is a constant 6.5%.",
        "<b>Many accounts.</b> Eleven accounts make it likely that one looks good by chance; the t-at-least-2.8 rule guards against this.",
        "<b>Operations.</b> One scheduled job runs everything; the committee commentary is written by an AI and can misread numbers, "
        "though the numbers themselves come from scripts and checks.",
        "<b>The name.</b> The project is called an RL trading agent; the working system is a rule-based factor strategy.",
        "<b>The old primary.</b> The council account at Rs 1L is handicapped by charges and whole-share rounding (one position reached 20% of the account)."])
s += [PageBreak()]

# ---------------- 10 bugs
s += [P("10. Bugs found and fixed", "h1"),
      T([["Issue", "Effect", "Fix and check"],
         ["Weekend special sessions (Budget days, Muhurat trading) read as corporate actions", "Live trader could rescale share counts; on 9 Nov 2026 77% of stocks showed a false factor, but rounding left every count unchanged",
          "Market-wide rule (more than 30% of stocks = missed session); replay: 7 of 9 accounts identical, 2 daily accounts swap one stock; unit test fails on old code"],
         ["Review script crashed on an account's first day", "Would have broken tonight's review for two new accounts", "Handles first sessions; tested"],
         ["Futures STT in the long-short study", "Used 0.02%; Budget 2026 raised it to 0.05%", "Re-run at 0.05%; conclusion unchanged"],
         ["ETF unit splits (GOLDBEES 1:100, NIFTYBEES and MON100 1:10)", "Fake 88-99% crashes in ETF series", "Snap to standard split ratios; series match known history"],
         ["Concentration from cash sweeping (council rule)", "One stock reached 20% of the Rs 1L account", "Kept (frozen rule); research uses a 7.5% cap; flagged in reviews"]],
        [4.6, 5.8, 6.2]), Spacer(1, 8),
      P("Not yet covered by tests: delistings, circuit-locked fills, and dividend edge cases.")]

# ---------------- 11 plan
s += [P("11. Plan and decision points", "h1"),
      T([["When", "What"],
         ["30 Nov 2026", "Momentum + delivery (primary) and the integrated account place their first trades"],
         ["Nightly", "Trading, integrity check, unit tests, reviews, post-trade case files, committee verdict, phone summary"],
         ["January 2027", "Dated amendment to add the multi-asset mix B account (code built and tested)"],
         ["Late May 2027 (6 months)", "Pre-set check: broken if the drawdown is worse than -40% or it trails the Nifty 500 by more than 20 points"],
         ["Late Nov 2027 (12 months)", "Working: ahead of the Nifty 500 with a drawdown better than -35%. Unclear but normal: behind by up to 25 points. "
                                       "Broken: behind by more than 25 points, or 15 behind the null control"],
         ["Nov 2028 (24 months)", "Trailing the Nifty 500 is a serious warning; by more than 10 points counts as broken"],
         ["Real money", "Only after the live bar (t at least 2.8) is met, and then as a small satellite next to an index core; mix B is the natural candidate"]],
        [3.6, 13.0]), Spacer(1, 8),
      box("<b>Research freeze.</b> No new studies before the 6-month checkpoint apart from the planned January account. The bottleneck is "
          "now live evidence, not more ideas. The most useful optional step is a tiny real-money pilot to measure actual fills, slippage "
          "and stop-order behaviour against the paper model."),
      PageBreak()]

# ---------------- appendices
s += [P("Appendix A: glossary", "h1"),
      T([["Term", "Meaning"],
         ["CAGR", "Compound annual growth rate: the steady yearly return that would give the same end result"],
         ["Sharpe ratio", "Return per unit of volatility; higher means a smoother ride for the same return"],
         ["Drawdown / worst fall", "Fall from a previous peak to a later low"],
         ["IC (rank information coefficient)", "Correlation between a signal's ranking today and stocks' later return ranking; 0.05 is useful in finance"],
         ["t-statistic", "How clearly a result stands out from noise; above about 2 is unlikely to be chance (above 2.8 for 10 accounts)"],
         ["Z-score", "How many standard deviations a stock is above or below the average of all stocks on that day"],
         ["Band rule", "Hold the top 20; sell only when a holding falls out of the top 100, so ordinary rank wobbles do not cause trades"],
         ["Delivery share", "Shares taken into delivery (kept) as a share of shares traded; high means committed buyers rather than day traders"],
         ["Factor / alpha", "A factor is a known, broad driver of returns; alpha is what is left after the factors are accounted for"],
         ["Holdout", "A period of data not used when the rules were chosen, kept back to test them"],
         ["Walk-forward", "Learning only from the past at every point in a simulation, then moving forward"],
         ["Deflated Sharpe", "The probability a backtest's Sharpe reflects a real edge after allowing for how many strategies were tried"],
         ["Pre-registration", "Writing down rules and success criteria before testing, so results cannot shape the rules"],
         ["Stage 1 / Stage 2", "Results with spread and impact only / with every fee and tax"]],
        [4.6, 12.0]), Spacer(1, 12), P("Appendix B: where to find things", "h1"),
      T([["Path", "Contents"],
         ["PREREGISTRATION.md", "Frozen rules, every amendment and fix, the overfitting safeguards and verdict thresholds"],
         ["paper/fleet.json, paper/config_*.json", "Accounts and their frozen configurations (including the planned multi-asset account)"],
         ["&lt;account&gt;/nav.csv, orders_after_*.json, ledger.txt", "Daily NAV, decisions and their SHA-256 ledger"],
         ["&lt;account&gt;/reviews/, &lt;account&gt;/trades/", "Daily session reviews; post-trade case files and learning ledger"],
         ["research/TRIALS.md", "Every test tried, so the multiple-testing burden is visible"],
         ["research/pods, stress, factors, multiasset, stops, wicks, agent_wf, agent_v2, nn, dividends", "Each study's rules (SPEC), code and RESULTS"],
         ["check_integrity.py, tests/", "Nightly integrity check and unit tests"],
         ["ISSUES.md", "Known issues and fixes"]],
        [7.4, 9.2])]

doc.build(s)
print("written", OUT)
