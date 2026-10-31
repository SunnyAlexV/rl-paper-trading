"""Deflated Sharpe ratio (Bailey & Lopez de Prado, 2014) for the frozen council (seed 0).

  DSR = Phi( (SR - SR0) * sqrt(T-1) / sqrt(1 - g3*SR + (g4-1)/4 * SR^2) )
  SR0 = sqrt(V) * ( (1-gamma)*Phi^-1(1 - 1/N) + gamma*Phi^-1(1 - 1/(N e)) ),  gamma = 0.5772...

SR, V are per-day (not annualised); g3, g4 are the skew and (non-excess) kurtosis of daily returns;
T is the number of days. V is the variance of Sharpe across trials, estimated from the five research
seeds of the real council (the closest thing we have to independent trials of the same search).
N, the number of effectively independent strategies tried on this data over the whole project, is
not known exactly, so the DSR is reported for a range. A DSR above 0.95 means the Sharpe survives
the selection: it is unlikely to be the best of N lucky draws.
"""
import numpy as np, pandas as pd
from scipy.stats import norm, skew, kurtosis

R = pd.read_csv("results/council_seeds_daily_returns.csv", index_col=0, parse_dates=True)
periods = {"Full 2013-26": ("2013-01-01", None), "2022-26": ("2022-01-01", None)}
EG = 0.5772156649
rows = []
for pname, (a, b) in periods.items():
    X = R.loc[a:b].dropna(how="all").fillna(0)
    sr = X.mean() / X.std()
    V = sr[[c for c in X if c.startswith("real")]].var(ddof=1)
    x = X["real_s0"]; T = len(x); s = sr["real_s0"]
    g3, g4 = skew(x), kurtosis(x, fisher=False)
    for N in (1, 10, 50, 100, 500, 1000):
        sr0 = 0.0 if N == 1 else np.sqrt(V) * ((1 - EG) * norm.ppf(1 - 1 / N) + EG * norm.ppf(1 - 1 / (N * np.e)))
        dsr = norm.cdf((s - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * s + (g4 - 1) / 4 * s ** 2))
        rows.append(dict(period=pname, N=N, sharpe_ann=s * np.sqrt(252), sr0_ann=sr0 * np.sqrt(252),
                         seed_sd_ann=np.sqrt(V * 252), skew=g3, kurt=g4, days=T, DSR=dsr))
    # empirical: real seeds vs null seeds, annualised Sharpe of daily post-tax returns
    for c in X:
        rows.append(dict(period=pname, series=c, sharpe_ann=sr[c] * np.sqrt(252)))
out = pd.DataFrame(rows)
out.to_csv("results/council_deflated_sharpe.csv", index=False)
pd.set_option("display.width", 200)
print(out.round(3).to_string())

# Sensitivity to V. The seed spread (one search, five seeds) understates how far Sharpe varies across
# the genuinely different strategies tried in this project (stage 3-5 pools, agents, council
# variants), so the DSR is also computed for wider cross-trial Sharpe dispersions.
grid = []
for pname, (a, b) in periods.items():
    X = R.loc[a:b].dropna(how="all").fillna(0)
    x = X["real_s0"]; T = len(x); s = x.mean() / x.std()
    g3, g4 = skew(x), kurtosis(x, fisher=False)
    for sd_ann in (0.085, 0.25, 0.5, 0.75):
        for N in (10, 50, 100, 500):
            sd = sd_ann / np.sqrt(252)
            sr0 = sd * ((1 - EG) * norm.ppf(1 - 1 / N) + EG * norm.ppf(1 - 1 / (N * np.e)))
            grid.append(dict(period=pname, trial_sd_ann=sd_ann, N=N, sr0_ann=sr0 * np.sqrt(252),
                             DSR=norm.cdf((s - sr0) * np.sqrt(T - 1) / np.sqrt(1 - g3 * s + (g4 - 1) / 4 * s ** 2))))
G = pd.DataFrame(grid); G.to_csv("results/council_deflated_sharpe_grid.csv", index=False)
print(G.pivot_table(index=["period", "trial_sd_ann"], columns="N", values="DSR").round(3).to_string())
