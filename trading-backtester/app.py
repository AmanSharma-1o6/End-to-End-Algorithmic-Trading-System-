"""Streamlit dashboard: Algorithmic Trading Strategy Backtester."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

import backtest as bt

st.set_page_config(page_title="Strategy Backtester", layout="wide")
st.title("Algorithmic Trading Strategy Backtester")
st.caption("MA Crossover vs RSI Mean Reversion vs Buy-and-Hold, net of costs")

# ---------- Sidebar controls ----------
st.sidebar.header("Settings")
tickers = st.sidebar.multiselect(
    "Tickers",
    ["SPY", "AAPL", "MSFT", "NVDA", "JPM"],
    default=["SPY", "AAPL", "MSFT", "NVDA", "JPM"],
)
start_date = st.sidebar.date_input("Start date", pd.Timestamp("2019-01-01"))
strategy = st.sidebar.radio("Strategy", ["MA Crossover", "RSI Mean Reversion", "Both"])

if len(tickers) < 1:
    st.warning("Select at least one ticker.")
    st.stop()


# ---------- Load data (cached) ----------
@st.cache_data(ttl=3600)
def load_prices(tickers, start):
    return bt.fetch_data(tickers, start)


prices = load_prices(tickers, start_date)
prices = prices.dropna()

# ---------- Run strategies ----------
ma_pos_all, fast_ma, slow_ma = bt.ma_crossover_signals(prices)
rsi = bt.compute_rsi(prices)
mr_pos_all = bt.mean_reversion_signals(prices, rsi)

ma_port = bt.backtest(prices, ma_pos_all).mean(axis=1)
mr_port = bt.backtest(prices, mr_pos_all).mean(axis=1)
bh_port = prices.pct_change().fillna(0).mean(axis=1)

# ---------- Performance table ----------
rows = [bt.performance_summary(bh_port, "Buy & Hold (benchmark)")]
if strategy in ("MA Crossover", "Both"):
    rows.append(bt.performance_summary(ma_port, "MA Crossover (net)"))
if strategy in ("RSI Mean Reversion", "Both"):
    rows.append(bt.performance_summary(mr_port, "RSI Mean Reversion (net)"))

st.subheader("Performance Comparison (Equal-Weight Portfolio, Net of Costs)")
st.dataframe(pd.DataFrame(rows).set_index("Strategy"), use_container_width=True)

# ---------- Equity curves ----------
st.subheader("Equity Curves")
fig = go.Figure()
fig.add_trace(go.Scatter(x=bh_port.index, y=(1 + bh_port).cumprod(),
                         name="Buy & Hold", line=dict(color="royalblue")))
if strategy in ("MA Crossover", "Both"):
    fig.add_trace(go.Scatter(x=ma_port.index, y=(1 + ma_port).cumprod(),
                             name="MA Crossover", line=dict(color="orange")))
if strategy in ("RSI Mean Reversion", "Both"):
    fig.add_trace(go.Scatter(x=mr_port.index, y=(1 + mr_port).cumprod(),
                             name="RSI Mean Reversion", line=dict(color="green")))
fig.update_layout(yaxis_title="Growth of $1", height=450,
                  legend=dict(orientation="h"))
st.plotly_chart(fig, use_container_width=True)

# ---------- Drawdown ----------
st.subheader("Drawdown")
fig_dd = go.Figure()
curve_list = [("Buy & Hold", bh_port, "royalblue")]
if strategy in ("MA Crossover", "Both"):
    curve_list.append(("MA Crossover", ma_port, "orange"))
if strategy in ("RSI Mean Reversion", "Both"):
    curve_list.append(("RSI Mean Reversion", mr_port, "green"))

for name, rets, color in curve_list:
    equity = (1 + rets).cumprod()
    dd = (equity / equity.cummax() - 1) * 100
    fig_dd.add_trace(go.Scatter(x=dd.index, y=dd, name=name,
                                line=dict(color=color)))
fig_dd.update_layout(yaxis_title="Drawdown (%)", height=350)
st.plotly_chart(fig_dd, use_container_width=True)

# ---------- Trade signals for selected ticker ----------
st.subheader("Trade Signals")
sig_ticker = st.selectbox("Ticker for signals", tickers)


def add_signals(fig, price_series, positions_series):
    """Add buy/sell markers for a position series to a figure."""
    changes = positions_series.diff()
    buys = changes[changes == 1].index
    sells = changes[changes == -1].index
    fig.add_trace(go.Scatter(x=buys, y=price_series.loc[buys], mode="markers",
                             marker=dict(symbol="triangle-up", size=12, color="green"),
                             name="Buy"))
    fig.add_trace(go.Scatter(x=sells, y=price_series.loc[sells], mode="markers",
                             marker=dict(symbol="triangle-down", size=12, color="red"),
                             name="Sell"))


if strategy in ("MA Crossover", "Both"):
    fig_sig = go.Figure()
    fig_sig.add_trace(go.Scatter(x=prices.index, y=prices[sig_ticker],
                                 name="Price", line=dict(color="black", width=1)))
    fig_sig.add_trace(go.Scatter(x=fast_ma.index, y=fast_ma[sig_ticker],
                                 name="SMA 50", line=dict(color="blue", width=1)))
    fig_sig.add_trace(go.Scatter(x=slow_ma.index, y=slow_ma[sig_ticker],
                                 name="SMA 200", line=dict(color="orange", width=1)))
    add_signals(fig_sig, prices[sig_ticker], ma_pos_all[sig_ticker])
    fig_sig.update_layout(title=f"MA Crossover - {sig_ticker}", height=400)
    st.plotly_chart(fig_sig, use_container_width=True)

if strategy in ("RSI Mean Reversion", "Both"):
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=prices.index, y=prices[sig_ticker],
                                 name="Price", line=dict(color="black", width=1)))
    add_signals(fig_rsi, prices[sig_ticker], mr_pos_all[sig_ticker])
    fig_rsi.update_layout(title=f"RSI Mean Reversion - {sig_ticker}", height=400)
    st.plotly_chart(fig_rsi, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("Costs modeled: 0.10% commission + 0.05% slippage per trade side. "
                   "Signals lagged 1 day to avoid lookahead bias.")
