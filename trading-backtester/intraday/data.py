"""Intraday data fetching with local caching."""

import os
import pandas as pd
import yfinance as yf

CACHE_DIR = "intraday/cache"
os.makedirs(CACHE_DIR, exist_ok=True)


def fetch_minutes(ticker, interval="1m", period="7d", use_cache=True):
    """
    Download intraday bars from yfinance with disk caching.
    yfinance limits: 1m -> last 7 days max per request,
                     5m/15m -> up to 60 days.
    """
    fname = f"{CACHE_DIR}/{ticker}_{interval}_{period}.csv"

    if use_cache and os.path.exists(fname):
        df = pd.read_csv(fname, index_col=0, parse_dates=True)
        return df

    df = yf.download(ticker, interval=interval, period=period,
                     auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if use_cache:
        df.to_csv(fname)
    return df


def add_session_features(df):
    """Add VWAP (session-resetting) and returns."""
    df = df.copy()
    df["date"] = df.index.date
    # Typical price * volume, cumulative within each session
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    df["cum_pv"] = (tp * df["Volume"]).groupby(df["date"]).cumsum()
    df["cum_vol"] = df["Volume"].groupby(df["date"]).cumsum()
    df["vwap"] = df["cum_pv"] / df["cum_vol"]
    df["ret"] = df["Close"].pct_change().fillna(0)
    return df.drop(columns=["date", "cum_pv", "cum_vol"])
