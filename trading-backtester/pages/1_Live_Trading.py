"""Live Trading page: monitor & control the Alpaca paper/live trader."""

import os
import time
from datetime import datetime

import pandas as pd
import streamlit as st
import yfinance as yf
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus

from intraday.trade_log import log_trade, read_log

load_dotenv()

st.set_page_config(page_title="Live Trading", page_icon="📈", layout="wide")
st.title("Live Trading — VWAP Mean Reversion (SPY)")

# ---------- Mode selection & safety gate ----------
LIVE_UNLOCKED = os.getenv("ALLOW_LIVE", "false").lower() == "true"

mode = st.sidebar.radio("Trading mode", ["PAPER", "LIVE"],
                        disabled=not LIVE_UNLOCKED,
                        help="LIVE requires ALLOW_LIVE=true in .env")

if mode == "LIVE":
    confirm = st.text_input("Type LIVE to confirm real-money mode:")
    if confirm != "LIVE":
        st.warning("Live mode locked until you type LIVE above.")
        st.stop()

key = os.getenv("APCA_API_KEY_ID")
sec = os.getenv("APCA_API_SECRET_KEY")
if not key or not sec:
    st.error("API keys missing from .env")
    st.stop()

trading = TradingClient(key, sec, paper=(mode == "PAPER"))

# ---------- Session state ----------
if "trader_on" not in st.session_state:
    st.session_state.trader_on = False
    st.session_state.last_log = []

ENTRY_BPS = st.sidebar.number_input("Entry threshold (bp below VWAP)", 1, 100, 10)
QTY = st.sidebar.number_input("Order size (shares)", 1, 100, 1)
POLL_SECONDS = st.sidebar.slider("Polling cadence (seconds)", 10, 300, 60, 5)



def log(msg):
    st.session_state.last_log.insert(0, f"[{datetime.now():%H:%M:%S}] {msg}")
    st.session_state.last_log = st.session_state.last_log[:100]


def session_vwap():
    df = yf.download("SPY", period="1d", interval="1m",
                     progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty or df["Volume"].sum() == 0:
        return None, None
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    vwap = (tp * df["Volume"]).sum() / df["Volume"].sum()
    return vwap, float(df["Close"].dropna().iloc[-1])


def run_one_cycle():
    """One trading decision — called by the auto-trader or the button."""
    clock = trading.get_clock()
    if not clock.is_open:
        log(f"Market closed. Next open {clock.next_open}")
        log_trade("MARKET_CLOSED", None, None, None, 0, mode=mode)
        return
    vwap, last = session_vwap()
    if vwap is None:
        log("No data yet.")
        return
    dev = (last / vwap - 1) * 10000
    try:
        pos = int(trading.get_open_position("SPY").qty)
    except Exception:
        pos = 0

    if pos == 0 and dev <= -ENTRY_BPS:
        trading.submit_order(LimitOrderRequest(
            symbol="SPY", qty=QTY, side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY, limit_price=round(last, 2)))
        log(f"BUY limit {QTY} @ {last:.2f} ({dev:.1f}bp below VWAP)")
        log_trade("BUY", last, vwap, dev, 0, mode=mode)
    elif pos > 0 and dev >= 0:
        trading.submit_order(LimitOrderRequest(
            symbol="SPY", qty=pos, side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY, limit_price=round(last, 2)))
        log(f"SELL limit {pos} @ {last:.2f} (reverted to VWAP)")
        log_trade("SELL", last, vwap, dev, pos, mode=mode)
    else:
        log(f"Hold. price={last:.2f} vwap={vwap:.2f} "
            f"dev={dev:+.1f}bp pos={pos}")
        log_trade("HOLD", last, vwap, dev, pos, mode=mode)


# ---------- Controls ----------
c1, c2 = st.columns(2)
if c1.button("Start auto-trader", type="primary"):
    st.session_state.trader_on = True
if c2.button("Stop auto-trader"):
    st.session_state.trader_on = False

if st.button("Run one check now"):
    run_one_cycle()

st.caption(f"Auto-trader: {'RUNNING' if st.session_state.trader_on else 'STOPPED'} — "
           f"mode: {mode}")

# ---------- Account & orders ----------
acct = trading.get_account()
a1, a2, a3 = st.columns(3)
a1.metric("Equity", f"${float(acct.equity):,.2f}")
a2.metric("Buying power", f"${float(acct.buying_power):,.2f}")
try:
    pos = trading.get_open_position("SPY")
    a3.metric("SPY position", f"{pos.qty} @ ${float(pos.avg_entry_price):.2f}")
except Exception:
    a3.metric("SPY position", "flat")

orders = trading.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, limit=10))
if orders:
    st.subheader("Recent orders")
    st.dataframe([{"time": str(o.created_at), "side": o.side.value,
                   "qty": o.qty, "type": o.order_type.value,
                   "status": o.status.value, "price": o.limit_price}
                  for o in orders], use_container_width=True)

st.subheader("Trader log")
st.code("\n".join(st.session_state.last_log) or "No activity yet.")

# ---------- CSV trade log ----------
st.subheader("Trade log (CSV)")
df_log = read_log()
if not df_log.empty:
    st.dataframe(df_log.tail(50), use_container_width=True)
    st.download_button("Download full CSV",
                       data=df_log.to_csv(index=False),
                       file_name="live_trades.csv",
                       mime="text/csv")
    trades = df_log[df_log["action"].isin(["BUY", "SELL"])]
    st.caption(f"{len(trades)} orders logged | "
               f"{(df_log['action'] == 'HOLD').sum()} hold checks")
else:
    st.caption("No CSV log yet — run a check or start the auto-trader.")

# ---------- Auto-refresh loop ----------
if st.session_state.trader_on:
    time.sleep(POLL_SECONDS)
    run_one_cycle()
    st.rerun()
