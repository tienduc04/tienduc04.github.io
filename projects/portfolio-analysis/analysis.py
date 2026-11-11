"""Portfolio analysis: returns, risk, Sharpe ratio and the long-only efficient frontier.

Run:  .venv/Scripts/python analysis.py            (uses data/prices.csv if it exists)
      .venv/Scripts/python analysis.py --refresh  (downloads prices again from Yahoo Finance)
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import minimize

# ---- Settings you can change ------------------------------------------------
ASSETS = {
    "SPY": "US equities (S&P 500)",
    "EFA": "Developed ex-US equities",
    "VNM": "Vietnam equities",
    "AGG": "US investment-grade bonds",
    "GLD": "Gold",
}
RISK_FREE = "BIL"  # 1–3 month US Treasury bills: its average return is the risk-free rate
START, END = "2015-01-01", "2025-01-01"  # 10 full calendar years, 2015–2024
TRADING_DAYS = 252
# -----------------------------------------------------------------------------

HERE = Path(__file__).parent
DATA, OUT = HERE / "data", HERE / "results"
COPPER, GREY, INK = "#C47A3A", "#7d8ca1", "#1d2733"


def load_prices(refresh=False):
    """Adjusted close prices (dividends reinvested), cached so results are reproducible."""
    cache = DATA / "prices.csv"
    if cache.exists() and not refresh:
        return pd.read_csv(cache, index_col=0, parse_dates=True)
    import yfinance as yf

    tickers = list(ASSETS) + [RISK_FREE]
    px = yf.download(tickers, start=START, end=END, auto_adjust=True, progress=False, threads=False)["Close"][tickers]
    px = px.dropna()
    if px.empty:
        sys.exit("No prices downloaded; check the tickers or your internet connection.")
    DATA.mkdir(exist_ok=True)
    px.to_csv(cache)
    return px


def portfolio_stats(w, mu, cov, rf):
    """Annualised return, volatility and Sharpe ratio for weights w."""
    ret = float(w @ mu)
    vol = float(np.sqrt(w @ cov @ w))
    return ret, vol, (ret - rf) / vol


def max_drawdown(prices):
    return float((prices / prices.cummax() - 1).min())


def optimise(mu, cov, rf, objective, target=None):
    """Long-only weights that sum to 1. objective: 'min_var' or 'max_sharpe'."""
    n = len(mu)
    cons = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    if target is not None:
        cons.append({"type": "eq", "fun": lambda w: w @ mu - target})
    if objective == "min_var":
        f = lambda w: w @ cov @ w
    else:
        f = lambda w: -(w @ mu - rf) / np.sqrt(w @ cov @ w)
    res = minimize(f, np.full(n, 1 / n), bounds=[(0, 1)] * n, constraints=cons, method="SLSQP")
    if not res.success:
        raise RuntimeError(f"Optimiser failed: {res.message}")
    return np.clip(res.x, 0, None) / np.clip(res.x, 0, None).sum()


def frontier(mu, cov, rf, points=40):
    """(volatility, return) pairs along the long-only efficient frontier."""
    w_min = optimise(mu, cov, rf, "min_var")
    lo, hi = float(w_min @ mu), float(mu.max())
    out = []
    for t in np.linspace(lo, hi, points):
        ret, vol, _ = portfolio_stats(optimise(mu, cov, rf, "min_var", t), mu, cov, rf)
        out.append((vol, ret))
    return out


def main():
    px = load_prices(refresh="--refresh" in sys.argv)
    rets = px.pct_change().dropna()
    rf = float(rets[RISK_FREE].mean() * TRADING_DAYS)
    r = rets[list(ASSETS)]
    mu = r.mean().values * TRADING_DAYS
    cov = r.cov().values * TRADING_DAYS
    corr = r.corr()
    years = (px.index[-1] - px.index[0]).days / 365.25

    assets = []
    for i, t in enumerate(ASSETS):
        p = px[t]
        assets.append({
            "ticker": t, "name": ASSETS[t],
            "ret": mu[i], "vol": float(np.sqrt(cov[i, i])),
            "cagr": float((p.iloc[-1] / p.iloc[0]) ** (1 / years) - 1),
            "sharpe": (mu[i] - rf) / float(np.sqrt(cov[i, i])),
            "max_drawdown": max_drawdown(p),
        })

    names = list(ASSETS)
    candidates = {
        "Max Sharpe": optimise(mu, cov, rf, "max_sharpe"),
        "Min variance": optimise(mu, cov, rf, "min_var"),
        "Equal weight": np.full(len(names), 1 / len(names)),
        "60/40 (SPY/AGG)": np.array([0.6 if t == "SPY" else 0.4 if t == "AGG" else 0 for t in names]),
    }
    portfolios = {}
    for label, w in candidates.items():
        ret, vol, sharpe = portfolio_stats(w, mu, cov, rf)
        growth = (1 + r @ w).cumprod()  # daily-rebalanced, in-sample
        portfolios[label] = {
            "weights": {t: round(float(x), 4) for t, x in zip(names, w)},
            "ret": ret, "vol": vol, "sharpe": sharpe, "max_drawdown": max_drawdown(growth),
        }

    # Out-of-sample check: weights chosen on 2015–2019 data, then held through 2020–2024.
    train, test = rets[:"2019-12-31"], rets["2020-01-01":]
    rf_tr, rf_te = (float(x[RISK_FREE].mean() * TRADING_DAYS) for x in (train, test))
    mu_tr, cov_tr = train[names].mean().values * TRADING_DAYS, train[names].cov().values * TRADING_DAYS
    mu_te, cov_te = test[names].mean().values * TRADING_DAYS, test[names].cov().values * TRADING_DAYS
    oos_weights = {
        "Max Sharpe (fitted 2015–2019)": optimise(mu_tr, cov_tr, rf_tr, "max_sharpe"),
        "Equal weight": candidates["Equal weight"],
        "60/40 (SPY/AGG)": candidates["60/40 (SPY/AGG)"],
    }
    out_of_sample = {}
    for label, w in oos_weights.items():
        ret, vol, sharpe = portfolio_stats(w, mu_te, cov_te, rf_te)
        out_of_sample[label] = {"weights": {t: round(float(x), 4) for t, x in zip(names, w)},
                                "ret": ret, "vol": vol, "sharpe": sharpe,
                                "max_drawdown": max_drawdown((1 + test[names] @ w).cumprod())}

    OUT.mkdir(exist_ok=True)
    summary = {
        "out_of_sample_2020_2024": out_of_sample,
        "period": f"{px.index[0].date()} to {px.index[-1].date()}",
        "observations": len(rets), "risk_free": rf,
        "assets": assets, "correlation": corr.round(3).values.tolist(), "portfolios": portfolios,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, default=float))

    # Chart 1: efficient frontier
    fr = frontier(mu, cov, rf)
    fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
    ax.plot([v for v, _ in fr], [m for _, m in fr], color=COPPER, lw=2.5, label="Efficient frontier (long-only)")
    for a in assets:
        ax.scatter(a["vol"], a["ret"], color=GREY, zorder=3)
        ax.annotate(a["ticker"], (a["vol"], a["ret"]), xytext=(6, 4), textcoords="offset points", color=INK)
    markers = {"Max Sharpe": "*", "Min variance": "D", "Equal weight": "o", "60/40 (SPY/AGG)": "s"}
    for label, p in portfolios.items():
        ax.scatter(p["vol"], p["ret"], marker=markers[label], s=140 if label == "Max Sharpe" else 60,
                   color=COPPER if label == "Max Sharpe" else INK, zorder=4, label=label)
    ax.set_xlabel("Annualised volatility")
    ax.set_ylabel("Annualised mean return")
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1, decimals=0))
    ax.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.02))
    ax.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(0.05))
    ax.set_title(f"Risk vs return, daily data {summary['period']}", loc="left")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "efficient_frontier.png")

    # Chart 2: correlation heatmap
    fig, ax = plt.subplots(figsize=(5.5, 4.5), dpi=150)
    im = ax.imshow(corr.values, cmap="copper_r", vmin=-0.2, vmax=1)
    ax.set_xticks(range(len(names)), names)
    ax.set_yticks(range(len(names)), names)
    for i in range(len(names)):
        for j in range(len(names)):
            ax.text(j, i, f"{corr.values[i, j]:.2f}", ha="center", va="center",
                    color="white" if corr.values[i, j] > 0.4 else INK, fontsize=9)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title("Correlation of daily returns", loc="left")
    fig.tight_layout()
    fig.savefig(OUT / "correlation.png")

    # Console summary
    print(f"Period {summary['period']}, {len(rets)} trading days, risk-free {rf:.2%}")
    print(pd.DataFrame(assets).set_index("ticker")[["ret", "vol", "cagr", "sharpe", "max_drawdown"]].round(3))
    for label, p in portfolios.items():
        w = ", ".join(f"{t} {x:.0%}" for t, x in p["weights"].items() if x > 0.005)
        print(f"{label:16s} ret {p['ret']:.2%}  vol {p['vol']:.2%}  Sharpe {p['sharpe']:.2f}  "
              f"maxDD {p['max_drawdown']:.1%}  [{w}]")
    print("Out of sample, 2020–2024:")
    for label, p in out_of_sample.items():
        w = ", ".join(f"{t} {x:.0%}" for t, x in p["weights"].items() if x > 0.005)
        print(f"  {label:30s} ret {p['ret']:.2%}  vol {p['vol']:.2%}  Sharpe {p['sharpe']:.2f}  "
              f"maxDD {p['max_drawdown']:.1%}  [{w}]")


if __name__ == "__main__":
    main()
