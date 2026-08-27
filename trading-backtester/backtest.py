"""Core backtesting logic for the trading strategy backtester."""

import yfinance as yf
import pandas as pd
import numpy as np

TRADING_DAYS = 252
COMMISSION = 0.001   # 0.1% per trade side
SLIPPAGE = 0.0005    # 0.05% per trade side


def fetch_data(tickers, start, end=None):
    """Download adjusted close prices for a list of tickers."""
    data = yf.download(tickers, start=start, end=end,
                       auto_adjust=True, progress=False)
    return data["Close"]


def compute_rsi(prices, period=14):
    """Compute RSI using Wilder's smoothing (industry standard)."""
    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.where(avg_loss != 0, 100.0)


def ma_crossover_signals(prices, fast_window=50, slow_window=200):
    """Position = 1 when fast SMA is above slow SMA, else 0."""
    fast_ma = prices.rolling(fast_window).mean()
    slow_ma = prices.rolling(slow_window).mean()
    positions = (fast_ma > slow_ma).astype(int)
    positions[slow_ma.isna()] = 0
    return positions, fast_ma, slow_ma


def mean_reversion_signals(prices, rsi, oversold=30, exit_level=55):
    """Buy when RSI crosses back above oversold, exit when RSI reaches exit_level."""
    positions = pd.DataFrame(0.0, index=prices.index, columns=prices.columns)
    for ticker in prices.columns:
        pos = 0
        rsi_series = rsi[ticker]
        for i in range(len(prices)):
            r = rsi_series.iloc[i]
            if pd.notna(r):
                if pos == 0 and r > oversold and rsi_series.iloc[i - 1] <= oversold:
                    pos = 1
                elif pos == 1 and r >= exit_level:
                    pos = 0
            positions.iloc[i, positions.columns.get_loc(ticker)] = pos
    return positions


def backtest(prices, positions, commission=COMMISSION, slippage=SLIPPAGE):
    """
    Backtest positions against prices, net of costs.
    Positions are lagged 1 day to avoid lookahead bias.
    """
    positions_lagged = positions.shift(1).fillna(0)
    daily_returns = prices.pct_change().fillna(0)
    gross_returns = positions_lagged * daily_returns
    trades = positions_lagged.diff().abs().fillna(0)
    costs = trades * (commission + slippage)
    net_returns = gross_returns - costs
    return net_returns


def total_return(returns):
    return (1 + returns).prod() - 1


def annualized_return(returns):
    total = (1 + returns).prod() - 1
    years = len(returns) / TRADING_DAYS
    return (1 + total) ** (1 / years) - 1


def sharpe_ratio(returns, rf=0.0):
    excess = returns.mean() * TRADING_DAYS - rf
    return excess / (returns.std() * np.sqrt(TRADING_DAYS))


def max_drawdown(returns):
    equity = (1 + returns).cumprod()
    return (equity / equity.cummax() - 1).min()


def performance_summary(returns, name):
    return {
        "Strategy": name,
        "Total Return %": round(total_return(returns) * 100, 1),
        "Ann. Return %": round(annualized_return(returns) * 100, 1),
        "Sharpe": round(sharpe_ratio(returns), 2),
        "Max DD %": round(max_drawdown(returns) * 100, 1),
    }
