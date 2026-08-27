"""Intraday backtest engine: lookahead-free, cost-aware."""

COSTS_PER_SIDE = 0.0005   # 5 bps per trade side (commission + slippage)


def vwap_reversion_signals(df, entry_bps=10, exit_bps=0):
    """
    Long when price is entry_bps BELOW session VWAP,
    exit when price reverts to within exit_bps of VWAP.
    Position can only be entered/exit on bar CLOSE, applied to NEXT bar.
    """
    dev = (df["Close"] / df["vwap"] - 1) * 10000   # deviation in bps
    pos = 0
    positions = []
    for d in dev:
        if pos == 0 and d <= -entry_bps:
            pos = 1
        elif pos == 1 and d >= -exit_bps:
            pos = 0
        positions.append(pos)
    import pandas as pd
    return pd.Series(positions, index=df.index)


def backtest_intraday(df, positions, cost_per_side=COSTS_PER_SIDE):
    """Returns net per-bar returns. Signal lagged 1 bar = no lookahead."""
    pos_lag = positions.shift(1).fillna(0)
    gross = pos_lag * df["ret"]
    trades = pos_lag.diff().abs().fillna(0)
    costs = trades * cost_per_side
    return (gross - costs).fillna(0)


def intraday_metrics(net_returns, bars_per_year=252 * 390):
    import numpy as np
    total = (1 + net_returns).prod() - 1
    sharpe = net_returns.mean() / net_returns.std() * np.sqrt(bars_per_year)
    equity = (1 + net_returns).cumprod()
    max_dd = (equity / equity.cummax() - 1).min()
    n_trades = int((net_returns != 0).sum())
    return {"Total return %": round(total * 100, 3),
            "Sharpe (bar-annualized)": round(sharpe, 2),
            "Max DD %": round(max_dd * 100, 2),
            "Bars in market": n_trades}
