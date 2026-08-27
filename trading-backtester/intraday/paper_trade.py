"""
Live paper-trading loop: VWAP mean reversion on SPY, 1-minute bars.
Runs against Alpaca PAPER account only - no real money.
"""

import os
import time
from datetime import datetime

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus

load_dotenv()   # reads .env from project root

TICKER = "SPY"
QTY = 1                  # shares per position
ENTRY_BPS = 10           # enter when price <= VWAP * (1 - 10bp)
EXIT_BPS = 0             # exit when price back >= VWAP
LOOP_SECONDS = 60        # check every minute

trading = TradingClient(os.getenv("APCA_API_KEY_ID"),
                        os.getenv("APCA_API_SECRET_KEY"), paper=True)


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def session_vwap():
    """Fetch today's 1m bars from yfinance and compute session VWAP."""
    df = yf.download(TICKER, period="1d", interval="1m",
                     progress=False, auto_adjust=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    if df.empty or df["Volume"].sum() == 0:
        return None
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    return (tp * df["Volume"]).sum() / df["Volume"].sum()


def current_position():
    try:
        pos = trading.get_open_position(TICKER)
        return int(pos.qty)
    except Exception:
        return 0


def cancel_stale_orders():
    orders = trading.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN))
    for o in orders:
        trading.cancel_order_by_id(o.id)


def main():
    log(f"Paper trader started. Ticker={TICKER} qty={QTY} "
        f"entry={ENTRY_BPS}bp below VWAP")
    while True:
        try:
            clock = trading.get_clock()
            if not clock.is_open:
                log(f"Market closed (next open {clock.next_open}). Sleeping...")
                time.sleep(300)
                continue

            vwap = session_vwap()
            if vwap is None:
                log("No bar data yet.")
                time.sleep(LOOP_SECONDS)
                continue

            # Last price from latest completed minute bar
            last = yf.download(TICKER, period="1d", interval="1m",
                               progress=False)["Close"].dropna().iloc[-1]
            dev_bps = (last / vwap - 1) * 10000

            held = current_position()
            if held == 0 and dev_bps <= -ENTRY_BPS:
                px = round(float(last), 2)
                req = LimitOrderRequest(symbol=TICKER, qty=QTY,
                                        side=OrderSide.BUY,
                                        time_in_force=TimeInForce.DAY,
                                        limit_price=px)
                trading.submit_order(req)
                log(f"BUY limit {QTY} {TICKER} @ {px} "
                    f"({dev_bps:.1f}bp below VWAP)")
            elif held > 0 and dev_bps >= -EXIT_BPS:
                px = round(float(last), 2)
                req = LimitOrderRequest(symbol=TICKER, qty=held,
                                        side=OrderSide.SELL,
                                        time_in_force=TimeInForce.DAY,
                                        limit_price=px)
                trading.submit_order(req)
                log(f"SELL limit {held} {TICKER} @ {px} "
                    f"(reverted, {dev_bps:+.1f}bp vs VWAP)")
            else:
                log(f"Hold. price={float(last):.2f} vwap={vwap:.2f} "
                    f"dev={dev_bps:+.1f}bp pos={held}")

            cancel_stale_orders()
        except Exception as e:
            log(f"ERROR: {e}")
        time.sleep(LOOP_SECONDS)


if __name__ == "__main__":
    main()
