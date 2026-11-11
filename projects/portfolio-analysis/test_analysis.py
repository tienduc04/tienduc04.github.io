"""Self-checks on synthetic data (no internet needed). Run: .venv/Scripts/python test_analysis.py"""
import numpy as np
import pandas as pd

from analysis import frontier, max_drawdown, optimise, portfolio_stats

mu = np.array([0.08, 0.04, 0.05])
vol = np.array([0.16, 0.05, 0.15])
corr = np.array([[1, 0.1, 0.0], [0.1, 1, 0.2], [0.0, 0.2, 1]])
cov = np.outer(vol, vol) * corr
rf = 0.02

# A single-asset portfolio has that asset's return and volatility.
ret, v, s = portfolio_stats(np.array([1, 0, 0]), mu, cov, rf)
assert np.isclose(ret, 0.08) and np.isclose(v, 0.16) and np.isclose(s, 0.375)

# Optimised weights are long-only, sum to 1, and beat simple alternatives.
for obj in ("max_sharpe", "min_var"):
    w = optimise(mu, cov, rf, obj)
    assert np.all(w >= 0) and np.isclose(w.sum(), 1), obj
w_ms, w_mv, w_eq = optimise(mu, cov, rf, "max_sharpe"), optimise(mu, cov, rf, "min_var"), np.full(3, 1 / 3)
assert portfolio_stats(w_ms, mu, cov, rf)[2] >= portfolio_stats(w_eq, mu, cov, rf)[2] - 1e-9
assert portfolio_stats(w_mv, mu, cov, rf)[1] <= min(vol) + 1e-9  # diversification: at or below the least risky asset

# The frontier is (volatility, return) pairs moving up and to the right, starting at the min-variance point.
fr = frontier(mu, cov, rf, points=10)
assert all(b[1] >= a[1] - 1e-9 and b[0] >= a[0] - 1e-6 for a, b in zip(fr, fr[1:]))
assert np.isclose(fr[0][0], portfolio_stats(w_mv, mu, cov, rf)[1], atol=1e-4)

# Max drawdown: 100 -> 120 -> 60 is a 50% fall from the peak.
assert np.isclose(max_drawdown(pd.Series([100, 120, 60, 90])), -0.5)

print("all checks passed")
