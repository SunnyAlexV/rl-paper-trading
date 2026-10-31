# rl-paper-trading

Forward paper-trading of a systematic NSE equity strategy, run daily and committed before each
market open. No real money is traded.

- `PREREGISTRATION.md` — the frozen system and the rules of the test. Read this first.
- `paper/config.json` — frozen configuration, including the SHA-256 of the signal file.
- `paper/nav.csv` — daily NAV, before and after accrued tax.
- `paper/orders_after_<date>.json` — decisions made after each close, filled at the next open.
- `paper/ledger.txt` — SHA-256 of every decision file, one line per day.
- `data/` — a rolling window of the last 500 trading days of NSE bhavcopy, delivery and F&O
  summaries (enough to compute every feature).

Run one day by hand (Python 3.11+, `pip install -r requirements.txt`):

    python -m alpha.paper_trade --config paper/config.json

Research behind the system: a reinforcement-learning trading engine project (cost and tax engine,
MCTS strategy discovery, survivorship-free universe, research council with null tests).
