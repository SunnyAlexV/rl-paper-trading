# Factor attribution: results (27 Nov 2026)

Rules: `SPEC.md` (committed before the run). 172 months, Jul 2012 - Nov 2026, pre-tax, all fees; Newey-West t-stats.

**Factor returns (long-short, equal weight, % a year):** MKT (equal-weight universe minus cash) 9.2, SIZE (small minus
large by traded value) 3.7, MOM 12.5, LOWVOL 2.0, DELIV 6.4. DELIV is strongly linked to LOWVOL (correlation 0.85) and
moves against the market (-0.76): high-delivery stocks behave defensively.

| Book | Factors | Alpha % a year (t) | R² | Market | Size | Momentum | Low vol | Delivery |
|---|---|---|---|---|---|---|---|---|
| **Momentum + delivery (primary)** | 4 known | **4.3 (1.44)** | 0.74 | 0.97 | 0.23 | 0.41 | 0.33 | |
| **Momentum + delivery (primary)** | + delivery | **1.9 (0.72)** | 0.78 | 1.03 | 0.03 | 0.40 | -0.02 | **0.53 (t 5.5)** |
| Momentum only | 4 known | -1.4 (-0.46) | 0.83 | 1.03 | 0.06 | 0.68 | -0.16 | |
| Council (frozen) | 4 known | 1.3 (0.49) | 0.71 | 1.00 | 0.19 | 0.15 | 0.42 | |
| Council (frozen) | + delivery | -0.1 (-0.03) | 0.72 | 1.03 | 0.07 | 0.14 | 0.21 | 0.31 |

**Verdict under the pre-set reading:** alpha t < 2, and adding the delivery factor removes most of what is left (4.3% -> 1.9%,
t 0.72). **The primary's return is factor exposure, not unexplained skill:** about one unit of the market, 0.4 of
momentum and 0.5 of the delivery factor. The size tilt the review committee worried about is small and disappears once
delivery is included. Momentum alone has no alpha at all (pure factor); the council has none either.

What is new is the **delivery factor itself**: 6.4% a year long-short over 2012-26, India-specific (NSE delivery data), not
one of the standard published factors, and behaving like a defensive / low-volatility tilt. Whether it is a reward
for risk or a market inefficiency is not settled by this data. Gap: no value factor (no book values available).
